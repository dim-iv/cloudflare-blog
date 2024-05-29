import io
import os
import select
import socket
import time
import utils
import sys

utils.new_ns()

interface = "lo"
address = '127.0.0.1'
port = 1

if len(sys.argv) > 1:
  interface = sys.argv[1]

if len(sys.argv) >= 2:
  address = sys.argv[2]

if len(sys.argv) >= 2:
  port = sys.argv[2]

tcpdump = utils.tcpdump_start(port, interface)
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

t0 = time.time()

utils.drop_start(dport=port, interface=interface)

if False:
   c.setsockopt(socket.IPPROTO_TCP, socket.TCP_USER_TIMEOUT, 5*1000)


# speedup
#    os.system('sysctl net.ipv4.tcp_syn_retries=4')

if False:
    c.setblocking(False)
    try:
        c.connect((address, port))
    except io.BlockingIOError:
        pass
    c.setblocking(True)

    utils.ss(port)
    time.sleep(1)
    utils.ss(port)
    time.sleep(3)
    utils.ss(port)

    poll = select.poll()
    poll.register(c, select.POLLOUT)
    poll.poll()
    utils.ss(port)
else:
    try:
        c.connect((address, port))
    except Exception as e:
        print(e)
e = c.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
print("[ ] SO_ERROR = %s" % (e,))

t1 = time.time()
print("[ ] connect took %fs" % (t1-t0,))
