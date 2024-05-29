import atexit
import ctypes
import io
import os
import shlex
import signal
import socket
import subprocess
import sys
import tcp_info
import time


LIBC = ctypes.CDLL("libc.so.6")

DEFAULT_INTERFACE='lo'

CLONE_NEWNET = 0x40000000
original_net_ns = open("/proc/self/ns/net", 'rb')
if True:
    r = LIBC.unshare(CLONE_NEWNET)
    if r != 0:
        print("[!] Are you root? Need unshare() syscall.")
        sys.exit(-1)
    LIBC.setns(original_net_ns.fileno(), CLONE_NEWNET)

def new_ns(interface=DEFAULT_INTERFACE):
    r = LIBC.unshare(CLONE_NEWNET)
    if r != 0:
        print("[!] Are you root? Need unshare() syscall.")
        sys.exit(-1)
    os.system("ip link set {interface} up")

def restore_ns():
    LIBC.setns(original_net_ns.fileno(), CLONE_NEWNET)


def do_iptables(action, sport, dport, extra, interface=DEFAULT_INTERFACE):
    if sport:
        sport = '--sport %d' % (sport,)
        dport = ''
    else:
        sport = ''
        dport = '--dport %d' % (dport,)
    os.system(f"iptables -{action} INPUT -i {interface} -p tcp {sport} {dport} {extra} -j DROP")

def drop_start(sport=None, dport=None, extra='', interface=DEFAULT_INTERFACE):
    do_iptables('I', sport, dport, extra, interface)

def drop_stop(sport=None, dport=None, extra='', interface=DEFAULT_INTERFACE):
    do_iptables('D', sport, dport, extra, interface)

tcpdump_bin = os.popen('which tcpdump').read().strip()
ss_bin = os.popen('which ss').read().strip()

def tcpdump_start(port, interface=DEFAULT_INTERFACE):
    p = subprocess.Popen(shlex.split(f'{tcpdump_bin} -B 16384 --packet-buffered -n -ttttt -i {interface} port {port}'))
    time.sleep(1)
    def close():
        p.send_signal(signal.SIGINT)
        p.wait()
    p.close = close
    atexit.register(close)
    return p

def ss(port):
    print(os.popen('%s -t -n -o -a dport = :%s or sport = :%s' % (ss_bin, port, port)).read())

def check_buffer(c):
    ti = tcp_info.from_socket(c)
    print("delivered, acked", ti.tcpi_bytes_acked-1)
    print("in-flight:", ti.tcpi_bytes_sent - ti.tcpi_bytes_retrans- ti.tcpi_bytes_acked+1)
    print("in queue, not in flight:", ti.tcpi_notsent_bytes)

def socket_info(c):
    ti = tcp_info.from_socket(c)
    acked = ti.tcpi_bytes_acked-1
    in_flight = ti.tcpi_bytes_sent - ti.tcpi_bytes_retrans- ti.tcpi_bytes_acked+1
    notsent = ti.tcpi_notsent_bytes
    return acked, in_flight, notsent
