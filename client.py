import socket               # Import socket module
import select
from requests import get
import time

class client():

        def __init__(self, id, config, message):
                self.id = id
                self.config = config
                self.message = message
                self.view = 0
                       
        def run(self):
                file = open(self.config,'r')
                replicas=[]
                ports=[]
                hosts=[]
                n=0
                for line in file:
                        #print(line)
                        a = line.split()
                        replicas.append(a[0])
                        #print(replicas)
                        ports.append(int(a[1]))
                        hosts.append(a[2])
                        n = n +1
        
                allmessage = open(self.message,'r')
                m = "heyheyheyheyheyhey"
                for m in allmessage:

                       #for i in range(self.view,n+self.view):
                        while True:
                                s = socket.socket()
                                host = socket.gethostname()                             
                #                host = socket.gethostname()
                                port = 52345
                                #host = hosts[self.view]
                                #port = ports[self.view]
                                self.view = (self.view + 1) % n

                                s.connect((host, port))
                                #s.sendto(m.encode(),(host,port))
                                #s.sendto(m.encode(),(host, port))
                                s.send(m.encode())
                                s.setblocking(0)
                                #timeout 5 sec
                                print('send message ')
                                read, write, error = select.select([s], [], [], 10)
                                if error:
                                      print(error)
                                if read:
                                        reply = s.recv(4096)
                                        print(reply)
                                        s.close()
                                        break

if __name__ == '__main__':
        config = 'config.txt'
        message = 'messages.txt'
        c=client(1,config,message)
        c.run()
