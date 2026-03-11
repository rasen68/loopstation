import os, pty, sys, select, shutil

def record(argv: list[str]):
    if not shutil.which(argv[0]):
        print("Loopstation: File not found, check $PATH?", file=sys.stderr)
        return
    else:
        print("--- LOOPSTATION: STARTING RECORDING ---")

    pid, master_fd = pty.fork()

    # we're child, become program
    if pid == 0:
        try:
            os.execvp(argv[0], argv)
        except FileNotFoundError: # In case our shutil.which check fails
            os.kill(os.getppid(), signal.SIGTERM)
        finally:
            return

    # otherwise, we're parent
    else:
        transcript = parent_loop(master_fd)
        finish_recording(transcript)

def parent_loop(master_fd):
    transcript = f"""$ {" ".join(argv)}\n"""
    print(transcript)
    try:
        while True:
            # readable, writeable, error
            r, _, _ = select.select([master_fd, sys.stdin], [], [])

            # child stdout, send to transcript and user stdout
            if master_fd in r:
                data = os.read(master_fd, 1024)
                if not data: break # child died
                transcript += data.decode('utf-8') # TODO: can this fail? e.g. cat a bytestream
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

def finish_recording(transcript):
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
                testname = input("Loopstation: Enter test name - ")
                try:
                    with open(testname + '.lpst', 'x') as f:
                        f.write(transcript)
                    print("Loopstation: Saved to", testname)
                except FileExistsError:
                    print("Loopstation:", testname, "already exists! Pick a new name")
                # TODO: handle other errors
            case _:
                pass

if __name__ == "__main__":
    try:
        record(sys.argv[1:])
    except KeyboardInterrupt:
        print("\nLoopstation: Interrupted, exiting without recording", file=sys.stderr)
