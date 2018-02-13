#!/usr/bin/env python3

from subprocess import Popen, PIPE
import re

udp_line = re.compile(r'^udp')
ip_address = re.compile(r'^\d+(\.\d+){3}')

proc = Popen('netstat', universal_newlines=True, stdout=PIPE)
stdout, stderr = proc.communicate()
print(tuple(sorted(set(map(lambda x: x.split(':')[0], map(lambda x: tuple(filter(lambda y: ip_address.match(y), x))[0], map(lambda x: x.split(), filter(lambda x: udp_line.match(x), stdout.splitlines()))))))))
