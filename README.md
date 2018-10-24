# Multi-Paxo-Chat-System

# How to Use

Run replica seperately: python replica.py $replica_id
And then there are 3 commands you can use: "Start", "Kill me" and "Skip slot".
(Plese only use Start command after start all the replicas!)

Run replica in batch mode: python replica_batch.py

Run client seperately: python client.py $client_name
(clients should have different names)

Run client in batch mode: python client_batch.py

# Update Log

Update: Replica can run seperately, during which time termination and skipping slots work. It seems to the only thing left is to test the performance in message loss mode.

TODO: Run replicas seperately; Create functions to control terminating replicas; Create Skipped slot error trigger.

Update: Skipped slot recovery supported

Update: Message loss supported (not tested)

Update: Command line chatting mode supported. Batch mode is moved to a single file called client_batch.py. To run client.py, use "python client.py #clientname".

Update: Batch mode supported in normal cases and case of several primary dead. Performance in other situation is not sure. More tests are needed. Run "python replica.py" in one terminal and run "python client.py" in another. log files are generated.

Update: Multi-Paxos supported. Try to run "python replica.py" and see the log files.