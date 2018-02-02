#!/usr/bin/env python3

import rpyc
from rpyc.utils.server import ThreadedServer

class EchoService(rpyc.Service):
    def on_connect(self):
        # Runs when something connects
        pass

    def on_disconnect(self):
        # Runs after a connection closes
        pass

    def exposed_echo(self, val):
        self.internal_echo(val)

    def internal_echo(self, val):
        print(val)

if __name__ == '__main__':
    server = ThreadedServer(EchoService, port=8888)
    server.start()
