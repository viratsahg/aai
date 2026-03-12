import sys
import copy
import heapq
import time
import math

# ------------------
# 1. Data Structures
# ------------------

class Task:
    def __init__(self, tid, cost, dependencies, llm_type):
        self.id = tid
        self.cost = cost
        self.dependencies = dependencies
        self.llm_type = llm_type  # 'ChatGPT' or 'Gemini'

class SolverState:
    """
    Represents a snapshot of the scheduling process.
    """
    def __init__(self, day, completed_mask, history, chatgpt_left, gemini_left, student_load):
        self.day = day
        self.completed_mask = completed_mask # Bitmask of completed tasks
        self.history = history               # Log: { task_id: (day, student) }
        self.chatgpt_left = chatgpt_left
        self.gemini_left = gemini_left
        self.student_load = student_load     # List: Tasks done by each student today

    def __lt__(self, other):
        # Comparison for Priority Queue (min-heap) based on Day
        return self.day < other.day

    def get_key(self):
        """
        Unique state signature for A* visited set.
        If we reach the exact same configuration (mask, resources, load) 
        at a later day, it is strictly suboptimal and should be pruned.
        """
        return (self.completed_mask, tuple(self.student_load), self.chatgpt_left, self.gemini_left)

# --------------------------
# 2. Heuristics & Validation
# --------------------------

def validate_limits(tasks, Kc, Kg):
    """
    Sanity Check: Returns False if any single task costs more than the daily limit.
    Prevents infinite searching for impossible constraints.
    """
    for t in tasks.values():
        if t.llm_type == 'ChatGPT' and t.cost > Kc:
            return False
        if t.llm_type == 'Gemini' and t.cost > Kg:
            return False
    return True

def calculate_heuristic(state, tasks_data, N, Kc, Kg):
    """
    Estimates minimum days remaining.
    h(n) = max(Resource Demand)
    """
    remaining_c = 0
    remaining_g = 0
    
    for tid, task in tasks_data.items():
        if not (state.completed_mask & (1 << int(tid))):
            if task.llm_type == 'ChatGPT':
                remaining_c += task.cost
            else:
                remaining_g += task.cost

    if remaining_c == 0 and remaining_g == 0:
        return 0

    # Resource Heuristic: Total Cost / Daily Limit
    days_c = math.ceil(remaining_c / Kc) if Kc > 0 else (float('inf') if remaining_c > 0 else 0)
    days_g = math.ceil(remaining_g / Kg) if Kg > 0 else (float('inf') if remaining_g > 0 else 0)
    
    return max(days_c, days_g)

# -----------------------------
# 3. Algorithms (DFS, DFBB, A*)
# -----------------------------

class Scheduler:
    def __init__(self, N, c1, c2, tasks, case_type):
        self.N = N
        self.c1 = c1
        self.c2 = c2
        self.tasks = tasks
        self.case_type = case_type
        self.total_tasks = len(tasks)
        self.nodes_expanded = 0
        self.best_solution_days = float('inf')
        self.best_schedule = None

        # Temp storage for current run
        self.Kc = 0
        self.Kg = 0
        self.max_depth = 0

    def reset_stats(self):
        self.nodes_expanded = 0
        self.best_solution_days = float('inf')
        self.best_schedule = None

    def is_task_available(self, task, state, current_student):
        # 1. Already done?
        if state.completed_mask & (1 << int(task.id)):
            return False

        # 2. Case A Limit (Max 1 task per student)
        if self.case_type == 'CASE_A' and state.student_load[current_student-1] >= 1:
            return False
            
        # 3. Resource Limit
        if task.llm_type == 'ChatGPT':
            if task.cost > state.chatgpt_left: return False
        else:
            if task.cost > state.gemini_left: return False

        # 4. Dependencies
        for dep_id in task.dependencies:
            # Parent must be done
            if not (state.completed_mask & (1 << int(dep_id))):
                return False
            
            # Timing Rules
            p_day, _ = state.history[dep_id]
            
            if self.case_type == 'CASE_B':
                # Delayed: Must be done strictly before today
                if p_day >= state.day: return False
            else:
                # Case A: Immediate (No restriction on same-day usage if parent is done)
                pass

        return True

    # --- A* Search (Optimized) ---
    def run_astar(self, Kc, Kg):
        # 1. Sanity Check
        if not validate_limits(self.tasks, Kc, Kg):
            return float('inf'), 0

        self.Kc, self.Kg = Kc, Kg
        self.reset_stats()
        
        initial_load = tuple([0] * self.N)
        initial_state = SolverState(1, 0, {}, Kc, Kg, initial_load)
        
        # Priority Queue: (f_score, day, student_idx, state)
        pq = []
        heapq.heappush(pq, (0, 1, 1, initial_state))
        
        # Visited Set: Stores (State_Key, Student_Idx)
        visited = set()
        
        while pq:
            f, day, student_idx, state = heapq.heappop(pq)
            self.nodes_expanded += 1
            
            # Pruning: Uniqueness Check
            state_key = (state.get_key(), student_idx)
            if state_key in visited:
                continue
            visited.add(state_key)
            
            # Goal Check
            if bin(state.completed_mask).count('1') == self.total_tasks:
                self.best_solution_days = state.day
                self.best_schedule = state.history
                return state.day, self.nodes_expanded
            
            # --- Transitions ---
            
            # Option 1: Do a Task
            possible_tasks = []
            for tid, task in self.tasks.items():
                temp_state = copy.copy(state)
                temp_state.student_load = list(state.student_load)
                if self.is_task_available(task, temp_state, student_idx):
                    possible_tasks.append(task)
            
            for task in possible_tasks:
                new_mask = state.completed_mask | (1 << int(task.id))
                new_history = state.history.copy()
                new_history[task.id] = (state.day, student_idx)
                
                new_c = state.chatgpt_left - (task.cost if task.llm_type == 'ChatGPT' else 0)
                new_g = state.gemini_left - (task.cost if task.llm_type == 'Gemini' else 0)
                
                new_load = list(state.student_load)
                new_load[student_idx-1] += 1
                
                new_state = SolverState(state.day, new_mask, new_history, new_c, new_g, tuple(new_load))
                
                g = state.day
                h = calculate_heuristic(new_state, self.tasks, self.N, Kc, Kg)
                heapq.heappush(pq, (g + h, state.day, student_idx, new_state))

            # Option 2: Pass Turn
            next_student = (student_idx % self.N) + 1
            if next_student == 1:
                # Next Day
                new_state = SolverState(state.day + 1, state.completed_mask, state.history, 
                                        self.Kc, self.Kg, tuple([0]*self.N))
                g_next = state.day + 1
            else:
                # Same Day, Next Student
                new_state = SolverState(state.day, state.completed_mask, state.history,
                                        state.chatgpt_left, state.gemini_left, state.student_load)
                g_next = state.day
            
            h = calculate_heuristic(new_state, self.tasks, self.N, Kc, Kg)
            heapq.heappush(pq, (g_next + h, g_next, next_student, new_state))

        return float('inf'), self.nodes_expanded

    # --- DFS & DFBB ---
    def run_dfs(self, Kc, Kg, limit_days):
        if not validate_limits(self.tasks, Kc, Kg): return float('inf'), 0
        self.Kc, self.Kg = Kc, Kg
        self.max_depth = limit_days
        self.reset_stats()
        self._dfs_recursive(SolverState(1, 0, {}, Kc, Kg, [0]*self.N), 1)
        return self.best_solution_days, self.nodes_expanded

    def _dfs_recursive(self, state, student_idx):
        self.nodes_expanded += 1
        if state.day > self.max_depth: return
        if bin(state.completed_mask).count('1') == self.total_tasks:
            if state.day < self.best_solution_days: self.best_solution_days = state.day
            return

        possible_tasks = [t for t in self.tasks.values() if self.is_task_available(t, state, student_idx)]
        
        # Branch 1: Do Tasks
        for task in possible_tasks:
            new_mask = state.completed_mask | (1 << int(task.id))
            new_hist = state.history.copy()
            new_hist[task.id] = (state.day, student_idx)
            new_c = state.chatgpt_left - (task.cost if task.llm_type=='ChatGPT' else 0)
            new_g = state.gemini_left - (task.cost if task.llm_type=='Gemini' else 0)
            new_load = list(state.student_load)
            new_load[student_idx-1] += 1
            
            self._dfs_recursive(SolverState(state.day, new_mask, new_hist, new_c, new_g, new_load), student_idx)

        # Branch 2: Pass
        next_student = (student_idx % self.N) + 1
        if next_student == 1:
            self._dfs_recursive(SolverState(state.day + 1, state.completed_mask, state.history, 
                                            self.Kc, self.Kg, [0]*self.N), 1)
        else:
            self._dfs_recursive(SolverState(state.day, state.completed_mask, state.history,
                                            state.chatgpt_left, state.gemini_left, state.student_load), next_student)

    def run_dfbb(self, Kc, Kg, limit_days):
        if not validate_limits(self.tasks, Kc, Kg): return float('inf'), 0
        self.Kc, self.Kg = Kc, Kg
        self.max_depth = limit_days
        self.reset_stats()
        self._dfbb_recursive(SolverState(1, 0, {}, Kc, Kg, [0]*self.N), 1)
        return self.best_solution_days, self.nodes_expanded

    def _dfbb_recursive(self, state, student_idx):
        self.nodes_expanded += 1
        
        # Pruning
        h = calculate_heuristic(state, self.tasks, self.N, self.Kc, self.Kg)
        if state.day + h >= self.best_solution_days: return
        if state.day > self.max_depth: return

        if bin(state.completed_mask).count('1') == self.total_tasks:
            self.best_solution_days = state.day
            return

        possible_tasks = [t for t in self.tasks.values() if self.is_task_available(t, state, student_idx)]
        possible_tasks.sort(key=lambda x: x.cost, reverse=True) # Greedy ordering

        for task in possible_tasks:
            new_mask = state.completed_mask | (1 << int(task.id))
            new_hist = state.history.copy()
            new_hist[task.id] = (state.day, student_idx)
            new_c = state.chatgpt_left - (task.cost if task.llm_type=='ChatGPT' else 0)
            new_g = state.gemini_left - (task.cost if task.llm_type=='Gemini' else 0)
            new_load = list(state.student_load)
            new_load[student_idx-1] += 1
            
            self._dfbb_recursive(SolverState(state.day, new_mask, new_hist, new_c, new_g, new_load), student_idx)

        next_student = (student_idx % self.N) + 1
        if next_student == 1:
            self._dfbb_recursive(SolverState(state.day + 1, state.completed_mask, state.history, 
                                             self.Kc, self.Kg, [0]*self.N), 1)
        else:
            self._dfbb_recursive(SolverState(state.day, state.completed_mask, state.history,
                                             state.chatgpt_left, state.gemini_left, state.student_load), next_student)

# -----------------
# 4. Input & Output
# -----------------

def parse_input_file(filename):
    tasks = {}
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith('%') or line.startswith('N') or line.startswith('K'):
                continue
            if parts := line.split():
                if parts[0] == 'A':
                    tid = parts[1]
                    cost = int(parts[2])
                    deps = parts[3:-1]
                    llm = 'ChatGPT' if int(tid) % 2 == 0 else 'Gemini'
                    tasks[tid] = Task(tid, cost, deps, llm)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    return tasks

def print_schedule(history, tasks):
    if not history: return
    organized = {}
    days = sorted(list(set(val[0] for val in history.values())))
    
    for tid, (day, student) in history.items():
        if day not in organized: organized[day] = {}
        if student not in organized[day]: organized[day][student] = []
        organized[day][student].append((tid, tasks[tid].llm_type))

    print("\n>>> Optimal Schedule (from A*):")
    for d in days:
        print(f"Day {d}:")
        if d in organized:
            for s in sorted(organized[d].keys()):
                # Format: A1(Gemini)
                t_list = [f"A{t[0]}({t[1]})" for t in organized[d][s]]
                print(f"  Student {s}: Solved [{', '.join(t_list)}]")
    print("----------------------\n")

# -------
# 5. Main
# -------

def main():
    if len(sys.argv) < 7:
        print("Usage: python assg03.py <input> <CASE> <QUERY> <N> <c1> <c2> [Params...]")
        sys.exit(1)

    filename = sys.argv[1]
    case_type = sys.argv[2]
    query_type = sys.argv[3]
    N = int(sys.argv[4])
    c1 = int(sys.argv[5])
    c2 = int(sys.argv[6])
    
    tasks = parse_input_file(filename)
    scheduler = Scheduler(N, c1, c2, tasks, case_type)
    
    print(f"\nRunning {query_type} for {case_type} (N={N}, c1={c1}, c2={c2})...")

    # --- MIN DAYS ---
    if query_type == "MIN_DAYS":
        if len(sys.argv) < 9:
            print("Error: MIN_DAYS requires <Kc> <Kg>")
            sys.exit(1)
        Kc = int(sys.argv[7])
        Kg = int(sys.argv[8])
        
        # 1. A*
        t0 = time.time()
        res_astar, nodes_astar = scheduler.run_astar(Kc, Kg)
        t_astar = time.time() - t0
        
        # Capturing Schedules for display
        final_schedule_log = copy.deepcopy(scheduler.best_schedule)
        
        if res_astar == float('inf'):
            print("\n!!! NO VALID SOLUTION EXISTS (Check Constraints/Limits) !!!")
            return

        # 2. DFBB
        t0 = time.time()
        res_dfbb, nodes_dfbb = scheduler.run_dfbb(Kc, Kg, res_astar + 5)
        t_dfbb = time.time() - t0
        
        # 3. DFS
        t0 = time.time()
        res_dfs, nodes_dfs = scheduler.run_dfs(Kc, Kg, res_astar + 2)
        t_dfs = time.time() - t0
        
        print("\n--- Algorithm Performance Report ---")
        print(f"| {'Algorithm':<10} | {'Nodes':<10} | {'Time (s)':<8} | {'Result':<6} |")
        print(f"| {'DFS':<10} | {nodes_dfs:<10} | {t_dfs:<8.4f} | {res_dfs:<6} |")
        print(f"| {'DFBB':<10} | {nodes_dfbb:<10} | {t_dfbb:<8.4f} | {res_dfbb:<6} |")
        print(f"| {'A*':<10} | {nodes_astar:<10} | {t_astar:<8.4f} | {res_astar:<6} |")
        
        print(f"\n>>> Earliest Completion Time: {res_astar} Days")
        # Schedule Printing
        print_schedule(final_schedule_log, tasks)

    # --- MIN COST ---
    elif query_type == "MIN_COST":
        if len(sys.argv) < 8:
            print("Error: MIN_COST requires <Days_m>")
            sys.exit(1)
        max_days = int(sys.argv[7])
        
        sum_c = sum(t.cost for t in tasks.values() if t.llm_type == 'ChatGPT')
        sum_g = sum(t.cost for t in tasks.values() if t.llm_type == 'Gemini')
        
        best_cost = float('inf')
        best_config = None
        best_schedule_log = None
        
        print(f"Optimizing... (Deadline: {max_days})")
        
        # Iterate Kc
        for kc_test in range(1, sum_c + 2):
            # Binary Search Kg
            low, high = 1, sum_g + 1
            min_valid_kg = -1
            
            # Temp storage for the best schedule found IN THIS INNER LOOP
            current_loop_schedule = None
            
            while low <= high:
                mid_kg = (low + high) // 2
                days, _ = scheduler.run_astar(kc_test, mid_kg)
                
                if days <= max_days:
                    min_valid_kg = mid_kg
                    # Capture schedule immediately if valid
                    current_loop_schedule = copy.deepcopy(scheduler.best_schedule)
                    high = mid_kg - 1
                else:
                    low = mid_kg + 1
            
            if min_valid_kg != -1:
                total = (c1 * kc_test) + (c2 * min_valid_kg)
                if total < best_cost:
                    best_cost = total
                    best_config = (kc_test, min_valid_kg)
                    best_schedule_log = current_loop_schedule
        
        if best_config:
            kc_opt, kg_opt = best_config
            _, nodes_astar = scheduler.run_astar(kc_opt, kg_opt)
            _, nodes_dfbb = scheduler.run_dfbb(kc_opt, kg_opt, max_days)
            _, nodes_dfs = scheduler.run_dfs(kc_opt, kg_opt, max_days)
            
            print("\n--- Algorithm Performance Report (Verification Run) ---")
            print(f"| {'Algorithm':<10} | {'Nodes':<10} | {'Result':<6} |")
            print(f"| {'DFS':<10} | {nodes_dfs:<10} | {'Valid':<6} |")
            print(f"| {'DFBB':<10} | {nodes_dfbb:<10} | {'Valid':<6} |")
            print(f"| {'A*':<10} | {nodes_astar:<10} | {'Valid':<6} |")

            print("\n>>> Optimization Result:")
            print(f"  Best Scheme: Kc={kc_opt}, Kg={kg_opt}")
            print(f"  Total Cost : {best_cost}")
            # Schedule Printing
            print_schedule(best_schedule_log, tasks)
        else:
            print("Impossible to finish within deadline.")

if __name__ == "__main__":
    main()