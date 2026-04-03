import os, sys, signal, select
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
                silent: bool=False):
    while True:
        # readable, writeable, error
        r, _w, _e = select.select([master_fd, sys.stdin], [], [])

        # child stdout, send to transcript and user stdout
        # TODO: Large enough IO (4096 ASCII chars?) breaks mysteriously
        if master_fd in r:
            data = os.read(master_fd, 1024)
            if not data: break # child died
            transcript.output_prefix()
            transcript.transcribe(data)
            if not silent:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

        # our stdin, send to child
        if sys.stdin in r:
            data = stdin_callable()
            os.write(master_fd, data)
            transcript.input_prefix()
            transcript.transcribe(data)
