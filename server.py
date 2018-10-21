import socket               # Import socket module
from requests import get
import selectors
import sys,errno
import types

###multi connection server

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            reply = 'Thank you received.'
            print('reply', repr(data.outb), 'to', data.addr)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


            
sel = selectors.DefaultSelector()
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
print(host)
port = 52345                # Reserve a port for your service.
s.bind((host, port))        # Bind to the port
s.listen()                 # Now wait for client connection.'
print('listening on', (host, port))
s.setblocking(False)
sel.register(s, selectors.EVENT_READ, data=None)

while True:
    events = sel.select(timeout=None)
    for key, mask in events:
        if key.data is None:
            accept_wrapper(key.fileobj)
        else:
            service_connection(key, mask)


#c, addr = s.accept()     # Establish connection with client.
#c.send(b'Thank you for connecting')
#print('Got connection from', addr)
#c.send(b'Thank you for connecting')


#while True: 
#   read, write, error = select.select([s], [], [], 0)
#   if error:
#      print(error)
#   if read:
#      reply = s.recv(4096)
#      print(reply.decode())
#      m = 'recv'
#      c.sendto(m.encode())
#c.close()                # Close the connection

#time = 5
#while time:
#   try:
#      data = c.recv(1024)
#      print(data)
#      time = time - 1
#      print(time)
#   try:
#      c.send(b'once more')

#c.close()  # Close the connection
