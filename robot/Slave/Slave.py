#!/usr/bin/env python3

from subprocess import Popen, PIPE
import re
from thread_decorator import thread
import rpyc
from rpyc.utils.server import ThreadedServer
from queue import Queue
import socket

def run(*cmd):
    proc = Popen(cmd, universal_newlines=True, stdout=PIPE)
    stdout, stderr = proc.communicate()
    return stdout

# Start a server
incoming = Queue()

class _Service(rpyc.Service):
    def exposed_reverse(self, string):
        controller.reverse_responce(string[::-1])

@thread
def _server():
    # Using an instance of Service causes every connection to get the same
    # object
    server = ThreadedServer(_Service, port=8888)
    # This blocks, hence the thread
    server.start()
_server()

_stdout = run('sudo', 'ifconfig')
# Generator comprehension to allow lazy evaluation of intermediate results,
# strip all leading and trailing whitespace from each line
_lines = (line.strip() for line in _stdout.splitlines())
# Information is on a line starting with inet. Fields are seperated by whitespace
_addresses = (line.split()[1:] for line in _lines if line.startswith('inet'))
_addresses_dicts = []
for _address in _addresses:
    _addresses_dicts.append(dict(map(lambda x: x.split(':'), _address)))

_res = [x for x in _addresses_dicts if x['addr'] != '127.0.0.1'][0] # TODO: Do better
# Localhost will be included in the previous result, remove it and any duplicate entries
#_ips = {line for line in _ips_unfiltered if line != '127.0.0.1'}

_slave_ip = _res['addr']
_bcast = _res['Bcast']

run('sudo', 'ping',' -c', '3', '-b', _bcast)
_stdout = run('sudo', 'arp', '-a')
_controller_ip = re.match(r'^.*\((.*)\).*$', _stdout).group(1)

# Attempt a connection to the controller's server TODO: What happens when there
# is no server yet
_conn = rpyc.connect(_controller_ip, 8889)
# Get the remote object
controller = _conn.root
# Send it our ip
controller.send_ip(_slave_ip)
