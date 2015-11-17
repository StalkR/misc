#!/usr/bin/python
# Binary ptyshell sets up a listening shell on a pty.
# Connect with: socat FILE:`tty`,raw,echo=0 TCP:localhost:1234

import os
import pty
import socket
import select
import subprocess
import sys


def main():
  if len(sys.argv) < 3:
    print 'Usage: %s <listen address> <listen port>' % sys.argv[0]
    raise SystemExit(1)

  host = sys.argv[1]
  port = int(sys.argv[2])

  serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  serv.bind((host, port))
  serv.listen(5)

  while True:
    client, addr = serv.accept()
    print 'New connection: %s' % repr(addr)

    if not os.fork(): # child
      Handle(client)
      client.close()
      os._exit(0)

    client.close()


def Handle(client):
  print '[%i] Spawn bash' % os.getpid()
  master, slave = pty.openpty()
  p = subprocess.Popen(['/bin/bash'], stdin=slave, stdout=slave, stderr=slave, close_fds=True, preexec_fn=os.setsid)
  print '[%i] Starting relay' % os.getpid()
  Relay(client, master, stop_func=lambda: p.poll() != None)
  print '[%i] Done' % os.getpid()


def Relay(a, b, bufsize=4096, debug=True, stop_func=None):
  """Relay (proxy) between two sockets/fds, return when closed."""

  def transfer_one_way(r, a, b, way):
    if a in r:
      if type(a) is int:
        buf = os.read(a, bufsize)
      else:
        buf = a.recv(bufsize)
      if buf:
        if way:
          print '%s: %s' % (way, repr(buf))
        if type(b) is int:
          os.write(b, buf)
        else:
          b.send(buf)
      else:
        a.close()
        a = None
    return a, b

  while a != None and b != None and not (stop_func and stop_func()):
    r, w, e = select.select([a, b], [], [], 1)
    a, b = transfer_one_way(r, a, b, 'A -> B' if debug else None)
    b, a = transfer_one_way(r, b, a, 'B -> A' if debug else None)

if __name__ == '__main__':
  main()
