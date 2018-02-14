#!/usr/bin/env python3

from thread_decorator import thread
import rpyc
from rpyc.utils.server import ThreadedServer
from queue import Queue

# Start a server

# Thread safe queue for communicating between the service thread and the main
# thread
incoming = Queue()

class _Service(rpyc.Service):
    def exposed_send_ip(ip):
        # When we get an ip put it on the queue
        incomming.put(ip)
    def exposed_reverse_responce(string):
        incoming.put(string)
        
@thread
def _server():
    # Using an instance of Service causes every connection to get the same
    # object
    server = ThreadedServer(_Service, port=8889)
    # This blocks, hence the thread
    server.start()
_server()

# Block until the slave sends an ip
_slave_ip = incoming.get()

# Open a connection back to the slave (This should never fail as the slave
# creates it's server before sending the ip)
_conn = rpyc.connect(slave_ip, 8888)
slave = _conn.remote
