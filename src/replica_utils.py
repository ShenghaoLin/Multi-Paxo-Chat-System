#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A module containing some useful definitions and functions used
	in this project

	@author: Shenghao Lin, Yangming Ke
"""

import socket
import random

# messge prefix
NOTIFICATION = 'N'
LEADER_REQ = 'L'
LEADER_APPROVE = 'D'
PROPOSE = 'P'
ACCEPT = 'A'
MESSAGE = 'M'
REPLY = 'R'

# Null execution
NULL_ACTION = '\{NULL\}'

# length of the message length prefix
SIZE_LEN = 8



def complete_send(s, server, msg, p = 0.0):
	""" Wrapper function for a raw send.
		Add the length of the message to the beginning of a message.
		Try to reconnect if the socket is not connected

	Parameters:
		s: socket
		server: (address, host) tuple, used for reconnection
		msg: raw message to send
		p: message loss probability
	"""

	if p > 0:
		if random.uniform(0, 1) < p:
			return

	msg = (('0' * SIZE_LEN + str(len(msg)))[-SIZE_LEN:] + str(msg)).encode()
	bytes_sent = 0
	try:
		s.sendall(msg)
	except:
		if (len(server) != 0):
			try:
				s.connect(server)
				s.sendall(msg)
				print(msg)
			except:
				return


def complete_recv(s):
	""" Wrapper function for a raw receive.
		Read the the length prefix first, 
		and then receive the whole message accordingly

	Parameters:
		s: socket

	Return:
		messge received (raw)
	"""

	size = ''
	while len(size) < SIZE_LEN:
		try:
			data = s.recv(SIZE_LEN - len(size)).decode()
			if not data:
				return ''
			size += data
		except:
			return ''

	size = int(size)

	msg = ''
	while len(msg) < size:
		try:
			data = s.recv(size - len(msg)).decode()
			if not data:
				break
			msg += data
		except:
			return ''

	return msg


def get_config(s):
	""" Get configurations from the config file

	Parameters:
		s: the path of config file

	Return:
		A list of tuples of (address, host)
	"""

	config = list()
	with open(s, 'r') as f:
		content = f.readlines()
		for line in content:
			config.append((line.split()[1], int(line.split()[2])))
	f.close()
	return config


def hash_it(s):
	""" Hash a message based on its prefix

	Parameters:
		s: message

	Return:
		Hash value
	"""

	name = s.split('~`')[0]

	for c in name:
		k = (k * 128 + ord(c)) % 1000000007

	return k * 200000 + int(s.split('~`')[1])

