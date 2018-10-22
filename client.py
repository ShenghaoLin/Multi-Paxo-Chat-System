import socket      # Import socket module
import select
from requests import get
from replica_utils import *
import threading
import time
from multiprocessing import Process


class client():

	def __init__(self, name, config, message, mode):
		self.name = name
		self.config = config
		self.message = message
		self.view = 0
		self.mode = mode
		self.chat_hist_code = list()
		self.chat_history = ''
		self.lock = threading.Lock()
		self.sending = False


	def receive(self, s):
		while True:

			msg = complete_recv(s)

			if msg != '':
				# print("reply")
				if msg[0] == REPLY:
					m = msg[1:]
					hash_code = m.split('~`')[0] + '-' + m.split('~`')[1] 
					

					self.lock.acquire()
					if hash_code not in self.chat_hist_code:
						real_msg = m.split('~`')[2].replace('-+-', ' ')
						self.chat_hist_code.append(hash_code)
						self.chat_history += (hash_code + ': ' + real_msg + '\n')
						# if m.split('~`')[0] == self.name:
						#       print(real_msg)
						# else:
						#       print(m.split('~`')[0] + ': ' + real_msg)
						if m.split('~`')[0] == self.name:
							self.sending = False

						with open('chat_history' + self.name + '.log', 'w') as f:
							f.write(self.chat_history)
						f.close()
					self.lock.release()


	def run(self):

		server_config = get_config(self.config)
		sockets = list()
		for server in server_config:
			s = socket.socket()
			s.connect(server)
			sockets.append((s, server))
			t = threading.Thread(target = self.receive, args = (s, ))
			t.start()

		with open(self.message, 'r') as f:
			msgs = f.readlines()


		for i in range(len(msgs)):

			self.sending = True

			while self.sending:
				print(self.view)
				s = sockets[self.view]
				complete_send(s[0], s[1], MESSAGE + self.name + '~`' + str(i) + '~`' + msgs[i].replace(' ', '-+-'))
				for tt in range(20):
					if self.sending == False:
						break;
					time.sleep(0.2)

				if self.sending:
					self.view += 1
					print(self.view)
					if self.view == len(self.config):
						self.view = 0
		print(self.name + " done")

		while True:
			continue

if __name__ == '__main__':
	config = 'servers.config'
	message = ['messages.txt','messages2.txt','messages3.txt']

	clients = list()
	processes = list()
	
	for i in range(3):
		c = client(str(i), config, message[i], 0)
		clients.append(c)


	for c in clients:
		p = Process(target = c.run)
		p.start()
		processes.append(p)

	t = threading.Timer(30.0, kill_all, args = (processes,))
	t.start()
