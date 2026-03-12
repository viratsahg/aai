=========================================================
Test Case Generator (genTestcases.py)
=========================================================

Description:
This script automatically generates formatted text files to be used as test cases for the EV Charging Station Scheduler. It creates random scenarios, secretly injecting mathematically unsatisfiable conditions into roughly 30% of the files to thoroughly test the solver.

Prerequisites:
- Python 3 (No external libraries required)

Usage:
    python genTestcases.py [number_of_test_cases]

Examples:
    python genTestcases.py      (Generates 5 test cases by default)
    python genTestcases.py 15   (Generates 15 test cases)

Output:
Creates files named `testcase_1.txt`, `testcase_2.txt`, etc., in the current directory.