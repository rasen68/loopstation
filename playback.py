import os, pty, sys, select, shutil
from record import child_execvp

def playback(test_dir: str, tests: list[str]=[]):
    if not os.path.isdir(test_dir):
        sys.exit(f"Loopstation: {test_dir} is not a directory, exiting")
    elif not all(os.path.isfile(os.path.join(test_dir, t)) for t in tests):
        sys.exit(f"Loopstation: One or more tests invalid, please check or pass no argument for all tests")
    else:
        print("--- LOOPSTATION: STARTING PLAYBACK ---")

    for test in (tests or os.path.listdir(test_dir)):
        playback_one(test)

def playback_one(test: str):
    with open(test, 'r') as transcript:

        # Assuming no [] in argv for now
        header = transcript.readline()
        argv = header.split(']')
        argv = [arg[arg.index['[']+1:] for arg in argv]
        if not shutil.which(argv[0]):
            sys.exit(f"Loopstation: File {argv[0]} not found, check $PATH?")

        pid, master_fd = pty.fork()
        # we're child, become program
        if pid == 0:
            return child_execvp(argv)

        # otherwise, we're parent
        parent_loop(master_fd)

def parent_loop(master_fd: int):
    transcript = ""
    try:
        while True:
            # readable, writeable, error
            r, _w, _e = select.select([master_fd, sys.stdin], [], [])

            # child stdout, send to transcript and user stdout
            # TODO: Large enough IO (4096 ASCII chars?) breaks mysteriously
            if master_fd in r:
                data = os.read(master_fd, 1024)
                if not data: break # child died
                transcript += '[ '
                transcript = write_data(transcript, data)

                # Write to stdout
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            # our stdin, send to child
            if sys.stdin in r:
                data = os.read(sys.stdin.fileno(), 1024)
                os.write(master_fd, data)
                transcript += '> '
                transcript = write_data(transcript, data)

    except OSError as e:
        if e.errno == 5: # I/O error
            print("--- LOOPSTATION: PROGRAM EXITED ---\n")
        else:
            raise e

    print("Loopstation: Recorded!")
    return transcript

