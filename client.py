import socket      # Import socket module
import select
from requests import get
from replica_utils import *
import threading
import sys
import time
from multiprocessing import Process


class client():

	def __init__(self, name, config, message, mode, p = 0):
		self.p = p
		self.name = name
		self.config = config
		self.message = message
		self.view = 0
		self.mode = mode
		self.chat_hist_code = list()
		self.chat_history = ''
		self.lock = threading.Lock()
		self.sending = False
		self.server_config = get_config(config)
		self.console_input = list()
		self.msg_sent = 0


	def receive(self, s):
		while True:

			msg = complete_recv(s)

			if msg != '':
				if msg[0] == REPLY:
					m = msg[1:]
					if m == NULL_ACTION:
						continue

					hash_code = m.split('~`')[0] + '-' + m.split('~`')[1] 

					self.lock.acquire()
					if hash_code not in self.chat_hist_code:
						real_msg = m.split('~`')[2].replace('-+-', ' ')
						self.chat_hist_code.append(hash_code)
						self.chat_history += (hash_code + ': ' + real_msg + '\n')
						
						if m.split('~`')[0] == self.name:
							self.sending = False

						if self.mode == 1:
							if m.split('~`')[0] != self.name:
								print(m.split('~`')[0] + ': ' + real_msg)

						with open('chat_history' + self.name + '.log', 'w') as f:
							f.write(self.chat_history)
						f.close()
					self.lock.release()

	def run(self):
		sockets = list()
		for server in self.server_config:
			s = socket.socket()
			try:
				s.connect(server)
			except:
				print("Not connected")
			sockets.append((s, server))
			t = threading.Thread(target = self.receive, args = (s, ))
			t.start()

		if self.mode == 0:
			self.run_batch_mode(sockets)
		else:
			self.run_cmdl_mode(sockets)


	def run_cmdl_mode(self, sockets):
		reading_thread = threading.Thread(target = self.read_input)
		reading_thread.daemon = True
		reading_thread.start()
		while True:
			if len(self.console_input) > 0:
				self.send_msg(self.console_input.pop(0), sockets)

	def read_input(self):
		while True:
			text = sys.stdin.readline()[:-1]
			self.console_input.append(text)

	def run_batch_mode(self, sockets):

		with open(self.message, 'r') as f:
			msgs = f.readlines()

		for i in range(len(msgs)):
			self.send_msg(msgs[i], sockets)

		print(self.name + " done")
		while True:
			continue

	def send_msg(self, m, sockets):
		self.sending = True
		while self.sending:
			# print(self.view)
			s = sockets[self.view]
			complete_send(s[0], s[1], MESSAGE + self.name + '~`' + str(self.msg_sent) + '~`' + m.replace(' ', '-+-'), p = self.p)
			for tt in range(10):

				if self.sending == False:
					break;
				complete_send(s[0], s[1], MESSAGE + self.name + '~`' + str(self.msg_sent) + '~`' + m.replace(' ', '-+-'), p = self.p)
				time.sleep(0.05)

			if self.sending:
				self.view = (self.view + 1) % len(self.server_config)
		self.msg_sent += 1

if __name__ == '__main__':
	config = 'servers.config'
	
	c = client(sys.argv[1], config, '', 1)
	c.run()
