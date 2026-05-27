from lpst.bin.playback import iter_tests, playback_one
from lpst.lib.diff import DiffMode

def rerecord(test_dir: str,
             test_names: list[str] = [],
             diff: DiffMode = DiffMode.RAW,
             ):
    print("--- LOOPSTATION: STARTING RERECORD ---")
    for test_file in iter_tests(test_dir, test_names):
        passed, actual = playback_one(test_file, diff)
        if not passed:
            print("Replace saved (expected) with new (actual)? [y/N] ", end='')
            if input().upper() == 'Y':
                actual.save(test_file, overwrite=True)
                print(f"Saved to {test_file}")
