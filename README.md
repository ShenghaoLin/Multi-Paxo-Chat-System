# Multi-Paxo-Chat-System

Update: Message loss supported (not tested)

Update: Command line chatting mode supported. Batch mode is moved to a single file called client_batch.py. To run client.py, use "python client.py #clientname".

Update: Batch mode supported in normal cases and case of several primary dead. Performance in other situation is not sure. More tests are needed. Run "python replica.py" in one terminal and run "python client.py" in another. log files are generated.

Update: Multi-Paxos supported. Try to run "python replica.py" and see the log files.