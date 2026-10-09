import math
import time
from pysat.solvers import Solver
from pysat.formula import CNF

class CommanderSudokuSolver:
    def __init__(self, N, givens, group_size=3):
        self.N = N
        self.subgrid_size = int(math.isqrt(N))
        self.givens = givens
        self.group_size = group_size
        self.cnf = CNF()
        self.max_var_id = N ** 3

    def var_id(self, r, c, v):
        return (r - 1) * (self.N ** 2) + (c - 1) * self.N + v

    def decode_var_id(self, var_id):
        idx = var_id - 1
        v = (idx % self.N) + 1
        c = ((idx // self.N) % self.N) + 1
        r = (idx // (self.N ** 2)) + 1
        return r, c, v

    def _add_commander_amo(self, lits):
        n = len(lits)
        if n <= 1:
            return

        if n <= self.group_size:
            for i in range(n):
                for j in range(i + 1, n):
                    self.cnf.append([-lits[i], -lits[j]])
            return

        groups = [lits[i:i + self.group_size] for i in range(0, n, self.group_size)]
        commander_vars = []

        for group in groups:
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    self.cnf.append([-group[i], -group[j]])

            if len(group) == 1:
                commander_vars.append(group[0])
                continue

            self.max_var_id += 1
            c_i = self.max_var_id
            commander_vars.append(c_i)

            self.cnf.append([-c_i] + group)
            for x in group:
                self.cnf.append([-x, c_i])

        self._add_commander_amo(commander_vars)

    def build_cnf(self):
        self.cnf = CNF()
        self.max_var_id = self.N ** 3
        N, B = self.N, self.subgrid_size

        for r in range(1, N + 1):
            for c in range(1, N + 1):
                cell_vars = [self.var_id(r, c, v) for v in range(1, N + 1)]
                self.cnf.append(cell_vars)
                self._add_commander_amo(cell_vars)

        for r in range(1, N + 1):
            for v in range(1, N + 1):
                row_vars = [self.var_id(r, c, v) for c in range(1, N + 1)]
                self.cnf.append(row_vars)
                self._add_commander_amo(row_vars)

        for c in range(1, N + 1):
            for v in range(1, N + 1):
                col_vars = [self.var_id(r, c, v) for c in range(1, N + 1)]
                self.cnf.append(col_vars)
                self._add_commander_amo(col_vars)

        for br in range(0, N, B):
            for bc in range(0, N, B):
                for v in range(1, N + 1):
                    box_vars = [
                        self.var_id(r, c, v)
                        for r in range(br + 1, br + B + 1)
                        for c in range(bc + 1, bc + B + 1)
                    ]
                    self.cnf.append(box_vars)
                    self._add_commander_amo(box_vars)

        for r, c, v in self.givens:
            self.cnf.append([self.var_id(r, c, v)])

    def solve(self, solver_name='cadical153'):
        start_time = time.time()
        self.build_cnf()

        with Solver(name=solver_name, bootstrap_with=self.cnf) as solver:
            is_sat = solver.solve()
            solve_time = time.time() - start_time
            num_vars = self.max_var_id
            num_clauses = len(self.cnf.clauses)

            if is_sat:
                model = solver.get_model()
                solution = [[0] * self.N for _ in range(self.N)]
                for lit in model:
                    if 0 < lit <= (self.N ** 3):
                        r, c, v = self.decode_var_id(lit)
                        solution[r - 1][c - 1] = v
                return solution, solve_time, num_vars, num_clauses
            else:
                return None, solve_time, num_vars, num_clauses