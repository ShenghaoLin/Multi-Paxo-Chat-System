# Multi-Paxo-Chat-System

# How to Use

Terminal commands:

python replica_batch.py $kill_number [$message_loss_prob]

python replica.py $replica_id [$message_loss_prob]

python client_batch.py [$message_loss_prob]

python client.py $client_name [$message_loss_prob]


Commands in replica cmdl mode:

start; kill me; skip slot; 


# Run test case 1: batch mode
Run client in batch mode: python replica_batch.py $kill_number [$message_loss_prob], where $kill_number is the number of primaries to kill during running, and $message_loss_prob is optional.

Run replica in batch mode: python client_batch.py [$message_loss_prob], as defined above.

# Run test case 2: primary dies

Run 2f+1 replicas separately first: python replica.py $replica_id , where $replica_id is integers for processor ids.

Run client separately: python client.py $client_name,  where $replica_id is integers for client names.

For replica 0, run command "Kill me"

See log files for results.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# Run test case 3: primary dies, view change
Run 2f+1 replicas separately first: python replica.py $replica_id , where $replica_id is integers for processor ids.

Run client separately: python client.py $client_name,  where $replica_id is integers for client names.

For f numbers of relicas, run command "Kill me"

See log files for results.

# Run test case 4: Skipped slot
Run 2f+1 replicas separately first: python replica.py $replica_id , where $replica_id is integers for processor ids.

Run client separately: python client.py $client_name,  where $client_name is the unique client names.

In the primary replica's command window, type "Skip slot" command

See log files for results.


# Run test case 5: Message loss
Optional argument [$message_loss_prob] is avaible in all modes.

Run client in batch mode: python client_batch.py [$message_loss_probability]

Run replica in batch mode: python replica_batch.py [$message_loss_probability]

The consensus system is alive when p is small, for example, p = 0.01



# Update Log

Update: Replica can run seperately, during which time termination and skipping slots work. It seems to the only thing left is to test the performance in message loss mode.

TODO: Run replicas seperately; Create functions to control terminating replicas; Create Skipped slot error trigger.

Update: Skipped slot recovery supported

Update: Message loss supported (not tested)

Update: Command line chatting mode supported. Batch mode is moved to a single file called client_batch.py. To run client.py, use "python client.py #clientname".

Update: Batch mode supported in normal cases and case of several primary dead. Performance in other situation is not sure. More tests are needed. Run "python replica.py" in one terminal and run "python client.py" in another. log files are generated.

Update: Multi-Paxos supported. Try to run "python replica.py" and see the log files.
