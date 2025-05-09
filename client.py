#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Time    : 2017/4/11
# @Author  : Twi1ight
import re
import socket
import requests
import sys
import urlparse
import urllib

from settings import route_to_init, route_to_transport, route_to_shutdown, md5digest
from settings import headers, cookie_param_name, data_fragment_size, encrypt, decrypt


def send_and_recv(buf):
    data = encrypt(buf)
    print ("send data length"), len(data)
    cookies = {cookie_param_name: urllib.quote(data)}
    response = http_request('GET', urlparse.urljoin(server_url, route_to_transport), cookies=cookies)
    ciphers = re.findall('"(.*?)"', response)
    ciphertext = ''.join(ciphers)
    digest = md5digest(ciphertext)
    if response[-len(digest):] != digest:
        print ("recv data digest error!")
        return ''
    print ("recv data length"), len(ciphertext)
    return decrypt(ciphertext)


def http_request(method, url, **kwargs):
    try:
        ret = requests.request(method, url, headers=headers, timeout=5,
                               proxies=http_proxy, verify=False, **kwargs).content
    except Exception as e:
        print ("url request exception"), str(e)
        ret = ''
    return ret


def argparse():
    if len(sys.argv) != 4:
        print ("usage: python client.py listen-port server-url http-proxy")
        print ("e.g. python client.py 2222 http://12.34.56.78:8089/ http://proxy.yourcorp.com:8080")
        print ("then ssh root@localhost -p 2222 will ssh to 12.34.56.78")
        sys.exit()
    return int(sys.argv[1]), sys.argv[2], sys.argv[3]


if __name__ == '__main__':
    listen_port, server_url, proxy_url = argparse()
    # listen_port, server_url, proxy_url = 2222, 'http://11.22.33.44:8089/', 'http://127.0.0.1:3128'
    http_proxy = {'http': proxy_url}
    socket = socket.socket()
    socket.bind(("127.0.0.1", listen_port))
    socket.listen(1)
    shutdown = lambda: 'client exited, %s' % http_request('GET', urlparse.urljoin(server_url, route_to_shutdown))
    while True:
        local, _ = socket.accept()
        print ("client accepted,"), http_request('GET', urlparse.urljoin(server_url, route_to_init))
        while True:
            try:
                buf = local.recv(data_fragment_size)
            except:
                print (shutdown())
                break
            if len(buf) == 0:
                print (shutdown())
                break
            resp = send_and_recv(buf)
            local.sendall(resp)
