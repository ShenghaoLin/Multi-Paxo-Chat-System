import socket               # Import socket module
import select
from requests import get




s = socket.socket()         # Create a socket object
host = socket.gethostbyname(socket.gethostname()) # Get local machine name


host = get('https://api.ipify.org').text



print(host)


port = 12345                # Reserve a port for your service.

s.connect((host, port))
while True:
	read, write, error = select.select([s], [], [], 0)
	if s in read:
		a = s.recv(1024)
		if len(a) > 0:
			print(a)
s.close()                     # Close the socket when done