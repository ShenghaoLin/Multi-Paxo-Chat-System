from replica import *

if __name__ == '__main__':
	config = get_config('../data/servers.config')
	replicas = list()
	processes = list()

	for i in range(len(config)):
		replicas.append(Replica(i, config, 0))

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
