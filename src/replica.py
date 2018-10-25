#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This module defines the replica class, and executing this module will
	automatically run a replica in cmdl mode.

	To run this program, always including the first argument as the id of
	this replica. If a message loss is needed, use the optional second argument.

	@author: Shenghao Lin, Yangming Ke
"""

import socket
import time
import threading
import sys
from multiprocessing import Process
from replica_utils import *


class Replica:
	""" This class implements the Replica object.
		Thre are 2 modes: cmdl line mode and batch mode.
		In cmdl line mode, a replica is started, and controlled by cmdl commands
		In batch mode, replicas are started from one py file, but in different processes

	Parameters:
		id: a number as given in the config file, representing this replica
		config: a list of config tuples
		mode: 0 fir batch mode, 1 for cmdl mode
		p: message loss probability
	"""
	
	def __init__(self, id, config, mode, p = 0):
		self.mode = mode
		self.id = id
		self.already_proposed = set()
		self.socket = socket.socket()
		self.socket.bind(config[id])
		self.lock = threading.Lock()
		self.socket_list = []
		self.receive_list = []
		self.config = config
		self.state = 0 # 0 means not a leader; 1 means send out requests; 2 means leader
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
		self.suicide_after = -1
		self.suicide = False
		self.decided_until = -1

		# initialize sockets connecting to other replicas
		for server in self.config:
			s = socket.socket()
			s.settimeout(1)
			self.socket_list.append((s, server))

		# in cmdl mode, listen from the beginning
		if self.mode == 1:
			self.socket.listen()
			t = threading.Thread(target = self.new_connection)
			t.daemon = True
			t.start()

		# refresh the log file
		filename = "../log/Replica" + str(self.id) + ".log"
		with open(filename, 'w') as f:
			f.write('')
		f.close()


	def connect(self):
		""" Function trying to connect all pre-defined sockets to other replicas
		"""

		for s, server in self.socket_list:
			try:
				s.connect(server)
			except:
				print(str(self.id) + " already connected with " + str(server))
			t = threading.Thread(target = self.notificate, args = (s, server,))
			t.daemon = True
			t.start()


	def notificate(self, s, server):
		""" Thread function usded to generate heartbeat to other replicas to
			notify them that this replica is still alive.

		Arguments:
			s: socket connecting to the target replica
			server: the server address and host of the target replica
		"""

		while True:

			if self.suicide:
				return

			complete_send(s, server, NOTIFICATION + str(self.id), p = self.p)
			time.sleep(0.1)
		
	def commit_suicide(self):
		""" Function called to kill this replica
		"""

		self.suicide = True

	def new_connection(self):
		""" Thread function used to keep track of all new connections to this replica
			and build new threads to receive messages from them.
		"""
		
		while True:

			if self.suicide:
				return
			
			s, addr = self.socket.accept()

			# Receive msgs from new connections
			print(str(self.id) + " has a new connection " + str(addr))
			t = threading.Thread(target = self.receive, args = (s,))
			t.start()
			self.receive_list.append((s, addr))
			# print('new connection: ' + str(self.id))

	def receive(self, s):
		""" Thread function to handle all receiving messages, which is the 
			most import function in this class.

		Arguments:
			s: socket of receiving data
		"""

		while True:

			msg = complete_recv(s)

			# Empty message check
			if msg != '': 

				# Handler of notification messages. Only valid when it is coming from a replica that is thought to be the leader
				if msg[0] == NOTIFICATION:
					if int(msg[1:]) == self.view:
						self.time_stamp = time.time()

				# Handler of messges coming from clients. Only take care of it when the replica is a leader
				elif msg[0] == MESSAGE:

					# Check leader status
					if self.state != 2:
						continue

					# If it is not a message has been decided, add it to our queue
					m = msg[1:]
					if m not in [self.decide[x] for x in self.decide] and m not in self.msg_queue:
						self.msg_queue.append(m)

				# Handler of approve messages for leadership from the acceptors
				elif msg[0] == LEADER_APPROVE:
										
					# If the replica is not waiting for an approve
					if self.state != 1:
						continue

					# Maintain a set of supporting replicas
					self.lock.acquire()
					print(str(self.id) + ' receive approve from ' + msg[1:].split()[0] + ' ' + str(len(self.approve)))
					self.approve.add(int(msg[1:].split()[0]))
					self.lock.release()

					# Retrieve values that have been proposed from this message, and store them into our dictionary
					# slot_to_propose, where the key is the slot number and the value is a tuple of (prev_leader_pid, value)
					proposed = msg[1:].split()[1:]
					self.slot_to_propose = min(self.slot_to_propose, int(proposed[0]) + 1)

					for i in range(int((len(proposed) - 1) / 3)):

						if int(proposed[3 * i + 1]) in self.to_propose:
							if int(proposed[3 * i + 2]) > self.to_propose[int(proposed[3 * i + 1])][0]:
								self.to_propose[int(proposed[3 * i + 1])] = (int(proposed[3 * i + 2]), proposed[3 * i + 3])
						else:
							self.to_propose[int(proposed[3 * i + 1])] = (int(proposed[3 * i + 2]), proposed[3 * i + 3])
						

					# Check if the replica gets the majority of replicas
					self.lock.acquire()
					if len(self.approve) > len(self.config) / 2 and self.state == 1:
						self.state = 2
						print(str(self.id) + ' becomes leader')
					self.lock.release()

				# Handler of leadership request
				elif msg[0] == LEADER_REQ:

					print(str(self.id) + " receive request from " + msg[1:])
					
					# If this message is from a larger number than the current leader (in RR rule), show loyalty to it.
					# The equal case is used when message loss happens: multiple approve messages may be needed 
					# to elect a leader
					if int(msg[1:]) >= self.current_leader or (self.current_leader == len(self.config) - 1):

						k = int(msg[1:])

						# Wrap all information in to this approve message (Approve + id + tombstone of last decision + proposed pairs)
						to_send = LEADER_APPROVE + str(self.id) + ' ' + str(self.decided_until)

						# If the was a leader, it is not anymore
						if self.state == 2 and self.id != k:
							self.state = 0

						for slot in self.proposed_pairs:
							to_send +=  ' ' + str(slot) + ' ' + \
							str(self.proposed_pairs[slot][0]) + ' ' + self.proposed_pairs[slot][1]

						complete_send(self.socket_list[k][0], self.socket_list[k][1], to_send, p = self.p)
						print(str(self.id) + ' send approve to ' + str(k))

						# Update current leader and view
						self.current_leader = k
						self.view = k

				# Handler of propose messages from the leader
				elif msg[0] == PROPOSE:

					print(str(self.id) + " receive propose")
					p = msg.split()

					# Check if this message is from a current or newer leader
					if int(p[1]) >= self.current_leader or int(p[1]) == len(self.config) - 1:

						# Change state if this message makes the replica notice that it is no longer a leader
						if self.state == 2 and (int(p[1]) > self.id or (int(p[1]) == len(self.config) - 1 and int(p[1]) != self.id)):
							self.state = 0

						self.proposed_pairs[int(p[2])] = (int(p[1]), p[3])

						if p[3] in self.msg_queue:
							self.msg_queue.remove(p[3])

						# Wrap and send the message to all replicas (Accept + slot number + msg + id)
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], ACCEPT + ' ' + p[2] + ' ' + p[3] + ' ' + str(self.id), p = self.p)

				# Handler of accept messages from acceptors
				elif msg[0] == ACCEPT:

					m = msg.split()
					
					self.lock.acquire()

					# to_dicide_list is a dict with key as slot number, and value as a dictionary with key as replica id, 
					# value as the value proposed by that replica
					# to_dicide is a dict with key as slot bumber, and value as a dictionary with key as value proposed,
					# and value as the number of proposals
					# Keep track of these two because in message loss cases, multiple same accepts can be sent, and we 
					# do not want to double count those
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
		""" Thread function used to keep track of keyboard input (special commmands in the cmdl mode)
		"""

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
		""" The main function run in the process of this replica
		"""

		self.last_decide_time = time.time()

		# Start here if the replica is defined in batch mode
		if self.mode == 0:
			self.socket.listen()
			t = threading.Thread(target = self.new_connection)
			t.daemon = True
			t.start()

		# Instructions for cmdl mode. Waiting for start command
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

		# Connect to other replicas
		self.connect()

		# Start to commicate
		self.run()


	def run(self):
		""" This function runs a infinite loop, always checking possible decide to do and executions
		"""
		
		# Timeout check, which is in charge of view change and sending out proposes
		self.time_stamp = time.time()
		t = threading.Thread(target = self.timeout_check)
		t.daemon = True
		t.start()


		while True:
			
			# Can kill the process from inside
			if self.suicide:
				print("killed")
				sys.exit()
			
			self.check_decision()
			self.execute()
			
			time.sleep(0.1)


	def check_decision(self):
		""" Check if there is any available decisions to make in any slot
		"""

		# Iterate through all possible decisions
		for slot in self.to_dicide:
			for m in self.to_dicide[slot]:
				if self.to_dicide[slot][m] > len(self.config) / 2 and (slot not in self.decided):
					self.decided.add(slot) 
					self.decide[slot] = m
					print(str(self.id) + " decided: " + m.replace('-+-', ' ').replace('~`', ' ') + ' at slot ' + str(slot))
					tmp = self.decided_until
					while tmp + 1 in self.decided:
						tmp += 1
					self.decided_until = tmp

				self.last_decide_time = time.time()

				# Special case when a skip slot command is given and successfully executed, notify the user to kill it some time
				if slot == self.suicide_after:
					print("I skipped a slot, remember to kill me later.")
					self.suicide_after = -1
				
				break


	def execute(self):
		""" Check if there is any available executions to do in the next slot
		"""

		# to_execute is a pointer always points to the next target to execute
		if self.to_execute in self.decided:

			for ss in self.receive_list:
				complete_send(ss[0], ss[1], REPLY + str(self.current_leader) + ' ' + self.decide[self.to_execute])

			# write log
			filename = "../log/Replica" + str(self.id) + ".log"
			with open(filename, 'a') as f:
				f.write(str(self.to_execute) + ' ' + self.decide[self.to_execute].replace('-+-', ' ').replace('~~', ' ') + '\n')
			f.close()

			self.to_execute += 1


	def repeat_propose(self, slot, msg):
		""" Called in message loss case, so that we can make sure at least one decision is made, which is in the leader, so that
			the clients may not be block forever. When the loss is not very heavy, a leader switch can repair other replicas

		Arguments:
			slot: the slot we want to get a decision
			msg: the message to send again, if needed (a decision is not made in given time)
		"""

		# Do it only when you are still the leader
		while self.state == 2 and slot not in self.decided:
			time.sleep(3)
			if slot not in self.decided:
				for ss in self.socket_list:
					complete_send(ss[0], ss[1], msg, p = self.p)
			
			
	def timeout_check(self):
		""" Thread function of time out check. Taking charge of view change and proposal generation, automatic request generation.
		"""

		while True:

			# View change if nothing is heard from the leader for more than 1.5s
			if time.time() - self.time_stamp >= 1.5 and self.id != self.view:
				self.lock.acquire()
				self.view += 1
				self.lock.release()
				self.time_stamp = time.time()


			# New leader request
			if self.id == self.view and self.state == 0:
				self.approve = set()
				self.slot_to_propose = self.decided_until + 1
				self.state = 1
				self.send_request = time.time()
				print(str(self.id) + " send request")

				for ss in self.socket_list:
					complete_send(ss[0], ss[1], LEADER_REQ + str(self.id), p = self.p)

			# When mesaage can be lost, resend the request if not enough votes are gotten.
			if self.state == 1 and time.time() - self.send_request > 5:

				self.send_request = time.time()
				for ss in self.socket_list:
					complete_send(ss[0], ss[1], LEADER_REQ + str(self.id), p = self.p)
				print(str(self.id) + " send request")

			# Send out proposes based on slot, and given proposed value from acceptors
			if self.state == 2:

				# Special case of skip slot
				if self.skip_slot:
					self.slot_to_propose += 1
					self.suicide_after = self.slot_to_propose
					self.skip_slot = False

				# When there are proposed values from the acceptors in this slot, use this value
				if self.slot_to_propose in self.to_propose:
					print(str(self.id) + ' send propose by prev ' + self.to_propose[self.slot_to_propose][1].replace('-+-', ' ').replace('~`', ' '))
					
					self.already_proposed.add(self.to_propose[self.slot_to_propose][1])
					for ss in self.socket_list:
						complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + self.to_propose[self.slot_to_propose][1], p = self.p)
					
					t = threading.Thread(target = self.repeat_propose, args = (self.slot_to_propose, PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + self.to_propose[self.slot_to_propose][1], ))
					t.daemon = True
					t.start()

					self.slot_to_propose += 1

				else:

					# If the slot was skipped, cover it by a NULL
					if (len(self.to_propose) > 0 and self.slot_to_propose < max([x for x in self.to_propose])) \
					or (len(self.decided) > 0 and self.slot_to_propose < max(self.decided)):
						print(str(self.id) + ' send propose ' + NULL_ACTION)
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + NULL_ACTION, p = self.p)
						t = threading.Thread(target = self.repeat_propose, args = (self.slot_to_propose, PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + NULL_ACTION, ))
						t.daemon = True
						t.start()
						self.slot_to_propose += 1

					# If there is a message in the queue, propose this message				
					elif len(self.msg_queue) > 0:
						
						while (len(self.msg_queue) > 0) and \
						(self.msg_queue[0] in [self.decide[x] for x in self.decide] or self.msg_queue[0] in self.already_proposed):
							self.msg_queue.pop(0)

						if len(self.msg_queue) == 0:
							continue

						to_propose_s = self.msg_queue.pop(0)

						print(str(self.id) + ' send propose by myself ' + to_propose_s.replace('-+-', ' ').replace('~`', ' '))
						self.already_proposed.add(to_propose_s)
						
						for ss in self.socket_list:
							complete_send(ss[0], ss[1], PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + to_propose_s, p = self.p)

						t = threading.Thread(target = self.repeat_propose, args = (self.slot_to_propose, PROPOSE + ' ' + str(self.id) + ' ' + str(self.slot_to_propose) + ' ' + to_propose_s, ))
						t.daemon = True
						t.start()

						self.slot_to_propose += 1

			time.sleep(0.2)

if __name__ == '__main__':
	config = get_config('../data/servers.config')
	prob = 0
	if (len(sys.argv) > 2):
		prob = float(sys.argv[2])
	r = Replica(int(sys.argv[1]), config, 1, p = prob)
	r.start()