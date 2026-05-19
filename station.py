import os, sys, signal, select, termios, tty
from typing import Callable
from transcript import Transcript

def read_stdin() -> bytes:
    return os.read(sys.stdin.fileno(), 1024)

def child_execvp(argv: list[str]):
    try:
        return os.execvp(argv[0], argv)
    except FileNotFoundError: # In case our shutil.which check fails
        os.kill(os.getppid(), signal.SIGTERM)

def parent_loop(master_fd: int,
                transcript: Transcript,
                stdin_callable: Callable[[], bytes]=read_stdin,
                *,
                filter_stdin: bool=False,
                silent: bool=False,
                ):
    # Turn off echo
    slave_fd = os.open(os.ttyname(master_fd), os.O_RDWR)
    attrs = termios.tcgetattr(slave_fd)
    attrs[3] &= ~termios.ECHO
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)
    os.close(slave_fd)

    while True:
        # readable, writeable, error
        r, _w, _e = select.select([master_fd, sys.stdin], [], [])

        # child stdout, send to transcript and user stdout
        # TODO: Large enough IO (4096 ASCII chars?) breaks mysteriously
        if master_fd in r:
            data = os.read(master_fd, 1024)
            if not data: break # child died

            # process data
            data = data.replace(b'\r\n', b'\n')
            if data:
                transcript.output_prefix()
                transcript.transcribe(data)
                if not silent:
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()

        # our stdin, send to child
        if sys.stdin in r:
            data = stdin_callable()
            data = data.replace(b'\r\n', b'\n')
            if data:
                os.write(master_fd, data)
                transcript.input_prefix()
                transcript.transcribe(data)
