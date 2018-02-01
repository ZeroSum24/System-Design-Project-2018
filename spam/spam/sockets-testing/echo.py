#!/usr/bin/env python3

import socketserver
import sys

class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Get all the data, strip leading and trailing whitespace and decode
        data = self.request.recv(999999999).strip().decode()
        # Print it to stdout (Can do arbitary things at this point)
        print(data)

# Simple TCP Server, I think using the ThreadingMixIn allows it to accept several connections
class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Kill all threads with ^C
    daemon_threads = True
    # Faster address rebinding
    allow_reuse_address = True

    def __init__(self, address, handler):
        socketserver.TCPServer.__init__(self, address, handler)

if __name__ == '__main__':
    # Listen on localhost:8888
    server = Server(('localhost', 8888), EchoHandler)
    # Serve untill ^C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
