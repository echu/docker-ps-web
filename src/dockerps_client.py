import gevent.socket, gevent.os
import json
from contextlib import contextmanager

import termios
import sys
import tty

class NoDataException(Exception):
    pass

def cleanup(greenlet):
    if greenlet is not None:
        greenlet.kill()

class Client(object):
    def __init__(self, host):
        ip, port = host.split(':')
        sock = gevent.socket.socket()
        sock.connect((ip,port))
        self.socket = sock

    def close(self):
        self.socket.close()

    def containers(self):
        self.socket.sendall('containers:')
        # here's to hoping container list doesn't exceed 1024...
        header_end = "\r\n\r\n"
        data_buffer = self.socket.recv(1024)
        while header_end not in data_buffer:
            data_buffer += self.socket.recv(1024)
        return json.loads(data_buffer.strip())

    def shell(self, node_id, forward_socket=None):
        self.socket.sendall('shell:{0}'.format(node_id))
        header_end = "\r\n\r\n"

        rstdin = sys.stdin.fileno()
        rstdout = sys.stdout.fileno()

        def write_loop():
            while True:
                try:
                    data = self.socket.recv(128)
                    if header_end in data:
                        raise NoDataException("Received end header.")

                    if data:
                        if forward_socket is None:
                            gevent.os.tp_write(rstdout, data)
                        else:
                            forward_socket.send(data)
                    else:
                        raise NoDataException("No data from docker source.")
                except Exception as e:
                    print e
                    cleanup(read_greenlet)
                    break

        def read_loop():
            while True:
                try:
                    if forward_socket is None:
                        data = gevent.os.tp_read(rstdin, 128)
                    else:
                        if hasattr(forward_socket, 'receive'):
                            data = forward_socket.receive()
                        else:
                            data = forward_socket.recv(128)
                    if data:
                        self.socket.send(data)
                    else:
                        raise NoDataException("No data from input source.")
                except Exception as e:
                    print e
                    cleanup(write_greenlet)
                    break

        if forward_socket is None:
            old_settings = termios.tcgetattr(rstdin)
            tty.setraw(sys.stdin)
        try:
            write_greenlet = gevent.spawn(write_loop)
            read_greenlet = gevent.spawn(read_loop)
            gevent.joinall([write_greenlet, read_greenlet])
        finally:
            if forward_socket is None:
                termios.tcsetattr(rstdin, termios.TCSADRAIN, old_settings)

@contextmanager
def client(host):
    c = Client(host)
    try:
        yield c
    finally:
        print "Closing dockerps client socket"
        c.close()


