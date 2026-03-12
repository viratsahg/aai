import sys
import math
from z3 import *


def parse_input(filename):
    K = 0
    prices = []
    vehicles = []

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignore comments and empty lines
                if not line or line.startswith('%'):
                    continue

                parts = line.split()
                if parts[0] == 'K':
                    K = int(parts[1])
                elif parts[0] == 'P':
                    # Prices for ports 1 to K
                    prices = [int(x) for x in parts[1:]]
                elif parts[0] == 'V':
                    # V <id> <arrival> <departure> <charge_time>
                    v_id = parts[1]
                    arr = int(parts[2])
                    dep = int(parts[3])
                    c = int(parts[4])
                    vehicles.append(
                        {'id': v_id, 'arr': arr, 'dep': dep, 'c': c})

    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    return K, prices, vehicles


def solve_ev_scheduling(K, prices, vehicles):
    # Create the optimizer instance
    opt = Optimize()

    # Dictionaries to store Z3 variables for each vehicle
    port_vars = {}
    start_vars = {}
    duration_vars = {}
    cost_vars = {}

    # 1. Setup Variables and Individual Vehicle Constraints
    for v in vehicles:
        vid = v['id']

        # Z3 Integer variables
        p_var = Int(f"port_{vid}")
        s_var = Int(f"start_{vid}")
        d_var = Int(f"dur_{vid}")
        c_var = Int(f"cost_{vid}")

        port_vars[vid] = p_var
        start_vars[vid] = s_var
        duration_vars[vid] = d_var
        cost_vars[vid] = c_var

        # Domain constraints
        opt.add(p_var >= 1, p_var <= K)      # Port must be between 1 and K
        # Must start after or at arrival time
        opt.add(s_var >= v['arr'])
        # Must finish before or at departure time
        opt.add(s_var + d_var <= v['dep'])

        # Link port selection to charging duration and cost
        for k in range(1, K + 1):
            # Calculate duration for port k: ceil(c_i / k)
            dur_k = math.ceil(v['c'] / k)
            # Calculate cost: duration * price_of_port
            cost_k = dur_k * prices[k - 1]

            # If port k is chosen, set the respective duration and cost
            opt.add(Implies(p_var == k, d_var == dur_k))
            opt.add(Implies(p_var == k, c_var == cost_k))

    # 2. Setup Overlap Constraints
    # No two vehicles can use the same port at the same time
    v_ids = [v['id'] for v in vehicles]
    num_vehicles = len(v_ids)

    for i in range(num_vehicles):
        for j in range(i + 1, num_vehicles):
            vid1 = v_ids[i]
            vid2 = v_ids[j]

            # If vehicle 1 and vehicle 2 are assigned to the SAME port
            same_port_condition = (port_vars[vid1] == port_vars[vid2])

            # Then they must NOT overlap in time
            # v1 finishes before v2 starts OR v2 finishes before v1 starts
            no_overlap_condition = Or(
                start_vars[vid1] + duration_vars[vid1] <= start_vars[vid2],
                start_vars[vid2] + duration_vars[vid2] <= start_vars[vid1]
            )

            # Add to optimizer
            opt.add(Implies(same_port_condition, no_overlap_condition))

    # 3. Define Objective Function
    # We want to minimize the total cost of charging
    total_cost = Sum([cost_vars[vid] for vid in v_ids])
    opt.minimize(total_cost)

    # 4. Solve and Extract Result
    print("Finding optimal schedule")
    if opt.check() == sat:
        model = opt.model()

        print("\nOptimal Schedule Found")
        final_cost = model.eval(total_cost).as_long()
        print(f"Total Minimized Cost: {final_cost}\n")

        print(
            f"{'Vehicle ID':<12} | {'Port':<6} | {'Start Time':<12} | {'End Time':<10} | {'Cost':<6}")
        print("-" * 55)

        for vid in v_ids:
            p_val = model.eval(port_vars[vid]).as_long()
            s_val = model.eval(start_vars[vid]).as_long()
            d_val = model.eval(duration_vars[vid]).as_long()
            c_val = model.eval(cost_vars[vid]).as_long()

            e_val = s_val + d_val  # End time
            print(
                f"V {vid:<10} | {p_val:<6} | {s_val:<12} | {e_val:<10} | {c_val:<6}")

    else:
        print("\nUNSATISFIABLE")
        print("No valid schedule exists.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python assg04.py <input_file.txt>")
        sys.exit(1)

    filename = sys.argv[1]
    K, prices, vehicles = parse_input(filename)

    print(f"Provided data: {K} Ports")
    print(f"Port Prices: {prices}")
    print(f"Total Vehicle Requests: {len(vehicles)}\n")

    solve_ev_scheduling(K, prices, vehicles)


if __name__ == "__main__":
    main()
