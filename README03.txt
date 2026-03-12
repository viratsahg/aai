# Files:
- assg03.py       : The main Python source code.
- README03.txt    : This file.

# Execution:
Command- python assg03.py <input_file> <CASE> <QUERY> <N> <c1> <c2> [Params]

# Parameters:
  <CASE>  : 'CASE_A' (Single Task) or 'CASE_B' (Multi-Task + Delayed)
  <QUERY> : 'MIN_DAYS' or 'MIN_COST'
  <N>     : Number of Students
  <c1>    : Cost per ChatGPT prompt
  <c2>    : Cost per Gemini prompt

   A. To Find Earliest Completion Time (MIN_DAYS)
      Command: MIN_DAYS
      Param1 : Daily Limit for ChatGPT (Kc)
      Param2 : Daily Limit for Gemini (Kg)
      
      Example (Case A): 
         python assg03.py input.txt CASE_A MIN_DAYS 3 10 15 5 5

   B. To Find Best Subscription Scheme (MIN_COST)
      Command: MIN_COST
      Param1 : Deadline in Days (m)
      
      Example (Case B): 
         python assg03.py input.txt CASE_B MIN_COST 3 10 15 7


# Output:

Sample Output (MIN_DAYS):
   Running MIN_DAYS for CASE_A (N=3, c1=10, c2=15)...

   --- Algorithm Performance Report ---
   | Algorithm | Nodes      | Time (s) | Result |
   | DFS       | 14520      | 4.2100   | 6      |
   | DFBB      | 1245       | 0.3500   | 6      |
   | A* | 840        | 0.0200   | 6      |

   >>> Earliest Completion Time: 6 Days

   >>> Optimal Schedule (from A*):
   Day 1:
     Student 1: Solved [A1(Gemini)]
     Student 2: Solved [A3(Gemini)]
   Day 2:
     Student 1: Solved [A2(ChatGPT)]