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
		self.msg_queue = list()
		self.time_stamp = 0
		self.last_decide_time = 0

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
			# self.lock.acquire()
			complete_send(s, server, NOTIFICATION + str(self.id))
			# self.lock.release()
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
					self.msg_queue.append(m)

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
							self.lock.acquire()
							complete_send(ss[0], ss[1], ACCEPT + ' ' + p[2] + ' ' + p[3])
							self.lock.release()

				elif msg[0] == ACCEPT:
					m = msg.split()
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
			self.lock.acquire()
			for slot in self.to_dicide:
				for m in self.to_dicide[slot]:
					if self.to_dicide[slot][m] > len(self.config) / 2 and (slot not in self.decided):
						self.decided.add(slot) 
						self.decide[slot] = m
						print(str(self.id) + " decided: " + m.replace('-+-', ' ').replace('~`', ' ') + ' at slot ' + str(slot))
						if slot in self.proposed_pairs:
							del(self.proposed_pairs[slot])
					for ss in self.receive_list:
						complete_send(ss[0], ss[1], REPLY + m)
					self.last_decide_time = time.time()
					flag = True


			self.lock.release()

			if flag:
				filename = "Replica" + str(self.id) + ".log"
				d = list()
				with open(filename, 'w') as f:
					for slot in self.decide:
						d.append((slot, self.decide[slot].replace('-+-', ' ').replace('~~', ' ')))
					d.sort(key = lambda x : x[0])
					s = ''
					for tt in d:
						s += str(tt[0]) + ' ' + tt[1] + '\n'
					f.write(s)
				f.close()
			
			time.sleep(0.1)

			if time.time() - self.last_decide_time > 30:
				self.socket.close()
				print('No new deciesions made recently, disconnect ' + str(self.id))
				break
			
			
			
	def timeout_check(self):
		while True:

			# print(str(self.id) + " alive at " + str(int(time.time())) + ' ' + str(self.view))

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
					complete_send(ss[0], ss[1], LEADER_REQ + str(self.id))
					self.lock.release()

			if self.state == 2:
				i = 0
				while i in self.decided:
					i += 1

				self.lock.acquire()
				if i in self.to_propose:
					print(str(self.id) + ' send propose ' + self.to_propose[i][1].replace('-+-', ' ').replace('~`', ' '))
					for ss in self.socket_list:
						complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(i) + ' ' + self.to_propose[i][1])
				else:
					if len(self.msg_queue) > 0:
						to_propose_s = self.msg_queue.pop(0)
						print(str(self.id) + ' send propose ' + to_propose_s.replace('-+-', ' ').replace('~`', ' '))
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(i) + ' ' + to_propose_s)
				self.lock.release()

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
