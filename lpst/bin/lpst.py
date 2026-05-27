import sys, argparse

from lpst.bin.playback import playback
from lpst.bin.rerecord import rerecord
from lpst.bin.record import record
from lpst.lib.diff import DiffMode, DIFF_MODE_STRS

DESCRIPTION = "CLI recorder for lazy tests"

def _cmd_record(args: argparse.Namespace) -> None:
    try:
        record([args.program, *args.args])
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted, exiting without recording\n")

def _cmd_synthesize(_args: argparse.Namespace) -> None:
    print("WIP")

def _cmd_playback(args: argparse.Namespace) -> None:
    diff_mode = getattr(DiffMode, args.diff.upper())
    playback(args.test_dir, args.tests, diff=diff_mode)

def _cmd_rerecord(args: argparse.Namespace) -> None:
    diff_mode = getattr(DiffMode, args.diff.upper())
    rerecord(args.test_dir, args.tests, diff=diff_mode)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lpst", description=DESCRIPTION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="Record a test")
    record.add_argument("program", help="Program to record")
    record.add_argument("args", nargs="*", default=[],
                        help="Arguments for the program")
    record.set_defaults(func=_cmd_record)

    synthesize = subparsers.add_parser("synthesize",
                                       help="Manually write a transcript")
    synthesize.set_defaults(func=_cmd_synthesize)

    playback = subparsers.add_parser("playback", help="Playback tests")
    playback.add_argument("test_dir", help="Directory containing test files")
    playback.add_argument("tests", nargs="*", default=[],
                          help="Test names (default: all tests in directory)")
    playback.add_argument("--diff",
                          choices=DIFF_MODE_STRS, default=DIFF_MODE_STRS[0],
                          help="Diff format on failure (default: %(default)s)")
    playback.set_defaults(func=_cmd_playback)

    rerecord = subparsers.add_parser("rerecord",
                                     help="Playback tests and edit failures")
    rerecord.add_argument("test_dir", help="Directory containing test files")
    rerecord.add_argument("tests", nargs="*", default=[],
        help="Test names (default: all tests in directory)")
    rerecord.add_argument("--diff",
                          choices=DIFF_MODE_STRS, default=DIFF_MODE_STRS[0],
                          help="Diff format on failure (default: %(default)s)")
    rerecord.set_defaults(func=_cmd_rerecord)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
