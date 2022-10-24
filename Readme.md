CS456 Assignemnt 2   Developed by Joyce Li. \
The program is built by Python 3.8.10. \
The program is built and tested on ubuntu2004-002.student.cs.uwaterloo.ca

Usage: \
    We need 3 hosts to execute the program. \
    1. On host1: python3 network_emulator.py \<port1> host2 \<port4> \<port3> \<host3> \<port2> <max_delay> \<p> \<verbose-mode> \
    2. On host2: python3 receiver.py host1 \<port3> \<port4> \<output_file> \
    3. On host3: python3 sender.py host1 \<port1> \<port2> \<timeout> \<input_file>
    
    port1-4 are 4 avalible ports,
    host1-3 are CS student environment machines,
    max_delay: maximum delay of the link in units of millisecond,
    p: packet discard probability,
    verbose-mode: Boolean: Set to 1,the network emulator will output its internal processing,
    timeout: timeout interval in units of millisecond.

Note: the output file will be overwritten every time you run the program, whereas the log files will not. If you want to overwrite log files, please remove them before running the program by running rm *.log in command line.
