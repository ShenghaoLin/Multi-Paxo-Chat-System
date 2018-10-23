import socket
import random

NOTIFICATION = 'N'
LEADER_REQ = 'L'
LEADER_APPROVE = 'D'
PROPOSE = 'P'
ACCEPT = 'A'
MESSAGE = 'M'
REPLY = 'R'
SIZE_LEN = 8



def complete_send(s, server, msg, p = 0.0):

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
			except:
				return

def complete_recv(s):
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
	config = list()
	with open(s, 'r') as f:
		content = f.readlines()
		for line in content:
			config.append((line.split()[1], int(line.split()[2])))
	f.close()
	return config


def kill_all(processes):
	for p in processes:
		p.terminate()

def hash_it(s):
	return int(s.split('~`')[0]) * 2000 + int(s.split('~`')[1])