import os, pty, sys, select, shutil
from station import child_execvp, playback_loop
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

def playback_one(test_file: str):
    with open(test_file, 'r') as file:
        # This naming convention has done but it works
        their_transcript = Transcript.load(file)
        our_transcript = Transcript(their_transcript.argv)

        pid, master_fd = pty.fork()

        # we're child, become program
        if pid == 0:
            return child_execvp(their_transcript.argv)

        # otherwise, we're parent
        playback_loop(master_fd, our_transcript, their_transcript)
        if our_transcript == their_transcript:
            print(f"LOOPSTATION: Test {test_file} passed!")
        else:
            # TODO: output better diff
            our_transcript.print()
            their_transcript.print()
