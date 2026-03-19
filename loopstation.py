import sys
from record import record

if __name__ == "__main__":
    match sys.argv[1:]:
        case ['record', *args]:
            try:
                record(args)
            except KeyboardInterrupt:
                sys.stderr.write("\nLoopstation: Interrupted, exiting without recording")
        case ['synthesize', *args]:
            print("WIP")
        case ['playback', *args]:
            print("WIP")
        case ['rerecord', *args]:
            print("WIP")
        case _:
            sys.exit(
"""Loopstation - CLI recorder for lazy tests

Usage -
\tloopstation record {program} [args...]     - Record a test
\tloopstation synthesize {program}           - Manually write a transcript
\tloopstation playback {program} [testnames] - Playback tests
\tloopstation rerecord {program} [testnames] - Playback tests and edit failures"""
            )
