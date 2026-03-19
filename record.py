import os, pty, sys, select, shutil

def record(argv: list[str]):
    if not shutil.which(argv[0]):
        sys.exit("Loopstation: File not found, check $PATH?")
    else:
        print("--- LOOPSTATION: STARTING RECORDING ---")

    pid, master_fd = pty.fork()

    # we're child, become program
    if pid == 0:
        return child_execvp(argv)

    # otherwise, we're parent
    print(header := f"""$ {" ".join(argv)}\n""")
    transcript = parent_loop(master_fd, header)
    finish_recording(transcript)

def child_execvp(argv: list[str]):
    try:
        return os.execvp(argv[0], argv)
    except FileNotFoundError: # In case our shutil.which check fails
        os.kill(os.getppid(), signal.SIGTERM)

def parent_loop(master_fd: int, transcript: str):
    try:
        while True:
            # readable, writeable, error
            r, _, _ = select.select([master_fd, sys.stdin], [], [])

            # child stdout, send to transcript and user stdout
            if master_fd in r:
                data = os.read(master_fd, 1024)
                if not data: break # child died
                try:
                    data_str = data.decode('utf-8')
                except UnicodeDecodeError:
                    # TODO: Mode to write bytes directly, maybe x ...
                    sys.exit("Loopstation: Can't decode non UTF-8 bytes, exiting\n")
                # TODO: Add stdout stream indicator, like [ ...
                # Idea: .lpst files should all look like
                # [char] input/output
                # $ means command
                # [ means output
                # > means input
                # x means bytes output
                # Mode for additional tests?
                # e.g. check pwd after

                transcript += data_str
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            # our stdin, send to child
            if sys.stdin in r:
                data = os.read(sys.stdin.fileno(), 1024)
                os.write(master_fd, data)

                # Tell transcript we read stdin
                # Child pty will print this to screen,
                # So we let stdout write it to transcript
                if not transcript.endswith("\n") and transcript[-1] != "\n":
                    transcript += "\\\n"
                transcript += "> "

    except OSError as e:
        if e.errno == 5: # I/O error
            print("--- LOOPSTATION: PROGRAM EXITED ---\n")
        else:
            raise e

    print("Loopstation: Recorded!")
    return transcript

def finish_recording(transcript: str):
    while True:
        match input("Loopstation: [s]ave/[v]iew recording/[q]uit - "):
            case 'v':
                print("--- LOOPSTATION: TRANSCRIPT ---")
                print(transcript)
                print("--- LOOPSTATION: END TRANSCRIPT ---")
            case 'q':
                print("\nLoopstation: Exiting without saving transcript")
                return
            case 's':
                # TODO: directory stuff
                # TODO: Suggested test name
                testname = input("Loopstation: Enter test name - ")
                try:
                    with open(testname + '.lpst', 'x') as f:
                        f.write(transcript)
                    print("Loopstation: Saved to", testname)
                    continue
                except FileExistsError:
                    print("Loopstation:", testname, "already exists!")
                # TODO: handle other errors
            case _:
                pass
