import os, pty, sys, select, shutil
from station import child_execvp, parent_loop
from transcript import Transcript

def playback(test_dir: str, tests: list[str]=[]):
    tests = [t + '.lpst' if not t.endswith('.lpst') else t for t in tests]
    if not os.path.isdir(test_dir):
        sys.exit(f"Loopstation: {test_dir} is not a directory, exiting")
    elif not all(os.path.isfile(os.path.join(test_dir, t)) for t in tests):
        sys.exit(f"Loopstation: One or more tests invalid, please check or pass no argument for all tests")
    else:
        print("--- LOOPSTATION: STARTING PLAYBACK ---")

    for test in (tests or os.listdir(test_dir)):
        playback_one(os.path.join(test_dir, test))

def playback_one(test: str):
    with open(test, 'r') as file:
        file_str = file.read()
        header = file_str.splitlines()[0]
        their_transcript = Transcript(file_str)
        our_transcript = Transcript(header)

        # Assuming no [] in argv for now
        argv = header.split(']')
        argv = [arg[arg.index('[')+1:] for arg in argv if arg]
        if not shutil.which(argv[0]):
            print(f"Test {test}: File {argv[0]} not found, check $PATH?")
            return

        pid, master_fd = pty.fork()

        # we're child, become program
        if pid == 0:
            return child_execvp(argv)

        # otherwise, we're parent
        try:
            parent_loop(master_fd,
                        our_transcript,
                        their_transcript.get_next_input)
        except OSError as e:
            if e.errno == 5: # IO error
                print("--- LOOPSTATION: PROGRAM EXITED ---\n")
            else: raise e
        our_transcript.print()
