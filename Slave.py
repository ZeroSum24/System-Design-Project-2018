#!/usr/bin/env python3

from subprocess import Popen, PIPE
import re
from thread_decorator import thread
import rpyc
from rpyc.utils.server import ThreadedServer

# Start a server
class _Service(rpyc.Service):
    pass

@thread
def _server():
    # Using an instance of Service causes every connection to get the same
    # object
    server = ThreadedServer(_Service(), port=8888)
    # This blocks, hence the thread
    server.start()
_server()

# Find both ips
_udp_line = re.compile(r'^udp')

_proc = Popen('netstat', universal_newlines=True, stdout=PIPE)
_stdout, _stderr = proc.communicate()

# Inter-brick network shows up as udp in netstat output. The IP is the 5th field
# split by whitespace (split with no arguments splits splits on \s+). The port
# is irrelevent so it gets chopped off
_ips = {(line.split()[4]).split(':')[0] for line in _stdout.splitlines() if _udp_line.match(line)}

if len(_ips) != 1:
    raise ValueError('Expected 1 IP, got {} ({})'.format(len(ips), ','.join(ips)))

# Sets aren't indexable
_controller_ip = tuple(ips)[0]

# TODO: Find ip of current device, ip command is available on the bricks
_slave_ip = '0.0.0.0'

# Attempt a connection to the controllers server TODO: What happens when there
# is no server yet
_conn = rpyc.connect(controller_ip, 8889)
# Get the remote object
controller = _conn.remote
# Send it our ip
controller.send_ip(slave_ip)
