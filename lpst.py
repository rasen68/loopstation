#!/usr/bin/python3
import sys
from record import record
from playback import playback

if __name__ == "__main__":
    match sys.argv[1:]:
        case ['record', program, *args]:
            try:
                record(program, args)
            except KeyboardInterrupt:
                sys.stderr.write("\nLoopstation: Interrupted, exiting without recording\n")
        case ['synthesize', program]:
            print("WIP")
        case ['playback', test_dir, *tests]:
            playback(test_dir, tests)
        case ['rerecord', test_dir, *tests]:
            print("WIP")
        case _:
            sys.exit(
"""Loopstation - CLI recorder for lazy tests

Usage -
\tlpst record {program} [args...]   - Record a test
\tlpst synthesize {program}         - Manually write a transcript
\tlpst playback {test_dir} [tests]  - Playback tests
\tlpst rerecord {test_dir} [tests]  - Playback tests and edit failures"""
            )
