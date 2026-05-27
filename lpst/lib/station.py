from __future__ import annotations
import os, sys, select, signal, time, termios, tty
from errno import EIO as IO_ERRNO
from lpst.lib.transcript import Transcript

_MIN_WAIT = 0.1 # seconds
_READ_SIZE = 1024

def child_execvp(argv: list[str]):
    ''' * argv: shell command and args to run               '''
    ''' argv[0] is the name of our command,                 '''
    ''' we search PATH for it and abort if it doesn't exist '''
    ''' this should be called from a child process          '''

    try:
        os.execvp(argv[0], argv)
    except FileNotFoundError: # In case our shutil.which check fails
        os.kill(os.getppid(), signal.SIGTERM)

class LpstReader:
    def __init__(self, fd: int) -> LpstReader:
        self.fd = fd
        self.echo = b''
        self._cr = False

    def read(self) -> bytes:
        data = os.read(self.fd, _READ_SIZE)
        data = data.replace(b'\r\n', b'\n')
        # Deal with possible split \r\n across reads
        if self._cr and not data.startswith(b'\n'):
            data = b'\r' + data
        if data.endswith(b'\r'):
            data = data.removesuffix(b'\r')
            self._cr = True
        return data

    def add_echo(self, data: bytes):
        self.echo += data

    def check_echo(self, data: bytes) -> bytes:
        if self.echo.startswith(data):
            self.echo = self.echo.removeprefix(data)
            data = b''
        # Partial echo: we might get some echo and some new data
        elif data.startswith(self.echo):
            data = data.removeprefix(self.echo)
            self.echo = b''
        return data

def record_loop(master_fd: int, transcript: Transcript):
    stdout = LpstReader(master_fd)
    stdin  = LpstReader(sys.stdin.fileno())
    try:
        while True:
            # readable, writeable, error
            r, _w, _e = select.select([master_fd, sys.stdin], [], [])

            # child stdout, send to transcript and user stdout
            if master_fd in r:
                data = stdout.read()
                if not data: break # child died
                data = stdout.check_echo(data)

                transcript.transcribe_output(data)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            # our stdin, send to child
            if sys.stdin in r:
                data = stdin.read()
                os.write(master_fd, data)
                transcript.transcribe_input(data)
                stdout.add_echo(data)

    except OSError as e:
        if e.errno == IO_ERRNO: pass
        else: raise e

def playback_loop(master_fd: int,
                  p_transcript: Transcript,
                  r_transcript: Transcript,
                  ):
    stdout = LpstReader(master_fd)
    try:
        while True:
            # readable, writeable, error
            r, _w, _e = select.select([master_fd], [], [], _MIN_WAIT)

            # child stdout, send to transcript
            if master_fd in r:
                data = stdout.read()
                if not data: break # child died
                data = stdout.check_echo(data)
                p_transcript.transcribe_output(data)

            # ask for stdin if we don't have stdout after _MIN_WAIT
            else:
                data = r_transcript.get_next_input()
                if isinstance(data, bytes) and data:
                    os.write(master_fd, data)
                    p_transcript.transcribe_input(data)
                    stdout.add_echo(data)
                elif isinstance(data, int):
                    # Check for end input sentinel
                    if data == Transcript.END_INPUT: break
                    time.sleep(data / 1000)
    except OSError as e:
        if e.errno == IO_ERRNO: pass
        else: raise e
