import math
import time
from pysat.solvers import Solver
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType


class SudokuSATSolver:
    def __init__(self, N, givens, encoding=EncType.pairwise):
        self.N = N
        self.subgrid_size = int(math.isqrt(N))
        self.givens = givens
        self.encoding = encoding
        self.cnf = CNF()
        self.vpool = IDPool(start_from=(self.N ** 3) + 1)

    def var_id(self, r, c, v):
        return (r - 1) * (self.N ** 2) + (c - 1) * self.N + v

    def decode_var_id(self, var_id):
        idx = var_id - 1
        v = (idx % self.N) + 1
        c = ((idx // self.N) % self.N) + 1
        r = (idx // (self.N ** 2)) + 1
        return r, c, v

    def _add_exactly_one(self, lits):
        self.cnf.append(lits)
        amo_clauses = CardEnc.atmost(
            lits=lits,
            bound=1,
            vpool=self.vpool,
            encoding=self.encoding
        )
        self.cnf.extend(amo_clauses)

    def build_cnf(self):
        self.cnf = CNF()
        self.vpool = IDPool(start_from=(self.N ** 3) + 1)
        N = self.N
        B = self.subgrid_size

        for r in range(1, N + 1):
            for c in range(1, N + 1):
                cell_vars = [self.var_id(r, c, v) for v in range(1, N + 1)]
                self._add_exactly_one(cell_vars)

        for r in range(1, N + 1):
            for v in range(1, N + 1):
                row_vars = [self.var_id(r, c, v) for c in range(1, N + 1)]
                self._add_exactly_one(row_vars)

        for c in range(1, N + 1):
            for v in range(1, N + 1):
                col_vars = [self.var_id(r, c, v) for r in range(1, N + 1)]
                self._add_exactly_one(col_vars)

        for br in range(0, N, B):
            for bc in range(0, N, B):
                for v in range(1, N + 1):
                    box_vars = [
                        self.var_id(r, c, v)
                        for r in range(br + 1, br + B + 1)
                        for c in range(bc + 1, bc + B + 1)
                    ]
                    self._add_exactly_one(box_vars)

        for r, c, v in self.givens:
            self.cnf.append([self.var_id(r, c, v)])

    def solve(self, solver_name='cadical153'):
        start_time = time.time()
        self.build_cnf()

        with Solver(name=solver_name, bootstrap_with=self.cnf) as solver:
            is_sat = solver.solve()
            solve_time = time.time() - start_time

            num_vars = max(self.cnf.nv, self.N ** 3)
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