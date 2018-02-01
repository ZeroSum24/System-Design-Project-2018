#!/usr/bin/env python3

import rpyc

with rpyc.connect('192.168.17.129', 8888) as c:
    remote = c.root
    remote.echo('Hi')
