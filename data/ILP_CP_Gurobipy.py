import time
import csv
import math
from benchmark import DATASETS

try:
    from ortools.sat.python import cp_model
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False

try:
    from docplex.cp.model import CpoModel
    HAS_CPLEX_CP = True
except ImportError:
    HAS_CPLEX_CP = False

try:
    from docplex.mp.model import Model as CplexModel
    HAS_CPLEX_MP = True
except ImportError:
    HAS_CPLEX_MP = False


def solve_sudoku_cpsat(n, givens=None, timeout_sec=3600):
    if not HAS_ORTOOLS:
        return "N/A", 0.0

    b = int(math.isqrt(n))
    if b * b != n:
        raise ValueError(f"N={n} không phải là số chính phương!")

    start = time.time()
    model = cp_model.CpModel()

    grid = [[model.NewIntVar(1, n, f'x_{i}_{j}') for j in range(n)] for i in range(n)]

    for i in range(n):
        model.AddAllDifferent(grid[i])

    for j in range(n):
        model.AddAllDifferent([grid[i][j] for i in range(n)])

    for r in range(0, n, b):
        for c in range(0, n, b):
            block = [grid[r + dr][c + dc] for dr in range(b) for dc in range(b)]
            model.AddAllDifferent(block)

    if givens:
        for r, c, v in givens:
            model.Add(grid[r - 1][c - 1] == v)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(timeout_sec)
    solver.parameters.num_search_workers = 4

    status = solver.Solve(model)
    runtime = time.time() - start

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return "Success", runtime
    elif status == cp_model.INFEASIBLE:
        return "UNSAT", runtime
    else:
        return "Timeout", runtime


def solve_sudoku_cplex_cp(n, givens=None, timeout_sec=3600):
    if not HAS_CPLEX_CP:
        return "N/A", 0.0

    b = int(math.isqrt(n))
    start = time.time()

    try:
        mdl = CpoModel(name="Sudoku_CPLEX_CP")

        grid = [[mdl.integer_var(1, n, name=f"x_{i}_{j}") for j in range(n)] for i in range(n)]

        for i in range(n):
            mdl.add(mdl.all_diff(grid[i]))

        for j in range(n):
            mdl.add(mdl.all_diff([grid[i][j] for i in range(n)]))

        for r in range(0, n, b):
            for c in range(0, n, b):
                block = [grid[r + dr][c + dc] for dr in range(b) for dc in range(b)]
                mdl.add(mdl.all_diff(block))

        if givens:
            for r, c, v in givens:
                mdl.add(grid[r - 1][c - 1] == v)

        sol = mdl.solve(TimeLimit=timeout_sec, LogVerbosity="Quiet")
        runtime = time.time() - start

        if sol and sol.is_solution():
            return "Success", runtime
        else:
            return "Timeout/UNSAT", runtime

    except Exception as e:
        return f"Error ({e})", time.time() - start


def solve_sudoku_cplex_mp(n, givens=None, timeout_sec=3600):
    if not HAS_CPLEX_MP:
        return "N/A", 0.0

    b = int(math.isqrt(n))
    start = time.time()

    try:
        mdl = CplexModel(name="Sudoku_CPLEX_MP")
        mdl.time_limit = timeout_sec
        mdl.context.solver.log_output = False

        x = {(i, j, v): mdl.binary_var(name=f"x_{i}_{j}_{v}") for i in range(n) for j in range(n) for v in range(n)}

        for i in range(n):
            for j in range(n):
                mdl.add_constraint(mdl.sum(x[i, j, v] for v in range(n)) == 1)

        for i in range(n):
            for v in range(n):
                mdl.add_constraint(mdl.sum(x[i, j, v] for j in range(n)) == 1)

        for j in range(n):
            for v in range(n):
                mdl.add_constraint(mdl.sum(x[i, j, v] for i in range(n)) == 1)

        for r in range(0, n, b):
            for c in range(0, n, b):
                for v in range(n):
                    mdl.add_constraint(mdl.sum(x[r + dr, c + dc, v] for dr in range(b) for dc in range(b)) == 1)

        if givens:
            for r, c, v in givens:
                mdl.add_constraint(x[r - 1, c - 1, v - 1] == 1)

        sol = mdl.solve()
        runtime = time.time() - start

        if sol:
            return "Success", runtime
        elif mdl.get_solve_status().name.startswith('TIME_LIMIT'):
            return "Timeout", runtime
        else:
            return "UNSAT", runtime

    except Exception as e:
        return f"Error ({e})", time.time() - start


def run_sudoku_benchmark():
    timeout = 3600

    output_file = "benchmark_sudoku_comparison_results.csv"
    headers = [
        "Size",
        "CPLEX_CP (s)", "CPLEX CP Status",
        "OR-Tools_CP-SAT (s)", "CP-SAT Status",
        "CPLEX_MIP (s)", "CPLEX MIP Status"
    ]

    print(f"{'Size':<12} | {'CPLEX CP (s)':<14} | {'CP-SAT (s)':<14} | {'CPLEX MIP (s)':<14}")
    print("-" * 62)

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for size_name, (n, givens) in DATASETS.items():
            cplex_cp_stat, cplex_cp_time = solve_sudoku_cplex_cp(n, givens, timeout)
            cp_stat, cp_time = solve_sudoku_cpsat(n, givens, timeout)
            cplex_mp_stat, cplex_mp_time = solve_sudoku_cplex_mp(n, givens, timeout)

            print(f"{size_name:<12} | {cplex_cp_time:<14.4f} | {cp_time:<14.4f} | {cplex_mp_time:<14.4f}")

            writer.writerow([
                size_name,
                round(cplex_cp_time, 6), cplex_cp_stat,
                round(cp_time, 6), cp_stat,
                round(cplex_mp_time, 6), cplex_mp_stat
            ])


if __name__ == "__main__":
    run_sudoku_benchmark()