#!/usr/bin/env python3

from subprocess import Popen, PIPE
import re
from thread_decorator import thread
import rpyc
from rpyc.utils.server import ThreadedServer
from queue import Queue

def run(*cmd):
    proc = Popen(cmd, universal_newlines=True, stdout=PIPE)
    stdout, stderr = proc.communicate()
    return stdout

class _Service(rpyc.Service):
    def dump(self, slot):
        incoming.put(slot)
        

@thread
def _server():
    # Using an instance of Service causes every connection to get the same
    # object
    server = ThreadedServer(_Service, port=8888)
    # This blocks, hence the thread
    server.start()

def _get_ips():
    net_dump = run('sudo', 'ifconfig')
    # Generator comprehension to allow lazy evaluation of intermediate results,
    # strip all leading and trailing whitespace from each line
    lines = (line.strip() for line in net_dump.splitlines())
    # Information is on a line starting with inet (There are two of these, one
    # is the one we want, the other is from the loopback interface, it is
    # distinguisable because it contains 127.0.0.1). Fields are seperated by
    # whitespace
    inet = [line.split()[1:] for line in lines if line.startswith('inet') and not '127.0.0.1' in line]
    # inet should only have one entry
    if len(inet) != 1:
        # TODO: Should be an exception so the control loop can catch it, is a
        # print statement so we can see it
        print('Expected 1 IP, got {} ({})'.format(len(inet), '|'.join(inet)))
        # TODO: Blocking for the above print, remove later
        while True:
            pass
    # Convert to dict by spliting on :, ip is under addr, Broadcast is under Bcast
    addresses = dict(map(lambda x: x.split(':'), inet[0]))
    slave_ip = addresses['addr']
    bcast = addresses['Bcast']

    # ping the broardcast address, seems to force arp cache repopulation
    run('sudo', 'ping', '-c', '1', '-b', bcast)
    # Read the arp cache
    ips_raw = run('sudo', 'arp', '-a').splitlines()
    # Should only get one line out as there is only one other computer on the
    # network
    if len(ips_raw) != 1:
        # TODO: Should be an exception so the control loop can catch it, is a
        # print statement so we can see it
        print('Expected 1 IP, got {} ({})'.format(len(inet), '|'.join(inet)))
        # TODO: Blocking for the above print, remove later
        while True:
            pass
    # Assuming the line is what we expect the ip should be in brackets
    match = re.match(r'^.*\((.*)\).*$', ips_raw[0])
    if match:
        # If the match was successful, pull out the ip
        controller_ip = match.group(1)
        return slave_ip, controller_ip
    else:
        # Or die
        # TODO: Should be an exception so the control loop can catch it, is a
        # print statement so we can see it
        print('Unexpected string format: {}'.format(ips_raw))
        # TODO: Blocking for the above print, remove later
        while True:
            pass

# Start a server
incoming = Queue()
_server()
_slave_ip, _controller_ip = _get_ips()

# Attempt a connection to the controller's server and get the remote object
while True:
    try:
        _conn = rpyc.connect(_controller_ip, 8889)
    except ConnectionRefusedError:
        pass
    else:
        break
controller = _conn.root
# Send it our ip
controller.send_ip(_slave_ip)
