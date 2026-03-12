# Files:
- assg02.py       : The main Python source code.
- input01.txt     : Sample Input 1.
- input02.txt     : Sample Input 2.
- input03.txt     : Sample Input 3.
- README02.txt    : This file.


# Execution:
Command- python assg02.py <input_file> <COMMAND> <param1> <param2> [DELAY]

A. To Find Earliest Completion Time (Minimum Days)
   Command: FIND_m
   Param1 : Number of Students (N)
   Param2 : Prompts per Day (K)
   
   Example: 
      python assg02.py input01.txt FIND_m 3 10

B. To Find Best Subscription (Minimum K)
   Command: FIND_K
   Param1 : Number of Students (N)
   Param2 : Maximum Days Allowed (m)
   
   Example: 
      python assg02.py input01.txt FIND_K 3 5

C. The Delayed Scenario
   The flag 'DELAY' at the end of any command. This enforces the rule 
   that cross-student dependencies are only unlocked the next day at 6am.
   
   Example: 
      python assg02.py input01.txt FIND_K 3 5 DELAY


5. Output:
Sample Output
   Searching for Min K (N=2, Days=2)...
   Best Subscription (Min K) = 11
   
   --- Final Schedule ---
   Day 1:
     Student 1: Solved [A1, A2, A5]
   Day 2:
     Student 1: Solved [A8]
     Student 2: Solved [A6]