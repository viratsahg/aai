#File structure
-----------------
- assg01.py     : Python source code.
- input01.txt   : Sample Input 1.
- input02.txt   : Sample Input 2.
- input03.txt   : Sample Input 3.
- README01.txt  : This file.
- output.txt    : Stores the schedule results (Generated at runtime).

#Requirements
---------------
- Python 3.x is required to run this program.
- No external libraries are needed (uses standard 'sys').

#Compilation & Execution
--------------------------
This is a Python script, no separate compilation needed. 
The source code is interpreted directly.

#Execution step:
1. Open the terminal or command prompt.
2. Navigate to the directory containing 'assg01.py' and the input files.
3. Run the program using the following command syntax:

   python assg01.py <input_filename> <number_of_days>

   Note: Depending on the OS, we can use 'python' or 'python3'.

#Execution Example
-----------------
To run the scheduler with the provided sample inputs:

Example 1:
   python assg01.py input01.txt 8

Example 2:
   python assg01.py input02.txt 6

Example 3:
   python assg01.py input03.txt 7


#Output
---------
- The program prints "Solution Found: <count>" to the console as it progresses.
- The detailed schedules are appended to 'output.txt' in the same directory.
- Note: The program clears the 'output.txt' file automatically at the start 
  of every new run.