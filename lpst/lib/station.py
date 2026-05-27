from __future__ import annotations
import os, sys, select, signal, time, termios, tty
from errno import EIO as IO_ERRNO
from lpst.lib.transcript import Transcript

_MIN_WAIT = 0.1 # seconds
_WAIT_LENIENCE = 5 # wait lenience * actual wait = allowed wait
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
        self.time = time.time()
        self.wait = 0
        self._deferred = b''

    def read(self) -> bytes:
        while True:
            chunk = os.read(self.fd, _READ_SIZE)
            if not chunk:
                if self._deferred:
                    data = self._deferred.replace(b'\r\n', b'\n').removesuffix(b'\r')
                    self._deferred = b''
                    return data
                return b''

            if self._deferred:
                chunk = self._deferred + chunk
                self._deferred = b''

            chunk = chunk.replace(b'\r\n', b'\n')
            if chunk.endswith(b'\r'):
                self._deferred = chunk
                continue

            return chunk

    def add_echo(self, data: bytes):
        self.echo += data

    def set_time(self):
        self.time = time.time()

    def check_time(self) -> bool:
        self.wait = (time.time() - self.time) * _WAIT_LENIENCE
        self.set_time()
        return self.wait > _MIN_WAIT

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

            # our stdin, send to child (before stdout so echo is buffered)
            if sys.stdin in r:
                data = stdin.read()
                os.write(master_fd, data)
                transcript.transcribe_input(data)
                stdout.add_echo(data)
                stdout.set_time()

            # child stdout, send to transcript and user stdout
            if master_fd in r:
                data = stdout.read()
                if not data: break # child died
                data = stdout.check_echo(data)

                # check for long delay
                if stdout.check_time():
                    transcript.transcribe_wait(stdout.wait)

                transcript.transcribe_output(data)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

    except OSError as e:
        if e.errno == IO_ERRNO: pass
        else: raise e

def playback_loop(master_fd: int,
                  p_transcript: Transcript,
                  r_transcript: Transcript,
                  ):
    stdout = LpstReader(master_fd)
    input_done = False
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
            elif not input_done:
                data = r_transcript.get_next_input()
                if isinstance(data, bytes) and data:
                    os.write(master_fd, data)
                    p_transcript.transcribe_input(data)
                    stdout.add_echo(data)
                elif isinstance(data, float):
                    time.sleep(data)
                elif data == Transcript.END_INPUT:
                    input_done = True
    except OSError as e:
        if e.errno == IO_ERRNO: pass
        else: raise e
