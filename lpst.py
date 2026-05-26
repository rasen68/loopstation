#!/usr/bin/python3
import sys
from record import record
from playback import playback
from diff import DiffMode

def _parse_playback_args(rest: list[str]) -> tuple[list[str], DiffMode]:
    diff = DiffMode.RAW
    tests = []
    for arg in rest:
        if arg.startswith("--diff="):
            mode = arg.removeprefix("--diff=")
            try:
                diff = DiffMode(mode)
            except ValueError:
                modes = "/".join(m.value for m in DiffMode)
                sys.exit(f"Loopstation: unknown diff mode {mode!r}, use {modes}")
        else:
            tests.append(arg)
    return tests, diff

if __name__ == "__main__":
    match sys.argv[1:]:
        case ['record', *argv]:
            try:
                record(argv)
            except KeyboardInterrupt:
                sys.stderr.write("\nLoopstation: Interrupted, exiting without recording\n")
        case ['synthesize', program]:
            print("WIP")
        case ['playback', test_dir, *rest]:
            tests, diff = _parse_playback_args(rest)
            playback(test_dir, tests, diff=diff)
        case ['rerecord', test_dir, *tests]:
            print("WIP")
        case _:
            sys.exit(
"""Loopstation - CLI recorder for lazy tests

Usage -
\tlpst record {program} [args...]   - Record a test
\tlpst synthesize {program}         - Manually write a transcript
\tlpst playback {test_dir} [tests] [--diff=raw|rich|vim]  - Playback tests
\tlpst rerecord {test_dir} [tests]  - Playback tests and edit failures"""
            )
