import sys
import random
import math
import os


def generate_testcases(num_files=5):

    print(f"Generating {num_files} test case\n")

    for i in range(1, num_files + 1):
        filename = f"testcase_{i}.txt"

        # Fixing to generate 30% UNSAT test cases
        force_unsat = random.random() < 0.30

        # 1. Generate Ports (K)
        K = random.randint(2, 6)

        # 2. Generate Prices (P) - strictly increasing for faster ports
        prices = []
        current_price = random.randint(5, 15)
        for _ in range(K):
            prices.append(current_price)
            # Faster ports cost more
            current_price += random.randint(3, 10)

        # 3. Generate Vehicles (V)
        num_vehicles = random.randint(5, 20)
        vehicles = []

        # If forced unsat, pick one random vehicle to have an impossible deadline
        unsat_index = random.randint(1, num_vehicles) if force_unsat else -1

        for v_id in range(1, num_vehicles + 1):
            arrival = random.randint(0, 100)
            charge_time = random.randint(10, 50)

            if v_id == unsat_index:
                # Infeasible: Departs before it could possibly finish charging on the fastest port
                min_possible_time = math.ceil(charge_time / K)
                # Departure time is strictly less than the minimum required time
                departure = arrival + \
                    random.randint(1, max(1, min_possible_time - 1))
            else:
                # Feasible: Give it plenty of slack time to account for waiting and slower ports
                slack = random.randint(charge_time, charge_time * 2)
                departure = arrival + charge_time + slack

            vehicles.append((v_id, arrival, departure, charge_time))

        # 4. Write to file following the exact assignment format
        with open(filename, 'w') as f:
            f.write(f"% number of ports\n")
            f.write(f"K {K}\n")
            f.write(f"% Price for ports per time unit\n")
            f.write(f"P {' '.join(map(str, prices))}\n")
            f.write(
                f"% vehicle requests: id arrival-time departure-time charge-time\n")
            for v in vehicles:
                f.write(f"V {v[0]} {v[1]} {v[2]} {v[3]}\n")

        print(f"Created: {filename} ({num_vehicles} vehicles, {K} ports)")

    print("\nTest cases generated successfully.")


if __name__ == '__main__':
    num_cases = 5  # Default value

    # Check if a command line argument is provided
    if len(sys.argv) > 1:
        try:
            num_cases = int(sys.argv[1])
            if num_cases <= 0:
                print(
                    "Error: Please provide a positive integer for the number of test cases.")
                sys.exit(1)
        except ValueError:
            print("Error: The number of test cases must be an integer.")
            sys.exit(1)
    else:
        print("No number specified. Generating 5 test cases by default.")

    generate_testcases(num_cases)
