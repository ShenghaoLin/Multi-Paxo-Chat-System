# Multi-Paxo-Chat-System

# How to Use

Terminal commands:

python replica_batch.py $kill_number [$message_loss_prob]

python replica.py $replica_id [$message_loss_prob]

python client_batch.py [$message_loss_prob]

python client.py $client_name [$message_loss_prob]


Commands in replica cmdl mode:

start; kill me; skip slot; 


Config file: servers.config, add more servers as you like

client message files: messages.txt, messages2.txt, messages3.txt. 


# Run test case 1: batch mode
Run replica in batch mode: python replica_batch.py $kill_number [$message_loss_prob], where $kill_number is the number of primaries to kill during running, and $message_loss_prob is optional.

Run client in batch mode: python client_batch.py [$message_loss_prob], as defined above.

# Run test case 2: primary dies

Run 2f+1 replicas separately first: python replica.py $replica_id , where $replica_id is integers for processor ids.

Run client separately: python client.py $client_name,  where $replica_id is integers for client names.

For replica 0, run command "Kill me"

See log files for results.

++++++++++++++++++++++++++++++++Batch mode test+++++++++++++++++++++++++++++++++++++++

Run replica in batch mode: python replica_batch.py $kill_number, where $kill_number is 1

Run client in batch mode: python client_batch.py

The system should perform view change process once

# Run test case 3: primary dies, view change
Run 2f+1 replicas separately first: python replica.py $replica_id , where $replica_id is integers for processor ids.

Run client separately: python client.py $client_name,  where $replica_id is integers for client names.

For f numbers of relicas, run command "Kill me"

See log files for results.

++++++++++++++++++++++++++++++++Batch mode test+++++++++++++++++++++++++++++++++++++++

Run replica in batch mode: python replica_batch.py $kill_number

Run client in batch mode: python client_batch.py

The system works properly when $kill_number is <= f, where 2f+1 is the number of servers in servers.config file


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

