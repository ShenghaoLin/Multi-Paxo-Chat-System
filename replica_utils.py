import socket


NOTIFICATION = 'N'
LEADER_REQ = 'L'
LEADER_APPROVE = 'D'
PROPOSE = 'P'
ACCEPT = 'A'
SIZE_LEN = 10

def complete_send(s, msg):
	msg = (('0' * SIZE_LEN + str(len(msg)))[-SIZE_LEN:] + str(msg)).encode()
	bytes_sent = 0
	while bytes_sent < len(msg) :
		sent = s.send(msg[bytes_sent:])
		if sent == 0:
			break
		bytes_sent += sent

def complete_recv(s):
	size = ''
	while len(size) < SIZE_LEN:
		data = s.recv(SIZE_LEN - len(size)).decode()
		if not data:
			return None
		size += data

	size = int(size)

	msg = ''
	while len(msg) < size:
		data = s.recv(size - len(msg)).decode()
		if not data:
			break
		msg += data

	return msg