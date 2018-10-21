import socket
import time
import threading
from multiprocessing import Process
from replica_utils import *

class Replica:
	
	def __init__(self, id, config):
		self.id = id
		self.socket = socket.socket()
		self.socket.bind(config[id])
		self.lock = threading.Lock()
		self.socket_list = []
		self.receive_list = []
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
		self.decided = False
		self.time_stamp = 0

	def connect(self):
		for server in self.config:
			s = socket.socket()
			while (s.connect(server)):
				continue
			t = threading.Thread(target = self.notificate, args = (s,))
			t.start()
			self.socket_list.append(s)

	def notificate(self, s):
		while True:
			# print("sent nofification")
			complete_send(s, NOTIFICATION + str(self.id))
			time.sleep(0.5)
		
	def new_connection(self):
		self.socket.listen(5)
		while True:
			s, addr = self.socket.accept()
			t = threading.Thread(target = self.receive, args = (s,))
			t.start()
			self.receive_list.append(t)
			# print('new connection: ' + str(self.id))

	def receive(self, s):
		while True:
			msg = complete_recv(s)
			if msg != None:
				if msg[0] == NOTIFICATION:
					if int(msg[1:]) == self.view:
						self.time_stamp = time.time()
				elif msg[0] == LEADER_APPROVE:
					print(str(self.id) + " receive approve")

					if (len(msg.split()) == 3):
						self.lock.acquire()
						if int(msg.split()[1]) > self.largest_pid_proposed:
							self.largest_pid_proposed = int(msg.split()[1])
							self.to_propose = msg.split()[2]
						self.lock.release()


					self.lock.acquire()
					self.approve += 1
					if self.approve > len(self.config) / 2 and self.state == 1:
						print(str(self.id) + " send propose")
						self.state = 2
						if self.to_propose == '':
							self.to_propose = 'new'
						for ss in self.socket_list:
							complete_send(ss, PROPOSE + ' ' + str(self.id) + ' ' + self.to_propose)
					self.lock.release()


				elif msg[0] == LEADER_REQ:
					print(str(self.id) + " receive request")
					self.lock.acquire()
					if int(msg[1:]) > self.current_leader:
						k = int(msg[1:])
						complete_send(self.socket_list[k], LEADER_APPROVE + ' ' + str(self.current_leader) + ' ' + self.proposed_value)
						self.current_leader = k
					self.lock.release()

				elif msg[0] == PROPOSE:
					print(str(self.id) + " receive propose")

					p = msg.split()
					print(p[1] + "  " + str(self.current_leader))
					if int(p[1]) >= self.current_leader:
						for ss in self.socket_list:
							complete_send(ss, ACCEPT + p[2])

				elif msg[0] == ACCEPT:
					print(str(self.id) + " receive accept")
					m = msg[1:]
					self.lock.acquire()
					if m in self.to_dicide:
						self.to_dicide[m] += 1
					else:
						self.to_dicide[m] = 1

					print(str(self.id) + " receive accept: " + str(self.to_dicide[m]) + " " + str(len(self.config) / 2))

					self.lock.release()


	def run(self):
		t = threading.Thread(target = self.new_connection)
		t.start()
		self.connect()
		self.time_stamp = time.time()
		t = threading.Thread(target = self.timeout_check)
		t.start()
		while True:
			flag = False
			self.lock.acquire()
			for m in self.to_dicide:
				if self.to_dicide[m] > len(self.config) / 2 and self.decided == False:
					self.decided = True
					self.decide = m
					print(str(self.id) + " decided: " + m)
					flag = True
					break
			self.lock.release()
			if flag:
				break

	def timeout_check(self):
		while True:
			self.lock.acquire()
			if time.time() - self.time_stamp >= 3.0 and self.id != self.view:
				self.view += 1
			self.lock.release()

			if self.id == self.view and self.state == 0:
				self.state = 1
				print(str(self.id) + " send request")
				for s in self.socket_list:
					complete_send(s, LEADER_REQ + str(self.id))

			time.sleep(0.5)


if __name__ == '__main__':

	k = list()
	 
	config = (('127.0.0.1', 12345), ('127.0.0.1', 12566), ('127.0.0.1', 12134), ('127.0.0.1', 12555), ('127.0.0.1', 12145))
	for i in range(5):
		k.append(Replica(i, config))
	pp = list()
	for i in range(5):
		p = Process(target = k[i].run)
		p.start()
		pp.append(p)
	pp[0].terminate()
	
