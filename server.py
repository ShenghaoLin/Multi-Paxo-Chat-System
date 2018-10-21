import socket               # Import socket module
from requests import get
import select

s = socket.socket()         # Create a socket object
#host = socket.gethostbyname(socket.gethostname())
#host = get('https://api.ipify.org').text
host = socket.gethostname()
print(host)
port = 52345                # Reserve a port for your service.


s.bind((host, port))        # Bind to the port

s.listen(5)                 # Now wait for client connection.
while True:
   c, addr = s.accept()     # Establish connection with client.
   print('Got connection from', addr)
 #  c.send(b'Thank you for connecting')

   read, write, error = select.select([s], [], [], 0)
   if read:
      reply = s.recv(4096)
      if len(a) > 0:
         print(reply.decode())
         c.send('received')

c.close()                # Close the connection
