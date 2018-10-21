import socket


NOTIFICATION = 'N'
LEADER_REQ = 'L'
LEADER_APPROVE = 'D'
PROPOSE = 'P'
ACCEPT = 'A'
SIZE_LEN = 10

def complete_send(s, server, msg):

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