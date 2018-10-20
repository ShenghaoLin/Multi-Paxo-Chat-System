import socket               # Import socket module
import select
from requests import get




s = socket.socket()         # Create a socket object


host = '10.0.0.172'



print(host)


port = 52345                # Reserve a port for your service.

s.connect((host, port))
while True:
	read, write, error = select.select([s], [], [], 0)
	if s in read:
		a = s.recv(1024)
		if len(a) > 0:
			print(a)
s.close()                     # Close the socket when done