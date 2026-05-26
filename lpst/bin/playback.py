import os, pty, sys, select, shutil
from lpst.lib.station import child_execvp, playback_loop
from lpst.lib.transcript import Transcript
from lpst.lib.diff import DiffMode

def playback(test_dir: str,
             test_names: list[str] = [],
             diff: DiffMode = DiffMode.RAW,
             ):
    tests = []
    for t in test_names:
        if not t.startswith('lpst.'): t = 'lpst.' + t
        if not t.endswith('.json'): t = t + '.json'
        tests.append(t)

    if not os.path.isdir(test_dir):
        sys.exit(f"Loopstation: {test_dir} is not a directory, exiting")
    elif not all(os.path.isfile(os.path.join(test_dir, t)) for t in tests):
        sys.exit(f"Loopstation: One or more tests invalid, please check or pass no argument for all tests")
    else:
        print("--- LOOPSTATION: STARTING PLAYBACK ---")

    for test in (tests or os.listdir(test_dir)):
        _playback_one(os.path.join(test_dir, test), diff)

def _playback_one(test_file: str, diff: DiffMode):
    with open(test_file, 'r') as file:
        recorded = Transcript.load(file)
        actual = Transcript(recorded.argv)

        pid, master_fd = pty.fork()

        # we're child, become program
        if pid == 0:
            return child_execvp(recorded.argv)

        # otherwise, we're parent
        playback_loop(master_fd, actual, recorded)
        actual.rechunk()
        if recorded == actual:
            print(f"LOOPSTATION: Test {test_file} passed!")
        else:
            print(f"LOOPSTATION: Test {test_file} failed!")
            diff(recorded, actual)
