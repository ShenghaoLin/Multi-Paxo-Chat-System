import socket
import time
import threading
import sys
from multiprocessing import Process
from replica_utils import *


class Replica:
	
	def __init__(self, id, config, p = 0):
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
		self.msg_queue = list()
		self.time_stamp = 0
		self.last_decide_time = 0
		self.p = p
		self.to_execute = 0
		self.slot_to_propose = 0

		filename = "Replica" + str(self.id) + ".log"
		with open(filename, 'w') as f:
			f.write('')
		f.close()

		self.msg_proposed = set()
		self.received = set()

	def connect(self):
		for server in self.config:
			s = socket.socket()
			s.connect(server)
			t = threading.Thread(target = self.notificate, args = (s, server,))
			t.start()
			self.socket_list.append((s, server))

	def notificate(self, s, server):
		while True:
			complete_send(s, server, NOTIFICATION + str(self.id), p = self.p)
			time.sleep(0.5)
		
	def new_connection(self):
		self.socket.listen()
		while True:
			s, addr = self.socket.accept()
			t = threading.Thread(target = self.receive, args = (s,))
			t.start()
			self.receive_list.append((s, addr))
			# print('new connection: ' + str(self.id))

	def receive(self, s):
		while True:

			# self.lock.acquire()
			msg = complete_recv(s)
			# self.lock.release()

			if msg != '':

				if msg[0] == NOTIFICATION:
					if int(msg[1:]) == self.view:
						self.time_stamp = time.time()

				elif msg[0] == MESSAGE:
					m = msg[1:]
					hash_code = hash_it(m)
					if (hash_code not in self.received) and (hash_code not in self.msg_proposed):
						
						self.msg_queue.append(m)
						self.received.add(hash_code)

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
							to_send +=  ' ' + str(slot) + ' ' + \
							str(self.proposed_pairs[slot][0]) + ' ' + self.proposed_pairs[slot][1]

						complete_send(self.socket_list[k][0], self.socket_list[k][1], to_send, p = self.p)

						self.current_leader = k
						self.view = k
					self.lock.release()

				elif msg[0] == PROPOSE:
					print(str(self.id) + " receive propose")

					p = msg.split()

					if int(p[1]) >= self.current_leader:
						self.proposed_pairs[int(p[2])] = (int(p[1]), p[3])
						if (p[3] != '[[NULL[['):
							hash_code = hash_it(p[3])
							self.received.add(hash_code)
							self.msg_proposed.add(hash_code)
						if p[3] in self.msg_queue:
							self.msg_queue.remove(p[3])
						for ss in self.socket_list:
							self.lock.acquire()
							complete_send(ss[0], ss[1], ACCEPT + ' ' + p[2] + ' ' + p[3], p = self.p)
							self.lock.release()

				elif msg[0] == ACCEPT:
					m = msg.split()
					if (m[2] != '[[NULL[['):
						self.msg_proposed.add(hash_it(m[2]))

					if (self.id == 1):
						print('111111 received ' + m[2])

					self.lock.acquire()

					if int(m[1]) not in self.to_dicide:
						self.to_dicide[int(m[1])] = dict()

					if m[2] in self.to_dicide[int(m[1])]:
						self.to_dicide[int(m[1])][m[2]] += 1
					else:
						self.to_dicide[int(m[1])][m[2]] = 1

					print(str(self.id) + " receive accept: " + msg[1:].replace('-+-', ' ').replace('~`', ' '))

					self.lock.release()

	def start(self):
		t = threading.Thread(target = self.new_connection)
		t.start()
		self.last_decide_time = time.time()
		self.run()

	def run(self):
		self.connect()
		self.time_stamp = time.time()
		t = threading.Thread(target = self.timeout_check)
		t.start()
		while True:
			flag = False
			
			self.check_decision()
			self.execute()
			
			time.sleep(0.1)

			if time.time() - self.last_decide_time > 30:
				self.socket.close()
				print('No new deciesions made recently, disconnect ' + str(self.id))
				break

	def check_decision(self):
		for slot in self.to_dicide:
			for m in self.to_dicide[slot]:
				if self.to_dicide[slot][m] > len(self.config) / 2 and (slot not in self.decided):
					self.decided.add(slot) 
					self.decide[slot] = m
					print(str(self.id) + " decided: " + m.replace('-+-', ' ').replace('~`', ' ') + ' at slot ' + str(slot))
					if slot in self.proposed_pairs:
						del(self.proposed_pairs[slot])
				self.last_decide_time = time.time()
				
				# if slot == 2 and self.id == 0:
				# 	print('fuuuuuu')
				# 	sys.exit()
				break

	def execute(self):
		if self.to_execute in self.decided:

			for ss in self.receive_list:
				complete_send(ss[0], ss[1], REPLY + self.decide[self.to_execute])
			filename = "Replica" + str(self.id) + ".log"
			with open(filename, 'a') as f:
				f.write(str(self.to_execute) + ' ' + self.decide[self.to_execute].replace('-+-', ' ').replace('~~', ' ') + '\n')
			f.close()

			self.to_execute += 1
			
			
	def timeout_check(self):
		while True:
			self.lock.acquire()
			if time.time() - self.time_stamp >= 1.5 and self.id != self.view:
				self.view += 1
				self.time_stamp = time.time()
			self.lock.release()

			if self.id == self.view and self.state == 0:
				self.state = 1
				print(str(self.id) + " send request")

				for ss in self.socket_list:
					self.lock.acquire()
					complete_send(ss[0], ss[1], LEADER_REQ + str(self.id), p = self.p)
					self.lock.release()

			if self.state == 2:
				while self.slot_to_propose in self.decided:
					self.slot_to_propose += 1

				# if self.slot_to_propose == 1 and self.id == 0:
				# 	self.slot_to_propose += 1

				if self.slot_to_propose in self.to_propose:
					print(str(self.id) + ' send propose by prev ' + self.to_propose[i][1].replace('-+-', ' ').replace('~`', ' '))
					for ss in self.socket_list:
						complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + self.to_propose[i][1], p = self.p)
				else:

					if (len(self.to_propose) > 0 and self.slot_to_propose < max([x for x in self.to_propose])) \
					or (len(self.decided) > 0 and self.slot_to_propose < max(self.decided)):
						print(str(self.id) + ' send propose ' + '[[NULL[[')
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + '[[NULL[[', p = self.p)
				
					elif len(self.msg_queue) > 0:
						
						while (len(self.msg_queue) > 0) and (hash_it(self.msg_queue[0]) in self.msg_proposed):
							self.msg_queue.pop(0)

						if len(self.msg_queue) == 0:
							continue

						to_propose_s = self.msg_queue.pop(0)

						print(str(self.id) + ' send propose by myself ' + to_propose_s.replace('-+-', ' ').replace('~`', ' '))
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + to_propose_s, p = self.p)
				

			time.sleep(0.2)

if __name__ == '__main__':
	config = get_config('servers.config')
	replicas = list()
	processes = list()

	for i in range(len(config)):
		replicas.append(Replica(i, config))

	for i in range(len(config)):
		p = Process(target = replicas[i].start)
		p.start()
		processes.append(p)

	# time.sleep(2)
	# processes[0].terminate()
	# time.sleep(2)
	# processes[1].terminate()

	t = threading.Timer(120.0, kill_all, args = (processes,))
	t.start()
