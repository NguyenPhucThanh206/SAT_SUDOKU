import time
import csv
import math

try:
    from ortools.sat.python import cp_model
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False

try:
    import gurobipy as gp
    from gurobipy import GRB
    HAS_GUROBI = True
except ImportError:
    HAS_GUROBI = False

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

def solve_sudoku_cpsat(n, timeout_sec=100):
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

def solve_sudoku_gurobi(n, timeout_sec=100):
    if not HAS_GUROBI:
        return "N/A", 0.0
    
    b = int(math.isqrt(n))
    start = time.time()
    
    try:
        env = gp.Env(empty=True)
        env.setParam('OutputFlag', 0)
        env.start()
        
        model = gp.Model("Sudoku_Gurobi", env=env)
        model.Params.TimeLimit = timeout_sec

        x = model.addVars(n, n, n, vtype=GRB.BINARY, name="x")
   
        for i in range(n):
            for j in range(n):
                model.addConstr(gp.quicksum(x[i, j, v] for v in range(n)) == 1)
                
        for i in range(n):
            for v in range(n):
                model.addConstr(gp.quicksum(x[i, j, v] for j in range(n)) == 1)
                
        for j in range(n):
            for v in range(n):
                model.addConstr(gp.quicksum(x[i, j, v] for i in range(n)) == 1)
                
        for r in range(0, n, b):
            for c in range(0, n, b):
                for v in range(n):
                    model.addConstr(gp.quicksum(x[r + dr, c + dc, v] for dr in range(b) for dc in range(b)) == 1)
                    
        model.optimize()
        runtime = time.time() - start
        
        if model.Status in (GRB.OPTIMAL, GRB.SUBOPTIMAL) or model.SolCount > 0:
            return "Success", runtime
        elif model.Status == GRB.TIME_LIMIT:
            return "Timeout", runtime
        else:
            return "UNSAT", runtime
            
    except Exception as e:
        return f"Error ({e})", time.time() - start

def solve_sudoku_cplex_cp(n, timeout_sec=100):
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

        sol = mdl.solve(TimeLimit=timeout_sec, LogVerbosity="Quiet")
        runtime = time.time() - start
        
        if sol and sol.is_solution():
            return "Success", runtime
        else:
            return "Timeout/UNSAT", runtime
            
    except Exception as e:
        return f"Error ({e})", time.time() - start

def solve_sudoku_cplex_mp(n, timeout_sec=100):
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
    sizes = [9, 16, 25, 36, 49, 64, 81, 100] 
    timeout = 100
    
    output_file = "benchmark_sudoku_comparison_results.csv"
    headers = [
        "Size", 
        "OR-Tools_CP-SAT (s)", "CP-SAT Status",
        "CPLEX_CP (s)", "CPLEX CP Status",
        "Gurobi_MIP (s)", "Gurobi Status",
        "CPLEX_MIP (s)", "CPLEX MIP Status"
    ]
    
    print(f"{'Size':<10} | {'CP-SAT (s)':<12} | {'CPLEX CP (s)':<12} | {'Gurobi MIP(s)':<12} | {'CPLEX MIP(s)':<12}")
    print("-" * 75)
    
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for n in sizes:
            cp_stat, cp_time = solve_sudoku_cpsat(n, timeout)
            cplex_cp_stat, cplex_cp_time = solve_sudoku_cplex_cp(n, timeout)
            gb_stat, gb_time = solve_sudoku_gurobi(n, timeout)
            cplex_mp_stat, cplex_mp_time = solve_sudoku_cplex_mp(n, timeout)
            
            print(f"{f'Sudoku {n}x{n}':<10} | {cp_time:<12.4f} | {cplex_cp_time:<12.4f} | {gb_time:<12.4f} | {cplex_mp_time:<12.4f}")
            
            writer.writerow([
                f"Sudoku {n}x{n}",
                round(cp_time, 6), cp_stat,
                round(cplex_cp_time, 6), cplex_cp_stat,
                round(gb_time, 6), gb_stat,
                round(cplex_mp_time, 6), cplex_mp_stat
            ])

if __name__ == "__main__":
    run_sudoku_benchmark()