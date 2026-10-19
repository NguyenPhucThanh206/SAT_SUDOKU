import csv
import time
import math
from pysat.card import EncType
from pysat.formula import CNF

from sudoku_solver import SudokuSATSolver
from commander_sudoku import CommanderSudokuSolver


def add_product_amo(cnf, lits, max_var_id):
    n = len(lits)
    if n <= 1:
        return max_var_id
    if n <= 3:
        for i in range(n):
            for j in range(i + 1, n):
                cnf.append([-lits[i], -lits[j]])
        return max_var_id

    p = math.ceil(math.sqrt(n))
    q = math.ceil(n / p)

    u_vars = [max_var_id + 1 + i for i in range(p)]
    v_vars = [max_var_id + 1 + p + j for j in range(q)]
    new_max_id = max_var_id + p + q

    for idx, lit in enumerate(lits):
        r = idx // q
        c = idx % q
        cnf.append([-lit, u_vars[r]])
        cnf.append([-lit, v_vars[c]])

    for i in range(p):
        for j in range(i + 1, p):
            cnf.append([-u_vars[i], -u_vars[j]])

    for i in range(q):
        for j in range(i + 1, q):
            cnf.append([-v_vars[i], -v_vars[j]])

    return new_max_id


class ProductSudokuSolver(SudokuSATSolver):
    def build_cnf(self):
        self.cnf = CNF()
        self.max_var_id = self.N ** 3
        N, B = self.N, self.subgrid_size

        for r in range(1, N + 1):
            for c in range(1, N + 1):
                cell_vars = [self.var_id(r, c, v) for v in range(1, N + 1)]
                self.cnf.append(cell_vars)
                self.max_var_id = add_product_amo(self.cnf, cell_vars, self.max_var_id)

        for r in range(1, N + 1):
            for v in range(1, N + 1):
                row_vars = [self.var_id(r, c, v) for c in range(1, N + 1)]
                self.cnf.append(row_vars)
                self.max_var_id = add_product_amo(self.cnf, row_vars, self.max_var_id)

        for c in range(1, N + 1):
            for v in range(1, N + 1):
                col_vars = [self.var_id(r, c, v) for r in range(1, N + 1)]
                self.cnf.append(col_vars)
                self.max_var_id = add_product_amo(self.cnf, col_vars, self.max_var_id)

        for br in range(0, N, B):
            for bc in range(0, N, B):
                for v in range(1, N + 1):
                    box_vars = [
                        self.var_id(r, c, v)
                        for r in range(br + 1, br + B + 1)
                        for c in range(bc + 1, bc + B + 1)
                    ]
                    self.cnf.append(box_vars)
                    self.max_var_id = add_product_amo(self.cnf, box_vars, self.max_var_id)

        for r, c, v in self.givens:
            self.cnf.append([self.var_id(r, c, v)])


DATASETS = {
    "Sudoku 9x9": (
        9,
        [
            (1, 1, 8), (2, 3, 3), (2, 4, 6), (3, 2, 7), (3, 5, 9), (3, 7, 2),
            (4, 2, 5), (4, 6, 7), (5, 5, 4), (6, 4, 1), (6, 8, 3),
            (7, 3, 1), (7, 8, 6), (7, 9, 8), (8, 3, 8), (8, 4, 5), (8, 8, 1),
            (9, 2, 9), (9, 7, 4)
        ]
    ),
    "Sudoku 16x16": (
        16,
        [
            (1, 1, 16), (2, 5, 12), (3, 9, 8),   (4, 13, 4),
            (5, 2, 3),  (6, 6, 7),  (7, 10, 11), (8, 14, 15),
            (9, 3, 2),  (10, 7, 6), (11, 11, 10), (12, 15, 14),
            (13, 4, 1), (14, 8, 5), (15, 12, 9), (16, 16, 13)
        ]
    ),
    "Sudoku 25x25": (
        25,
        [(i, ((i * 2) % 25) + 1, i) for i in range(1, 26)]
    ),
    "Sudoku 36x36": (
        36,
        [(i, ((i * 5) % 36) + 1, i) for i in range(1, 37)]
    ),
    "Sudoku 49x49": (
        49,
        [(i, ((i * 3) % 49) + 1, i) for i in range(1, 50)]
    ),
    "Sudoku 64x64": (
        64,
        [(i, ((i * 5) % 64) + 1, i) for i in range(1, 65)]
    ),
    "Sudoku 81x81": (
        81,
        [(i, ((i * 7) % 81) + 1, i) for i in range(1, 82)]
    )
}

ENCODINGS = {
    "Pairwise": ("pysat", EncType.pairwise),
    "Bitwise": ("pysat", EncType.bitwise),
    "SeqCounter": ("pysat", EncType.seqcounter),
    "Commander": ("commander", None),
    "Product": ("product", None)
}


def run_benchmark():
    results = []
    print("=== CHẠY BENCHMARK SAT SUDOKU (TỪ 9x9 ĐẾN 81x81) ===\n")

    for size_name, (N, givens) in DATASETS.items():
        print(f"================ {size_name} ================")
        for enc_name, (enc_kind, enc_val) in ENCODINGS.items():
            print(f"--> [{size_name}] Đang giải {enc_name} ...", end=" ", flush=True)

            try:
                if enc_kind == "pysat":
                    solver = SudokuSATSolver(N=N, givens=givens, encoding=enc_val)
                elif enc_kind == "commander":
                    solver = CommanderSudokuSolver(N=N, givens=givens)
                elif enc_kind == "product":
                    solver = ProductSudokuSolver(N=N, givens=givens)

                sol, solve_time, num_vars, num_clauses = solver.solve(solver_name='cadical153')
                status = "Success" if sol else "UNSAT"

                print(f"Xong! ({solve_time:.4f}s | Biến: {num_vars:,} | Mệnh đề: {num_clauses:,} | {status})")

                results.append({
                    "Dataset": size_name,
                    "Encoding": enc_name,
                    "Variables": num_vars,
                    "Clauses": num_clauses,
                    "Time_Seconds": round(solve_time, 6),
                    "Status": status
                })

            except MemoryError:
                print("LỖI TRÀN RAM (MemoryError)!")
                results.append({
                    "Dataset": size_name,
                    "Encoding": enc_name,
                    "Variables": "N/A",
                    "Clauses": "N/A",
                    "Time_Seconds": "MemoryError",
                    "Status": "MemoryError"
                })
            except Exception as e:
                print(f"LỖI KHÁC ({e})")
                results.append({
                    "Dataset": size_name,
                    "Encoding": enc_name,
                    "Variables": "N/A",
                    "Clauses": "N/A",
                    "Time_Seconds": "Error",
                    "Status": str(e)
                })

        print()

    output_csv = "benchmark_sizes_results.csv"
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Dataset", "Encoding", "Variables", "Clauses", "Time_Seconds", "Status"])
        writer.writeheader()
        writer.writerows(results)

    print(f"[HOÀN THÀNH TẤT CẢ] Đã xuất toàn bộ kết quả ra file: {output_csv}\n")


if __name__ == "__main__":
    run_benchmark()