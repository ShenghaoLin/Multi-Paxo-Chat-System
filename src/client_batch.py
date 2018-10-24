from client import *

if __name__ == '__main__':
	config = '../data/servers.config'
	data_path = '../data/'
	message = ['messages.txt','messages2.txt','messages3.txt']

	clients = list()
	processes = list()
	
	for i in range(3):
		c = client(str(i), config, data_path + message[i], 0, p = 0)
		clients.append(c)


	for c in clients:
		p = Process(target = c.run)
		p.start()
		processes.append(p)

	# t = threading.Timer(30.0, kill_all, args = (processes,))
	# t.start()