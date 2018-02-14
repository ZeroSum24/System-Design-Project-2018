#!/usr/bin/env python3

from subprocess import Popen, PIPE
import re
from thread_decorator import thread
import rpyc
from rpyc.utils.server import ThreadedServer
from queue import Queue
import socket

# Start a server
incoming = Queue()

class _Service(rpyc.Service):
    def exposed_reverse(string):
        controller.reverse_responce(reversed(string))

@thread
def _server():
    # Using an instance of Service causes every connection to get the same
    # object
    server = ThreadedServer(_Service, port=8888)
    # This blocks, hence the thread
    server.start()
_server()

_proc = Popen('netstat', universal_newlines=True, stdout=PIPE)
_stdout, _stderr = _proc.communicate()

# Inter-brick network shows up as udp in netstat output. The IP is the 5th field
# split by whitespace (split with no arguments splits splits on \s+). The port
# is irrelevent so it gets chopped off. Set comprehension because order is 
# irrelevent and duplicates should be removed
_ips = {(line.split()[4]).split(':')[0] for line in _stdout.splitlines() if line.startswith('udp')}

if len(_ips) != 1:
    raise ValueError('Expected 1 IP, got {} ({})'.format(len(_ips), ','.join(_ips)))

# Sets aren't indexable
_controller_ip = tuple(_ips)[0]

# Discover the ip of the current device
# Running ifconfig like this requires the brick's sudoers file to be modified
# to have %sudo   ALL=(ALL:ALL) NOPASSWD:ALL in it
_proc = Popen(['sudo', 'ifconfig'], universal_newlines=True, stdout=PIPE)
_stdout, _stderr = _proc.communicate()

# Generator comprehension to allow lazy evaluation of intermediate results,
# strip all leading and trailing whitespace from each line
_lines = (line.strip() for line in _stdout.splitlines())
# Relavent data is the second field split on whitespace and the part after
# the : on a line that starts with inet
_ips_unfiltered = ((line.split()[1]).split(':')[1] for line in _lines if line.startswith('inet'))
# Localhost will be included in the previous result, remove it and any duplicate entries
_ips = {line for line in _ips_unfiltered if line != '127.0.0.1'}

if len(_ips) != 1:
    raise ValueError('Expected 1 IP, got {} ({})'.format(len(_ips), ','.join(_ips)))

_slave_ip = tuple(_ips)[0]

# Attempt a connection to the controllers server TODO: What happens when there
# is no server yet
_conn = rpyc.connect(controller_ip, 8889)
# Get the remote object
controller = _conn.remote
# Send it our ip
controller.send_ip(slave_ip)
