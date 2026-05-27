from playback import playback_one

def rerecord(test_dir: str,
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

