import sys
import copy


class SolverState:
    """
    Encapsulates the state of a single feasibility check.
    """
    def __init__(self, n_students, k_prompts, max_days, tasks, delayed_mode):
        self.N = n_students
        self.K = k_prompts
        self.max_days = max_days
        self.tasks = tasks  # Dictionary of tasks
        self.delayed_mode = delayed_mode
        self.total_tasks = len(tasks)
        
        # Tracks completion details: { task_id: (day_completed, student_id) }
        self.completion_log = {} 
        
        # Stores the successful schedule if one is found
        self.final_schedule = None


def check_feasibility(N, K, max_days, raw_tasks, delayed_mode=False):
    """
    Returns: (True, schedule_log) if feasible, (False, None) otherwise.
    """
    tasks_copy = copy.deepcopy(raw_tasks)
    state = SolverState(N, K, max_days, tasks_copy, delayed_mode)
    initial_prompts = [K] * N
    
    success = backtrack(1, 1, initial_prompts, 0, 0, state)
    return success, state.final_schedule

def backtrack(day, student_id, current_prompts, completed_count, consecutive_passes, state):
    # 1. Base Case: Success
    if completed_count == state.total_tasks:
        # Capture the current log as the final schedule before returning
        state.final_schedule = state.completion_log.copy()
        return True

    # 2. Base Case: Failure
    if day > state.max_days:
        return False

    # 3. End of Day Check
    if consecutive_passes == state.N:
        new_prompts = [state.K] * state.N
        return backtrack(day + 1, 1, new_prompts, completed_count, 0, state)

    # 4. Attempt to assign a task
    my_prompts_left = current_prompts[student_id - 1]
    all_ids = sorted(state.tasks.keys())

    for tid in all_ids:
        t = state.tasks[tid] # [cost, deps, is_completed]
        
        if t[2]: continue # Already done
            
        # Check Dependencies
        parents_met = True
        for pid in t[1]:
            if not state.tasks[pid][2]: # Parent not done
                parents_met = False
                break
            
            if state.delayed_mode:
                p_day, p_student = state.completion_log[pid]
                # Rule: Previous day OR Same day & Same student
                if p_day < day: continue 
                elif p_day == day and p_student == student_id: continue
                else:
                    parents_met = False
                    break
        
        # Check Cost
        if parents_met and t[0] <= my_prompts_left:
            # Do Task
            t[2] = True
            state.completion_log[tid] = (day, student_id)
            current_prompts[student_id - 1] -= t[0]
            
            if backtrack(day, student_id, current_prompts, completed_count + 1, 0, state):
                return True 
            
            # Undo
            t[2] = False
            del state.completion_log[tid]
            current_prompts[student_id - 1] += t[0]

    # 5. Pass Turn
    next_student = (student_id % state.N) + 1
    return backtrack(day, next_student, current_prompts, completed_count, consecutive_passes + 1, state)

def print_schedule(schedule_log):
    """
    Prints the schedule from the log dictionary.
    Log format: { task_id: (day, student) }
    """
    if not schedule_log:
        return

    # Invert log to: { Day: { Student: [Tasks] } }
    organized = {}
    days = sorted(list(set(val[0] for val in schedule_log.values())))
    
    for tid, (day, student) in schedule_log.items():
        if day not in organized: organized[day] = {}
        if student not in organized[day]: organized[day][student] = []
        organized[day][student].append(tid)

    print("\n--- Final Schedule ---")
    for d in days:
        print(f"Day {d}:")
        if d in organized:
            for s in sorted(organized[d].keys()):
                tasks = ", A".join(organized[d][s])
                print(f"  Student {s}: Solved [A{tasks}]")

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
                    tasks[parts[1]] = [int(parts[2]), parts[3:-1], False]
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    return tasks

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    if len(sys.argv) < 5:
        print("Mismatch in the number of parameters.\nCorrect command: python assg02.py <input_file> <COMMAND> <param1> <param2> [DELAY]")
        sys.exit(1)

    filename = sys.argv[1]
    command = sys.argv[2]
    param1 = int(sys.argv[3])
    param2 = int(sys.argv[4])
    delayed_mode = len(sys.argv) > 5 and sys.argv[5] == "DELAY"
    
    if delayed_mode: print(">>> Mode: Delayed Exchange ENABLED <<<")

    raw_tasks_data = parse_input_file(filename)
    total_cost_sum = sum(t[0] for t in raw_tasks_data.values())
    max_single_cost = max(t[0] for t in raw_tasks_data.values())

    if command == "FIND_m":
        N, K = param1, param2
        print(f"Searching for Minimum Days (N={N}, K={K})...")
        
        for d in range(1, total_cost_sum + 2):
            is_feasible, schedule = check_feasibility(N, K, d, raw_tasks_data, delayed_mode)
            if is_feasible:
                print(f"Earliest Completion Time = {d} Days")
                print_schedule(schedule)
                return
        print("No feasible schedule found.")

    elif command == "FIND_K":
        N, max_days = param1, param2
        print(f"Searching for Min K (N={N}, Days={max_days})...")
        
        low, high = max_single_cost, total_cost_sum
        best_k = -1
        best_schedule = None
        
        while low <= high:
            mid_k = (low + high) // 2
            is_feasible, schedule = check_feasibility(N, mid_k, max_days, raw_tasks_data, delayed_mode)
            
            if is_feasible:
                best_k = mid_k
                best_schedule = schedule
                high = mid_k - 1
            else:
                low = mid_k + 1
        
        if best_k != -1:
            print(f"Best Subscription (Min K) = {best_k}")
            print_schedule(best_schedule)
        else:
            print(f"Impossible to complete in {max_days} days.")

if __name__ == "__main__":
    main()