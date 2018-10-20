import socket               # Import socket module


s = socket.socket()         # Create a socket object
host = ''
print(host)
port = 52345                # Reserve a port for your service.


s.bind((host, port))        # Bind to the port

s.listen(5)                 # Now wait for client connection.
while True:
   c, addr = s.accept()     # Establish connection with client.
   print('Got connection from', addr)
   c.send(b'Thank you for connecting')
   c.close()                # Close the connection