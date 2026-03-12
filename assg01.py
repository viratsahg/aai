import sys


# Defining global variables
N = 0
K = 0
# The tasks dictionary will store everything
# Key is the ID. Value is a list: [cost, dependencies_list, is_completed_boolean]
tasks = {}
total_tasks_count = 0
max_days_allowed = 0
solution_count = 0


def solve(day, student, prompts_left, completed_count, path):
    global solution_count

    # Base condition to check if all tasks are finished
    if completed_count == total_tasks_count:
        solution_count = solution_count + 1
        print("Solution Found: " + str(solution_count))
        # Open file in append mode, to write the output in a output file
        f_out = open("output.txt", "a")
        f_out.write("Solution Found: " + str(solution_count) + "\n")

        # Print as well as write to output file the schedules
        for p in path:
            print(p)
            f_out.write(p + "\n")
        print("--------------------------------------------------")
        f_out.write("--------------------------------------------------\n")
        f_out.close()

        return

    # Check if the day limit is exhausted
    if day > max_days_allowed:
        return

    # Sorting keys to make sure to check them in order A1, A2...
    all_ids = sorted(tasks.keys())


    for id in all_ids:
        # Get the task details from the dictionary
        # t[0] is cost, t[1] is dependency list, t[2] is is_completed
        t = tasks[id]

        # 1. Check if task is already done
        if t[2] == True:
            continue

        # 2. Check dependencies (parents)
        parents_are_done = True
        for parent_id in t[1]:
            # if parent is not done
            if tasks[parent_id][2] == False:
                parents_are_done = False
                break

        # If dependencies are met, check if enough prompts are left
        if parents_are_done == True:
            if t[0] <= prompts_left:
                #Prompts left, task can be done.

                # Step 1: Mark as done
                tasks[id][2] = True

                # Step 2: Add to history path
                # Scheduels updated
                action_string = "Day " + \
                    str(day) + " Student " + str(student) + \
                    " --> A" + str(id)
                path.append(action_string)

                #Recursively calling solve() with same student  but with remaining prompts left
                solve(day, student, prompts_left -
                      t[0], completed_count + 1, path)

                # Step 4: Backtrack (Undo changes for the next loop)
                tasks[id][2] = False
                path.pop()

    # After trying all tasks for this student, we also need to try the option
    # where the student stops working for the day and passes to the next person.

    next_student = student + 1
    next_day = day

    # If we go past student N, we move to the next day and reset student to 1
    if next_student > N:
        next_student = 1
        next_day = day + 1

    # Recursive call for the next person (reset prompts to K)
    # This acts as the "pass" turn
    solve(next_day, next_student, K, completed_count, path)


# Main part of the code

# Clear the output file before starting
open("output.txt", "w").close()

# Read command line arguments
# args[1] is filename, args[2] is days

args = sys.argv
filename = args[1]
days_input = args[2]
max_days_allowed = int(days_input)

print("Reading file: " + filename)
f_out = open("output.txt", "a")
f_out.write("Reading file: " + filename + "\n")
f_out.close()


# Opening the file
f = open(filename, "r")
lines = f.readlines()
f.close()

# Parsing the file line by line
for line in lines:
    line = line.strip()

    # Skip comments and empty lines
    if len(line) == 0:
        continue
    if line[0] == "%":
        continue

    parts = line.split()

    if parts[0] == "N":
        N = int(parts[1])
    elif parts[0] == "K":
        K = int(parts[1])
    elif parts[0] == "A":
        # Format: A <id> <cost> <dep1> <dep2> ... 0
        task_id = parts[1]
        cost = int(parts[2])

        # Dependencies are from index 3 to the end minus 1 (the 0)
        deps = parts[3:]
        deps.pop()  # remove the last 0

        # Save to dictionary: [cost, deps, False]
        # False means not completed yet
        tasks[task_id] = [cost, deps, False]

total_tasks_count = len(tasks)
print("Total Assignments loaded: " + str(total_tasks_count))
print("Start searching for schedules...")

f_out = open("output.txt", "a")
f_out.write("Total Assignments loaded: " + str(total_tasks_count) + "\n")
f_out.write("Start searching for schedules...\n")
f_out.write("--------------------------------------------------\n")
f_out.close()


# Start the recursion
# Day 1, Student 1, Full K prompts, 0 completed, empty path list
solve(1, 1, K, 0, [])

if solution_count == 0:
    print("No solutions found.")

    # Open file in append mode
    f_out = open("output.txt", "a")
    f_out.write("No solutions found.\n")
    f_out.write("-------------------\n")
    f_out.close()
