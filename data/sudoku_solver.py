import math
import time
from pysat.solvers import Solver
from pysat.formula import CNF
from pysat.card import CardEnc, EncType

class SudokuSATSolver:
    def __init__(self, N, givens, encoding=EncType.pairwise):
        self.N = N
        self.subgrid_size = int(math.isqrt(N))
        self.givens = givens
        self.encoding = encoding 
        self.cnf = CNF()

    def var_id(self, r, c, v):
        return (r - 1) * (self.N ** 2) + (c - 1) * self.N + v

    def decode_var_id(self, var_id):
        idx = var_id - 1
        v = (idx % self.N) + 1
        c = ((idx // self.N) % self.N) + 1
        r = (idx // (self.N ** 2)) + 1
        return r, c, v

    def build_cnf(self): 
        self.cnf = CNF()
        N = self.N
        B = self.subgrid_size 
        enc = self.encoding

        for r in range(1, N + 1):
            for c in range(1, N + 1):
                cell_vars = [self.var_id(r, c, v) for v in range(1, N + 1)]
                self.cnf.append(cell_vars)
                self.cnf.extend(CardEnc.atmost(lits=cell_vars, bound=1, encoding=enc))

        for r in range(1, N + 1):
            for v in range(1, N + 1):
                row_vars = [self.var_id(r, c, v) for c in range(1, N + 1)]
                self.cnf.append(row_vars)
                self.cnf.extend(CardEnc.atmost(lits=row_vars, bound=1, encoding=enc))

        for c in range(1, N + 1):
            for v in range(1, N + 1):
                col_vars = [self.var_id(r, c, v) for r in range(1, N + 1)]
                self.cnf.append(col_vars)
                self.cnf.extend(CardEnc.atmost(lits=col_vars, bound=1, encoding=enc)) 

        for br in range(0, N, B):
            for bc in range(0, N, B):
                for v in range(1, N + 1):
                    box_vars = [
                        self.var_id(r, c, v)
                        for r in range(br + 1, br + B + 1)
                        for c in range(bc + 1, bc + B + 1)
                    ]
                    self.cnf.append(box_vars)
                    self.cnf.extend(CardEnc.atmost(lits=box_vars, bound=1, encoding=enc))   

        for r, c, v in self.givens:
            self.cnf.append([self.var_id(r, c, v)])

    def solve(self, solver_name='cadical153'):
        start_time = time.time()
        self.build_cnf()

        with Solver(name=solver_name, bootstrap_with=self.cnf) as solver:
            is_sat = solver.solve()
            solve_time = time.time() - start_time

            num_vars = self.cnf.nv
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