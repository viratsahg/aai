import sys
import os
import time
import subprocess
import argparse
from itertools import combinations
from dataclasses import dataclass
from typing import List, Dict, Tuple



@dataclass
class Course:
    id: int
    start: int       # s_i : earliest possible start day
    deadline: int    # d_i : course must FINISH by this day
    duration: int    # t_i : number of consecutive days required


@dataclass
class Problem:
    M: int               # number of rooms
    N: int               # number of courses
    courses: List[Course]
    T: int = 0           # global horizon = max deadline

    def __post_init__(self):
        if self.courses:
            self.T = max(c.deadline for c in self.courses)

    def valid_starts(self, course: Course) -> range:
        lo = course.start
        hi = course.deadline - course.duration + 1
        if hi < lo:
            return range(0)   # no valid start — problem is trivially UNSAT
        return range(lo, hi + 1)



def parse_input(filename: str) -> Problem:
    """Parse the assignment input format into a Problem object."""
    M = N = 0
    courses: List[Course] = []

    with open(filename) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('%'):
                continue
            parts = line.split()
            tag = parts[0]
            if tag == 'M':
                M = int(parts[1])
            elif tag == 'N':
                N = int(parts[1])
            elif tag == 'C':
                cid      = int(parts[1])
                s        = int(parts[2])
                deadline = int(parts[3])
                duration = int(parts[4])
                courses.append(Course(cid, s, deadline, duration))

    return Problem(M, N, courses)



def exactly_one(variables: List[int]) -> List[List[int]]:
    if not variables:
        return []
    clauses: List[List[int]] = []
    # At-Least-One
    clauses.append(list(variables))
    # At-Most-One (pairwise negation)
    for vi, vj in combinations(variables, 2):
        clauses.append([-vi, -vj])
    return clauses


def clause_stats(clauses: List[List[int]]) -> Dict:
    """Count total clauses and breakdown by literal count."""
    return {
        'total' : len(clauses),
        '1-lit' : sum(1 for c in clauses if len(c) == 1),
        '2-lit' : sum(1 for c in clauses if len(c) == 2),
        '3-lit' : sum(1 for c in clauses if len(c) == 3),
        '3+lit' : sum(1 for c in clauses if len(c) > 3),
    }


#  Option 1 Encoding  —  z_{i, j, t}
#  "Course i starts in room j on day t"

def encode_option1(prob: Problem) -> Tuple[int, List[List[int]], Dict]:
    # variable allocation
    var_map: Dict[Tuple[int, int, int], int] = {}  # (course_id, room, day) -> var
    counter = 1

    for course in prob.courses:
        for j in range(1, prob.M + 1):
            for t in prob.valid_starts(course):
                var_map[(course.id, j, t)] = counter
                counter += 1

    num_vars = counter - 1
    clauses: List[List[int]] = []

    # C1: exactly-one per course
    for course in prob.courses:
        course_vars = [
            var_map[(course.id, j, t)]
            for j in range(1, prob.M + 1)
            for t in prob.valid_starts(course)
            if (course.id, j, t) in var_map
        ]
        if not course_vars:
            # No valid (room, start-day) pair → trivially UNSAT
            clauses.append([1])
            clauses.append([-1])
        else:
            clauses.extend(exactly_one(course_vars))

    # C2: no room conflict
    for j in range(1, prob.M + 1):
        for ca, cb in combinations(prob.courses, 2):
            for ta in prob.valid_starts(ca):
                for tb in prob.valid_starts(cb):
                    if (ta <= tb + cb.duration - 1) and (tb <= ta + ca.duration - 1):
                        va = var_map.get((ca.id, j, ta))
                        vb = var_map.get((cb.id, j, tb))
                        if va and vb:
                            clauses.append([-va, -vb])

    return num_vars, clauses, var_map


#  Option 2 Encoding  —  x_{i,j}  +  y_{i,t}
#  "Course i is assigned to room j"  +  "Course i starts on day t"

def encode_option2(prob: Problem) -> Tuple[int, List[List[int]], Dict, Dict]:
    # variable allocation
    x_map: Dict[Tuple[int, int], int] = {}  # (course_id, room) -> var
    y_map: Dict[Tuple[int, int], int] = {}  # (course_id, day)  -> var
    counter = 1

    for course in prob.courses:
        for j in range(1, prob.M + 1):
            x_map[(course.id, j)] = counter
            counter += 1

    for course in prob.courses:
        for t in prob.valid_starts(course):
            y_map[(course.id, t)] = counter
            counter += 1

    num_vars = counter - 1
    clauses: List[List[int]] = []

    # C1: each course in exactly one room
    for course in prob.courses:
        room_vars = [x_map[(course.id, j)] for j in range(1, prob.M + 1)]
        clauses.extend(exactly_one(room_vars))

    # 2: each course starts on exactly one day
    for course in prob.courses:
        day_vars = [
            y_map[(course.id, t)]
            for t in prob.valid_starts(course)
            if (course.id, t) in y_map
        ]
        if not day_vars:
            # No valid start day → trivially UNSAT
            clauses.append([1])
            clauses.append([-1])
        else:
            clauses.extend(exactly_one(day_vars))

    # C3: no room conflict
    for j in range(1, prob.M + 1):
        for ca, cb in combinations(prob.courses, 2):
            xa = x_map.get((ca.id, j))
            xb = x_map.get((cb.id, j))
            if xa is None or xb is None:
                continue
            for ta in prob.valid_starts(ca):
                for tb in prob.valid_starts(cb):
                    if (ta <= tb + cb.duration - 1) and (tb <= ta + ca.duration - 1):
                        ya = y_map.get((ca.id, ta))
                        yb = y_map.get((cb.id, tb))
                        if ya and yb:
                            clauses.append([-xa, -xb, -ya, -yb])

    return num_vars, clauses, x_map, y_map


#  DIMACS File Writer

def write_dimacs(filename: str, num_vars: int, clauses: List[List[int]]):
    """Write clauses to a DIMACS CNF file."""
    # Empty clauses mean UNSAT; replace with a contradictory unit pair
    processed = []
    has_empty = False
    for c in clauses:
        if len(c) == 0:
            has_empty = True
        else:
            processed.append(c)

    if has_empty:
        processed.append([1])
        processed.append([-1])

    with open(filename, 'w') as f:
        f.write(f"c DIMACS CNF generated by assg05.py\n")
        f.write(f"p cnf {num_vars} {len(processed)}\n")
        for clause in processed:
            f.write(' '.join(map(str, clause)) + ' 0\n')


#  Solver Runner

SOLVER_CMDS = {
    'z3'     : ['z3'],
    'kissat' : ['kissat'],
    'minisat': ['minisat'],
}


def run_solver(solver_name: str, cnf_file: str, timeout: int = 60) -> Dict:
    cmd = SOLVER_CMDS[solver_name] + [cnf_file]

    start_time = time.perf_counter()
    try:
        proc    = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.perf_counter() - start_time
        output  = proc.stdout + proc.stderr

        # parse SAT/UNSAT from solver output
        result = 'UNKNOWN'
        for line in output.splitlines():
            lu = line.upper().strip()
            if lu.startswith('S UNSATISFIABLE') or 'UNSATISFIABLE' in lu:
                result = 'UNSAT'
                break
            if lu.startswith('S SATISFIABLE') or lu == 'SATISFIABLE':
                result = 'SAT'
                break

        return {
            'result': result,
            'time_s': round(elapsed, 6),
            'mem_mb': _parse_memory(output),
        }

    except subprocess.TimeoutExpired:
        return {'result': 'TIMEOUT',       'time_s': timeout, 'mem_mb': 0.0}
    except FileNotFoundError:
        return {'result': 'NOT_INSTALLED', 'time_s': 0.0,     'mem_mb': 0.0}
    except Exception as e:
        return {'result': f'ERROR:{e}',    'time_s': 0.0,     'mem_mb': 0.0}


def _parse_memory(output: str) -> float:
    """
    Extract peak memory (MB) from solver output.
      Kissat  → 'c maximum-resident-set-size-mb: X'
      MiniSAT → 'Memory used:  X MB'
    Returns 0.0 if not found.
    """
    for line in output.splitlines():
        lo = line.lower()
        if 'maximum-resident' in lo or 'resident set' in lo:
            for p in line.replace(':', ' ').split():
                try:
                    return float(p)
                except ValueError:
                    pass
        if 'memory used' in lo or 'mem used' in lo:
            for p in line.split():
                try:
                    return float(p)
                except ValueError:
                    pass
    return 0.0


#  Core Solve Pipeline

def solve_problem(prob: Problem, output_prefix: str = 'output') -> Dict:
    """
    Encode the problem with both options, write DIMACS files,
    run all three solvers, and collect statistics.
    Returns a structured result dictionary.
    """
    results = {}

    for opt_label in ['option1', 'option2']:

        # encode
        t0 = time.perf_counter()
        if opt_label == 'option1':
            num_vars, clauses, *_ = encode_option1(prob)
        else:
            num_vars, clauses, *_ = encode_option2(prob)
        enc_time = time.perf_counter() - t0

        # write DIMACS
        cnf_file = f"{output_prefix}_{opt_label}.cnf"
        write_dimacs(cnf_file, num_vars, clauses)

        # collect clause stats
        stats = clause_stats(clauses)

        # run all three solvers
        solver_results = {
            name: run_solver(name, cnf_file)
            for name in SOLVER_CMDS
        }

        results[opt_label] = {
            'num_vars'      : num_vars,
            'clause_stats'  : stats,
            'encoding_time' : round(enc_time, 6),
            'cnf_file'      : cnf_file,
            'solver_results': solver_results,
        }

    return results


#  Pretty Printer

def print_results(results: Dict, prob: Problem):
    print(f"\n{'═'*64}")
    print(f"  Problem: {prob.N} courses | {prob.M} rooms | T = {prob.T}")
    print(f"{'═'*64}")

    for opt in ['option1', 'option2']:
        d     = results[opt]
        s     = d['clause_stats']
        label = 'z_{i,j,t}' if opt == 'option1' else 'x_{i,j} + y_{i,t}'

        print(f"\n  ┌─ {opt.upper()}  [{label}]")
        print(f"  │  Variables     : {d['num_vars']}")
        print(f"  │  Total clauses : {s['total']}")
        print(f"  │    1-literal   : {s['1-lit']}")
        print(f"  │    2-literal   : {s['2-lit']}")
        print(f"  │    3-literal   : {s['3-lit']}")
        print(f"  │    3+-literal  : {s['3+lit']}")
        print(f"  │  Encoding time : {d['encoding_time']} s")
        print(f"  │  CNF file      : {d['cnf_file']}")
        print(f"  │")
        print(f"  │  Solver Results:")
        for solver, sr in d['solver_results'].items():
            print(f"  │    {solver:<10}  {sr['result']:<14}"
                  f"  time={sr['time_s']:.4f}s  mem={sr['mem_mb']:.2f} MB")
        print(f"  └{'─'*60}")


#  CLI Entry Point

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('input',
                        help='Path to the input file')
    parser.add_argument('--prefix', '-p', default='output',
                        help='Prefix for generated .cnf files (default: output)')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] File not found: {args.input}")
        sys.exit(1)

    prob    = parse_input(args.input)
    results = solve_problem(prob, args.prefix)
    print_results(results, prob)


if __name__ == '__main__':
    main()
