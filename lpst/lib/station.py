import os, sys, select, signal, time, termios, tty
from errno import EIO as IO_ERRNO
from lpst.lib.transcript import Transcript

_MIN_WAIT = 0.005 # seconds

def child_execvp(argv: list[str]):
    ''' * argv: shell command and args to run               '''
    ''' argv[0] is the name of our command,                 '''
    ''' we search PATH for it and abort if it doesn't exist '''
    ''' this should be called from a child process          '''

    try:
        os.execvp(argv[0], argv)
    except FileNotFoundError: # In case our shutil.which check fails
        os.kill(os.getppid(), signal.SIGTERM)

def _lpst_read(fd: int, size: int) -> bytes:
    ''' * fd: file descriptor to read from                  '''
    ''' * size: number of bytes to read                     '''
    ''' + returns data: byte data read from fd              '''
    ''' + if there is nothing to read, return b''           '''
    data = os.read(fd, size)
    data = data.replace(b'\r\n', b'\n')
    return data

# TODO: make stdin queue an object?
def _check_echo(queue: bytes, data: bytes) -> tuple[bytes, bytes]:
    ''' * queue: record of previous stdin that might echo   '''
    ''' * data: stdout that's coming right now              '''
    ''' removes data from queue or queue from data          '''
    ''' + returns tuple(new_queue, new_data)                '''
    # Data might be all of or some of stdin queue
    if queue.startswith(data):
        queue = queue.removeprefix(data)
        data = b''
    # Partial echo: we might get some echo and some new data
    elif data.startswith(queue):
        data = data.removeprefix(queue)
        queue = b''
    return (queue, data)

# TODO: these might want to be one function again
def record_loop(master_fd: int, transcript: Transcript):
    stdin_queue = b""
    try:
        while True:
            # readable, writeable, error
            r, _w, _e = select.select([master_fd, sys.stdin], [], [])

            # child stdout, send to transcript and user stdout
            # TODO: Large enough IO (4096 ASCII chars?) breaks mysteriously
            if master_fd in r:
                data = _lpst_read(master_fd, 1024)
                if not data: break # child died
                stdin_queue, data = _check_echo(stdin_queue, data)
                transcript.transcribe_output(data)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            # our stdin, send to child
            if sys.stdin in r:
                # TODO: should we just use input()? How to not byte limit?
                data = _lpst_read(sys.stdin.fileno(), 1024)
                os.write(master_fd, data)
                transcript.transcribe_input(data)
                stdin_queue += data
    except OSError as e:
        if e.errno == IO_ERRNO: pass
        else: raise e

def playback_loop(master_fd: int,
                  p_transcript: Transcript,
                  r_transcript: Transcript,
                  ):
    stdin_queue = b""
    try:
        while True:
            # readable, writeable, error
            r, _w, _e = select.select([master_fd], [], [], _MIN_WAIT)

            # child stdout, send to transcript
            if master_fd in r:
                data = _lpst_read(master_fd, 1024)
                if not data: break # child died
                stdin_queue, data = _check_echo(stdin_queue, data)
                p_transcript.transcribe_output(data)

            # ask for stdin if we don't have stdout after _MIN_WAIT
            else:
                data = r_transcript.get_next_input()
                if isinstance(data, bytes) and data:
                    os.write(master_fd, data)
                    p_transcript.transcribe_input(data)
                    stdin_queue += data
                    time.sleep(_MIN_WAIT)
                elif isinstance(data, int):
                    # Check for end input sentinel
                    if data == Transcript.END_INPUT: break
                    time.sleep(data / 1000)
    except OSError as e:
        if e.errno == IO_ERRNO: pass
        else: raise e
