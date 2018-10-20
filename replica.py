import socket
import time
import threading
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


class Replica:
	
	def __init__(self, id, config):
		self.id = id
		self.socket = socket.socket()
		self.socket.bind(config[id])
		self.socket_list = []
		self.receive_list = []
		t = threading.Thread(target = self.new_connection)
		t.start()
		self.config = config
		self.state = 0
		self.view = 0
		self.current_leader = -1
		self.approve = 0
		self.proposed_value = ''

		self.to_propose = ''
		self.largest_pid_proposed = -1

		self.to_dicide = dict()
		self.decide = ''

	def connect(self):
		for server in self.config:
			s = socket.socket()
			s.connect(server)
			self.socket_list.append(s)
		
	def new_connection(self):
		self.socket.listen(5)
		while True:
			s, addr = self.socket.accept()
			t = threading.Thread(target = self.receive, args = (s,))
			t.start()
			self.receive_list.append(t)

	def receive(self, s):
		while True:
			msg = complete_recv(s)
			if msg != None:
				if msg[0] == LEADER_APPROVE:
					print("receive approve")

					if (len(msg.split()) == 3):
						if int(msg.split()[1]) > self.largest_pid_proposed:
							self.largest_pid_proposed = int(msg.split()[1])
							self.to_propose = msg.split()[2]

					self.approve += 1
					print(self.approve)
					if self.approve > len(self.config) / 2 and self.state == 1:
						print("send propose")
						self.state = 2
						if self.to_propose == '':
							self.to_propose = 'new'
						for ss in self.socket_list:
							complete_send(ss, PROPOSE + ' ' + str(self.id) + ' ' + self.to_propose)


				elif msg[0] == LEADER_REQ:
					print("receive request")
					if int(msg[1:]) > self.current_leader:
						k = int(msg[1:])
						complete_send(self.socket_list[k], LEADER_APPROVE + ' ' + str(self.current_leader) + ' ' + self.proposed_value)
						self.current_leader = k

				elif msg[0] == PROPOSE:
					print("receive propose")

					p = msg.split()
					print(p[1] + "  " + str(self.current_leader))
					if int(p[1]) >= self.current_leader:
						for ss in self.socket_list:
							complete_send(ss, ACCEPT + p[2])

				elif msg[0] == ACCEPT:
					print("receive accept")
					m = msg[1:]
					if m in self.to_dicide:
						self.to_dicide[m] += 1
					else:
						self.to_dicide[m] = 1
					if self.to_dicide[m] > len(self.config):
						self.decide = m
						print(m)


	def run(self):
		if self.id == self.view and self.state == 0:
			self.state = 1
			print("send request")
			for s in self.socket_list:
				complete_send(s, LEADER_REQ + str(self.id))

if __name__ == '__main__':
	k = list()
	 
	config = (('127.0.0.1', 12345), ('127.0.0.1', 12566), ('127.0.0.1', 12134))
	for i in range(3):
		k.append(Replica(i, config))
		print(i)
	for i in range(3):
		k[i].connect()
	for i in range(3):
		k[i].run()
