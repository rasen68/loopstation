import os, pty, sys, select, shutil

def record(program: str, args: list[str]):
    if not shutil.which(program):
        sys.exit(f"Loopstation: File {program} not found, check $PATH?")
    else:
        print("--- LOOPSTATION: STARTING RECORDING ---")

    pid, master_fd = pty.fork()

    # we're child, become program
    if pid == 0:
        return child_execvp([program] + args)

    # otherwise, we're parent
    header = f"$ [{program}]"
    for arg in args:
        header += f" [{arg}]"
    header += '\n'
    transcript = parent_loop(master_fd, header)
    finish_recording(transcript)

def child_execvp(argv: list[str]):
    try:
        return os.execvp(argv[0], argv)
    except FileNotFoundError: # In case our shutil.which check fails
        os.kill(os.getppid(), signal.SIGTERM)

def parent_loop(master_fd: int, transcript: str):
    # TODO: should probs be a queue instead, might solve big input problem
    last_stdin = None
    try:
        while True:
            # readable, writeable, error
            r, _w, _e = select.select([master_fd, sys.stdin], [], [])

            # child stdout, send to transcript and user stdout
            # TODO: test IO > 1024
            if master_fd in r:
                data = os.read(master_fd, 1024)
                if not data: break # child died
                try: # Decode data for transcript
                    data_str = data.decode('utf-8')
                    prefix = "[ "
                except UnicodeDecodeError:
                    # Decode failed, write data in hex (x) mode
                    # TODO: binary input, e.g. piped from file?
                    data_str = data.hex()
                    if not transcript.endswith('\n') and transcript[-1] != '\n':
                        transcript += '\\\n'
                    prefix = "x "

                # Process transcript
                if transcript.endswith('\n'):
                    transcript += prefix
                if '\n' in data_str[:-1]:
                    data_str = (data_str[:-1].replace('\n', '\n'+prefix)
                                + data_str[-1:])
                data_str = data_str.replace('\r\n', '\n')
                transcript += data_str

                # Write to stdout, subtracting last stdin to avoid duplication
                # TODO: this doesnt work
                sys.stdout.buffer.write(f"DATA: {data}\n".encode())
                sys.stdout.buffer.flush()
                if data.startswith(last_stdin):
                    last_stdin = None
                    data.removeprefix(last_stdin)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()

            # our stdin, send to child
            if sys.stdin in r:
                data = os.read(sys.stdin.fileno(), 1024)
                last_stdin = data
                sys.stdout.buffer.write(f"LAST_STDIN: {last_stdin}\n".encode())
                sys.stdout.buffer.flush()
                os.write(master_fd, data)

                # Tell transcript we read stdin
                # Child pty will print this to screen,
                # So we let stdout write it to transcript
                if not transcript.endswith('\n') and transcript[-1] != '\n':
                    transcript += '\\\n'
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
                # TODO: windows vs unix
                while not (name := input("Loopstation: Enter test name - ")):
                    pass
                try:
                    filename = name + '.lpst'
                    with open(filename, 'x') as f:
                        f.write(transcript)
                    print(f"Loopstation: Saved to {filename}")
                    return
                except FileExistsError:
                    print(f"Loopstation: {filename} already exists!")
                # TODO: handle other errors
            case _:
                pass
