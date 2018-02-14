#!/usr/bin/env python3

from subprocess import Popen, PIPE
import re

udp_line = re.compile(r'^udp')
ip_address = re.compile(r'^\d+(\.\d+){3}')

proc = Popen('netstat', universal_newlines=True, stdout=PIPE)
stdout, stderr = proc.communicate()

# Inter-brick network shows up as udp in netstat output. The IP is the 5th field
# split by whitespace (split with no arguments splits splits on \s+). The port
# is irrelevent so it gets chopped off
ips = {(line.split()[4]).split(':')[0] for line in stdout.splitlines() if udp_line.match(line)}

if len(ips) != 1:
    raise ValueError('Expected 1 IP, got {} ({})'.format(len(ips), ','.join(ips)))

# Sets aren't indexable
controller_ip = tuple(ips)[0]
