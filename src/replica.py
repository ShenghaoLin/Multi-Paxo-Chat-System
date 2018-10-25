import socket
import time
import threading
import sys
from multiprocessing import Process
from replica_utils import *

class Replica:
	
	def __init__(self, id, config, mode, p = 0):
		self.mode = mode
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
		self.approve = set()
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
		self.ready_to_connect = False
		self.console_input = list()
		self.skip_slot = False
		self.to_dicide_list = dict()
		self.send_request = 0
		self.met = set()
		self.suicide_after = -1
		self.suicide = False
		self.decided_until = -1

		for server in self.config:
			s = socket.socket()
			s.settimeout(1)
			self.socket_list.append((s, server))

		if self.mode == 1:
			self.socket.listen()
			t = threading.Thread(target = self.new_connection)
			t.daemon = True
			t.start()

		filename = "../log/Replica" + str(self.id) + ".log"
		with open(filename, 'w') as f:
			f.write('')
		f.close()

		self.msg_proposed = set()
		self.received = set()

	def connect(self):
		# print("start to connect")
		for s, server in self.socket_list:
			try:
				s.connect(server)
			except:
				print(str(self.id) + " already connected with " + str(server))
			t = threading.Thread(target = self.notificate, args = (s, server,))
			t.daemon = True
			t.start()
		# print("connect finish")


	def notificate(self, s, server):
		while True:

			if self.suicide:
				return

			complete_send(s, server, NOTIFICATION + str(self.id), p = self.p)
			time.sleep(0.1)
		
	def new_connection(self):
		while True:

			if self.suicide:
				return
			
			s, addr = self.socket.accept()
			print(str(self.id) + " has a new connection " + str(addr))
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
						if int(msg[1:]) not in self.met:
							# print("receive from " + msg[1:])
							try:
								self.socket_list[int(msg[1:])][0].connect(self.socket_list[int(msg[1:])][1])
							except:
								print(str(self.id) + " already connected with " + msg[1:])
						self.met.add(int(msg[1:]))


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
					self.approve.add(int(msg[1:].split()[0]))
					self.lock.release()



					proposed = msg[1:].split()[1:]
					self.slot_to_propose = min(self.slot_to_propose, int(proposed[0]) + 1)

					for i in range(int((len(proposed) - 1) / 3)):

						self.lock.acquire()
						if int(proposed[3 * i + 1]) in self.decided:
							continue
						if int(proposed[3 * i + 1]) in self.to_propose:
							if int(proposed[3 * i + 2]) > self.to_propose[int(proposed[3 * i + 1])][0]:
								self.to_propose[int(proposed[3 * i + 1])] = (int(proposed[3 * i + 2]), proposed[3 * i + 3])
						self.lock.release()


					self.lock.acquire()
					
					if len(self.approve) > len(self.config) / 2 and self.state == 1:
						self.state = 2
						print(str(self.id) + ' becomes leader')
					self.lock.release()


				elif msg[0] == LEADER_REQ:
					print(str(self.id) + " receive request from " + msg[1:])
					self.lock.acquire()

					if int(msg[1:]) >= self.current_leader or (self.current_leader == len(self.config) - 1):
						k = int(msg[1:])
						to_send = LEADER_APPROVE + str(self.id) + ' ' + str(self.decided_until)
						if self.state == 2:
							self.state = 0

						for slot in self.proposed_pairs:
							to_send +=  ' ' + str(slot) + ' ' + \
							str(self.proposed_pairs[slot][0]) + ' ' + self.proposed_pairs[slot][1]

						complete_send(self.socket_list[k][0], self.socket_list[k][1], to_send, p = self.p)
						print('Approve sent')

						self.current_leader = k
						self.view = k
					self.lock.release()

				elif msg[0] == PROPOSE:
					print(str(self.id) + " receive propose")

					p = msg.split()

					if int(p[1]) >= self.current_leader or int(p[1]) == len(self.config) - 1:
						if self.state == 2 and (int(p[1]) > self.id or (int(p[1]) == len(self.config) - 1 and int(p[1]) != self.id)):
							self.state = 0
						self.proposed_pairs[int(p[2])] = (int(p[1]), p[3])
						if (p[3] != NULL_ACTION):
							hash_code = hash_it(p[3])
							self.received.add(hash_code)
							self.msg_proposed.add(hash_code)
						if p[3] in self.msg_queue:
							self.msg_queue.remove(p[3])
						for ss in self.socket_list:
							self.lock.acquire()
							complete_send(ss[0], ss[1], ACCEPT + ' ' + p[2] + ' ' + p[3] + ' ' + str(self.id), p = self.p)
							self.lock.release()

				elif msg[0] == ACCEPT:
					m = msg.split()
					if (m[2] != NULL_ACTION):
						self.msg_proposed.add(hash_it(m[2]))

					self.lock.acquire()

					if int(m[1]) not in self.to_dicide:
						self.to_dicide[int(m[1])] = dict()
						self.to_dicide_list[int(m[1])] = dict()

					if int(m[3]) not in self.to_dicide_list[int(m[1])]:
						self.to_dicide_list[int(m[1])][int(m[3])] = m[2]
						try:
							self.to_dicide[int(m[1])][m[2]] += 1
						except:
							self.to_dicide[int(m[1])][m[2]] = 1
					elif m[2] != self.to_dicide_list[int(m[1])][int(m[3])]:
						self.to_dicide[int(m[1])][self.to_dicide_list[int(m[1])][int(m[3])]] -= 1
						try:
							self.to_dicide[int(m[1])][m[2]] += 1
						except:
							self.to_dicide[int(m[1])][m[2]] = 1


					print(str(self.id) + " receive accept: " + msg[1:].replace('-+-', ' ').replace('~`', ' '))

					self.lock.release()

	def read_input(self):
		while True:
			
			text = sys.stdin.readline()[:-1].lower()
			if text == 'kill me':
				self.suicide = True
			if text == "skip slot":
				print("Going to skip the next slot")
				self.skip_slot = True
			if text == "start":
				self.ready_to_connect = True


	def start(self):
		self.last_decide_time = time.time()

		if self.mode == 0:
			self.socket.listen()
			t = threading.Thread(target = self.new_connection)
			t.daemon = True
			t.start()

		if self.mode != 0:
			print('Use "start" to start running, after you open all replicas')
			print('Use "kill me" to kill this process.')
			print('Use "skip slot" to skip a slot.')
			reading_thread = threading.Thread(target = self.read_input)
			reading_thread.daemon = True
			reading_thread.start()
		else:
			self.ready_to_connect = True

		while not self.ready_to_connect:
			continue

		self.connect()
		self.run()

	def run(self):
		
		self.time_stamp = time.time()
		t = threading.Thread(target = self.timeout_check)
		t.daemon = True
		t.start()
		while True:
			if self.suicide:
				print("killed")
				sys.exit()
			
			self.check_decision()
			self.execute()
			
			time.sleep(0.1)


	def check_decision(self):
		for slot in self.to_dicide:
			for m in self.to_dicide[slot]:
				if self.to_dicide[slot][m] > len(self.config) / 2 and (slot not in self.decided):
					self.decided.add(slot) 
					self.decide[slot] = m
					print(str(self.id) + " decided: " + m.replace('-+-', ' ').replace('~`', ' ') + ' at slot ' + str(slot))
					if slot in self.proposed_pairs:
						del(self.proposed_pairs[slot])
					tmp = self.decided_until
					while tmp + 1 in self.decided:
						tmp += 1
					self.decided_until = tmp

				self.last_decide_time = time.time()

				if slot == self.suicide_after:
					print("I skipped a slot, remember to kill me later.")
					# self.suicide = True
					self.suicide_after = -1
				
				break

	def execute(self):
		if self.to_execute in self.decided:

			for ss in self.receive_list:
				complete_send(ss[0], ss[1], REPLY + str(self.current_leader) + ' ' + self.decide[self.to_execute])
			filename = "../log/Replica" + str(self.id) + ".log"
			with open(filename, 'a') as f:
				f.write(str(self.to_execute) + ' ' + self.decide[self.to_execute].replace('-+-', ' ').replace('~~', ' ') + '\n')
			f.close()

			self.to_execute += 1

	def repeat_propose(self, slot, msg):
		while self.state == 2 and slot not in self.decided:
			time.sleep(3)
			if slot not in self.decided:
				for ss in self.socket_list:
					complete_send(ss[0], ss[1], msg, p = self.p)
			
			
	def timeout_check(self):
		while True:
			if self.suicide:
				return

			self.lock.acquire()
			if time.time() - self.time_stamp >= 1.5 and self.id != self.view:
				self.view += 1
				self.time_stamp = time.time()
			self.lock.release()

			if self.id == self.view and self.state == 0:
				self.approve = set()
				self.slot_to_propose = self.decided_until + 1
				self.state = 1
				self.send_request = time.time()
				print(str(self.id) + " send request")

				for ss in self.socket_list:
					self.lock.acquire()
					complete_send(ss[0], ss[1], LEADER_REQ + str(self.id), p = self.p)
					self.lock.release()

			if self.state == 1 and time.time() - self.send_request > 5:

				self.send_request = time.time()
				print(str(self.id) + " send request")

				for ss in self.socket_list:
					self.lock.acquire()
					complete_send(ss[0], ss[1], LEADER_REQ + str(self.id), p = self.p)
					self.lock.release()

			if self.state == 2:
				# while self.slot_to_propose in self.decided:
				# 	self.slot_to_propose += 1

				if self.skip_slot:
					self.slot_to_propose += 1
					self.suicide_after = self.slot_to_propose
					self.skip_slot = False

				if self.slot_to_propose in self.to_propose:
					print(str(self.id) + ' send propose by prev ' + self.to_propose[i][1].replace('-+-', ' ').replace('~`', ' '))
					for ss in self.socket_list:
						complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + self.to_propose[i][1], p = self.p)
						t = threading.Thread(target = self.repeat_propose, args = (self.slot_to_propose, PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + self.to_propose[i][1], ))
						t.daemon = True
						t.start()
					

					self.slot_to_propose += 1

				else:

					if (len(self.to_propose) > 0 and self.slot_to_propose < max([x for x in self.to_propose])) \
					or (len(self.decided) > 0 and self.slot_to_propose < max(self.decided)):
						print(str(self.id) + ' send propose ' + NULL_ACTION)
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + NULL_ACTION, p = self.p)
							t = threading.Thread(target = self.repeat_propose, args = (self.slot_to_propose, PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + NULL_ACTION, ))
							t.daemon = True
							t.start()
						self.slot_to_propose += 1


				
					elif len(self.msg_queue) > 0:
						
						while (len(self.msg_queue) > 0) and (hash_it(self.msg_queue[0]) in self.msg_proposed):
							self.msg_queue.pop(0)

						if len(self.msg_queue) == 0:
							continue

						to_propose_s = self.msg_queue.pop(0)

						print(str(self.id) + ' send propose by myself ' + to_propose_s.replace('-+-', ' ').replace('~`', ' '))
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + to_propose_s, p = self.p)
							
							t = threading.Thread(target = self.repeat_propose, args = (self.slot_to_propose, PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + to_propose_s, ))
							t.daemon = True
							t.start()

						self.slot_to_propose += 1
				


			time.sleep(0.2)

if __name__ == '__main__':
	config = get_config('../data/servers.config')
	r = Replica(int(sys.argv[1]), config, 1)
	r.start()