import sys
from record import record

if __name__ == "__main__":
    match sys.argv[1:]:
        case ['record', program, *args]:
            try:
                record(program, args)
            except KeyboardInterrupt:
                sys.stderr.write("\nLoopstation: Interrupted, exiting without recording")
        case ['synthesize', program, *args]:
            print("WIP")
        case ['playback', program, *args]:
            print("WIP")
        case ['rerecord', program, *args]:
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
