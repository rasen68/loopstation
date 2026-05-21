import os, sys, signal, select, termios, tty
from typing import TextIO
from transcript import Transcript

def child_execvp(argv: list[str]):
    ''' * argv: shell command and args to run               '''
    ''' argv[0] is the name of our command,                 '''
    ''' we search PATH for it and abort if it doesn't exist '''
    ''' this should be called from a child process          '''

    try:
        os.execvp(argv[0], argv)
    except FileNotFoundError: # In case our shutil.which check fails
        os.kill(os.getppid(), signal.SIGTERM)

def _lpst_read(fd: TextIO, size: int) -> bytes:
    ''' * fd: file descriptor to read from                  '''
    ''' * size: number of bytes to read                     '''
    ''' + returns data: byte data read from fd              '''
    ''' + if there is nothing to read, return b''           '''
    data = os.read(fd, 1024)
    data = data.replace(b'\r\n', b'\n')
    return data

def record_loop(master_fd: int, transcript: Transcript):
    while True:
        # readable, writeable, error
        r, _w, _e = select.select([master_fd, sys.stdin], [], [])

        # child stdout, send to transcript and user stdout
        # TODO: Large enough IO (4096 ASCII chars?) breaks mysteriously
        if master_fd in r:
            data = _lpst_read(master_fd, 1024)
            if not data: break # child died TODO: is this definitely true
            transcript.transcribe_output(data)

            # write to stdout
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

        # our stdin, send to child
        if sys.stdin in r:
            data = _lpst_read(sys.stdin.fileno(), 1024)
            os.write(master_fd, data)
            transcript.transcribe_input(data)

def playback_loop(master_fd: int,
                  our_transcript: Transcript,
                  their_transcript: Transcript,
                  ):
    while True:
        # readable, writeable, error
        r, _w, _e = select.select([master_fd], [], [])

        # child stdout, send to transcript and user stdout
        # TODO: Large enough IO (4096 ASCII chars?) breaks mysteriously
        if master_fd in r:
            data = _lpst_read(master_fd, 1024)
            if not data: break # child died TODO: is this definitely true
            our_transcript.transcribe_output(data)

        # our stdin, send to child
        if sys.stdin in r:
            data = their_transcript.get_next_input()
            # It will read and call this even if there is nothing there
            if data:
                os.write(master_fd, data)
                our_transcript.transcribe_input(data)
