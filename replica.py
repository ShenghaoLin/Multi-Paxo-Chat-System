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
		self.to_propose = dict()
		self.proposed_pairs = dict()
		self.to_dicide = dict()
		self.decide = dict()
		self.decided = set()
		self.time_stamp = 0

	def connect(self):
		for server in self.config:
			s = socket.socket()
			s.connect(server)
			t = threading.Thread(target = self.notificate, args = (s, server,))
			t.start()
			self.socket_list.append((s, server))

	def notificate(self, s, server):
		while True:
			# print(str(self.id) + " sent nofification")
			complete_send(s, server, NOTIFICATION + str(self.id))
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
					
					if self.state != 1:
						continue

					self.lock.acquire()
					self.approve += 1
					self.lock.release()

					proposed = msg.split()
					for i in range(int((len(proposed) - 1) / 3)):

						self.lock.acquire()
						if int(proposed[3 * i + 1]) in self.decided:
							continue
						if int(proposed[3 * i + 1]) in self.to_propose:
							if int(proposed[3 * i + 2]) > self.to_propose[int(proposed[3 * i + 1])][0]:
								self.to_propose[int(proposed[3 * i + 1])] = (int(proposed[3 * i + 2]), proposed[3 * i + 3])
						self.lock.release()


					self.lock.acquire()
					
					if self.approve > len(self.config) / 2 and self.state == 1:
						self.state = 2
					self.lock.release()


				elif msg[0] == LEADER_REQ:
					print(str(self.id) + " receive request")
					self.lock.acquire()

					if int(msg[1:]) > self.current_leader:
						k = int(msg[1:])
						to_send = LEADER_APPROVE

						for slot in self.proposed_pairs:
							to_send +=  ' ' + slot + ' ' + \
							self.proposed_pairs[slot][0] + ' ' + self.proposed_pairs[slot][1]

						complete_send(self.socket_list[k][0], self.socket_list[k][1], to_send)
						self.current_leader = k
						self.view = k
					self.lock.release()

				elif msg[0] == PROPOSE:
					print(str(self.id) + " receive propose")

					p = msg.split()
					if int(p[1]) >= self.current_leader:
						self.proposed_pairs[int(p[2])] = (int(p[1]), p[3])
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], ACCEPT + ' ' + p[2] + ' ' + p[3])

				elif msg[0] == ACCEPT:
					m = msg.split()
					self.lock.acquire()

					if int(m[1]) not in self.to_dicide:
						self.to_dicide[int(m[1])] = dict()

					if m[2] in self.to_dicide[int(m[1])]:
						self.to_dicide[int(m[1])][m[2]] += 1
					else:
						self.to_dicide[int(m[1])][m[2]] = 1

					print(str(self.id) + " receive accept: " + msg[1:])

					self.lock.release()

	def start(self):
		t = threading.Thread(target = self.new_connection)
		t.start()
		self.run()

	def run(self):
		self.connect()
		self.time_stamp = time.time()
		t = threading.Thread(target = self.timeout_check)
		t.start()
		while True:
			flag = False
			self.lock.acquire()
			for slot in self.to_dicide:
				for m in self.to_dicide[slot]:
					if self.to_dicide[slot][m] > len(self.config) / 2 and (slot not in self.decided):
						self.decided.add(slot) 
						self.decide[slot] = m
						print(str(self.id) + " decided: " + m + ' at slot ' + str(slot))
						if slot in self.proposed_pairs:
							del(self.proposed_pairs[slot])
			self.lock.release()
			if len(self.decided) > 3:
				break

	def timeout_check(self):
		while True:

			# print(str(self.id) + " alive at " + str(int(time.time())) + ' ' + str(self.view))

			self.lock.acquire()
			if time.time() - self.time_stamp >= 3.0 and self.id != self.view:
				self.view += 1
			self.lock.release()

			if self.id == self.view and self.state == 0:
				self.state = 1
				print(str(self.id) + " send request")
				for ss in self.socket_list:
					complete_send(ss[0], ss[1], LEADER_REQ + str(self.id))

			if self.state == 2:
				i = 0
				while i in self.decided:
					i += 1


				if i in self.to_propose:
					print(str(self.id) + ' send propose ' + self.to_propose[i][1])
					for ss in self.socket_list:
						complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(i) + ' ' + self.to_propose[i][1])
				else:
					to_propose_s = str(int(time.time() * 1000) % 100)
					print(str(self.id) + ' send propose ' + to_propose_s)
					for ss in self.socket_list:
						complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(i) + ' ' + to_propose_s)

			time.sleep(0.5)


if __name__ == '__main__':

	k = list()
	 
	config = (('127.0.0.1', 12345), ('127.0.0.1', 12566), ('127.0.0.1', 12134), ('127.0.0.1', 12555), ('127.0.0.1', 12145))
	for i in range(5):
		k.append(Replica(i, config))
	pp = list()
	for i in range(5):
		p = Process(target = k[i].start)
		p.start()
		pp.append(p)
	# time.sleep(1.7)
	# pp[0].terminate()
	
