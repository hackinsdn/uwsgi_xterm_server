# terminal_backend.py
# Responsável por criar um subprocesso com PTY e encaminhar I/O

import os
import fcntl
import struct
import termios
import tty
import select
import threading
from ptyprocess import PtyProcessUnicode


class PtyTerminal:
    def __init__(self, cmd=['/bin/bash']):
        # cria um processo com pty
        self.proc = PtyProcessUnicode.spawn(cmd)
        self.lock = threading.Lock()


    def read(self, timeout=0.01):
        '''Lê qualquer saída disponível do pty.'''
        with self.lock:
            try:
                return self.proc.read_nonblocking(size=4096, timeout=timeout)
            except Exception:
                return ''


    def write(self, data):
        with self.lock:
            try:
                self.proc.write(data)
            except Exception:
                pass


    def resize(self, cols, rows):
        # envia TIOCSWINSZ
        with self.lock:
            try:
                TIOCSWINSZ = getattr(termios, 'TIOCSWINSZ', -2146929568)
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.proc.fd, termios.TIOCSWINSZ, winsize)
            except Exception:
                pass


    def isalive(self):
        return self.proc.isalive()


    def close(self):
        try:
            self.proc.terminate(force=True)
        except Exception:
            pass