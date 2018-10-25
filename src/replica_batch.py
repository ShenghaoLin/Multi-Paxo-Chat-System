#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Script used to run clients in batch mode.
	
	At least 1 parameter should be given: the number of times primary dies

	Message loss probability can be given as a second (optional) command line argument

	The command to use is "python replica_batch.py $no_primary_die [$message_loss_probability]"

	@author: Shenghao Lin, Yangming Ke
"""

from replica import *

if __name__ == '__main__':
	config = get_config('../data/servers.config')
	replicas = list()
	processes = list()

	prob = 0
	if len(sys.argv) > 2:
		prob = float(sys.argv[2])

	for i in range(len(config)):
		replicas.append(Replica(i, config, 0, p = prob))

	kill_till = int(sys.argv[1])

	for i in range(len(config)):
		p = Process(target = replicas[i].start)
		p.start()
		processes.append(p)

	time.sleep(3)
	for i in range(kill_till):
		time.sleep(2)
		replicas[i].commit_suicide()