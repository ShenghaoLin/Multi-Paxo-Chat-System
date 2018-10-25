#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Script used to run clients in batch mode.
	
	Clients will automatically read and send messges in our pre-defined
	message set.

	Message loss probability can be given as a command line argument.

	The command to use is "python client_batch.py [$message_loss_probability]"


	@author: Yangming Ke, Shenghao Lin
"""

from client import *

if __name__ == '__main__':
	config = '../data/servers.config'
	data_path = '../data/'
	message = ['messages.txt','messages2.txt','messages3.txt']

	clients = list()
	processes = list()

	prob = 0
	if len(sys.argv) > 1:
		prob = float(sys.argv[1])
	
	for i in range(3):
		c = Client(str(i), config, data_path + message[i], 0, p = prob)
		clients.append(c)


	# Clients are still running in different processes
	for c in clients:
		p = Process(target = c.run)
		p.start()
		processes.append(p)