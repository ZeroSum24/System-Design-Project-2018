#!/usr/bin/env python3

import socket
import requests
from sys import argv

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 8888))
payload = (('key1', 'value1'), ('key1', 'value2'))
r = requests.post('http://127.0.0.1:5000', data=payload)
print(r.text)

s.send(r)
