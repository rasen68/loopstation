import difflib
import os
import shlex
import sys
import tempfile
from enum import StrEnum
from itertools import zip_longest

from transcript import Transcript


class DiffMode(StrEnum):
    RAW = "raw"
    RICH = "rich"
    VIM = "vim"


def _transcript_lines(transcript: Transcript) -> list[str]:
    argv = "$ " + " ".join(f"[{arg}]" for arg in transcript.argv)
    return [argv, *transcript.get_strs()]


def print_diff(expected: Transcript,
               actual: Transcript,
               mode: DiffMode = DiffMode.RAW,
               *,
               test_file: str = "test",
               ) -> None:
    match mode:
        case DiffMode.RAW:
            _print_diff_raw(expected, actual)
        case DiffMode.RICH:
            _print_diff_rich(expected, actual)
        case DiffMode.VIM:
            _print_diff_vim(expected, actual, test_file)


def _print_diff_raw(expected: Transcript, actual: Transcript) -> None:
    for line in difflib.unified_diff(
        _transcript_lines(expected),
        _transcript_lines(actual),
        fromfile="expected",
        tofile="actual",
        lineterm="",
    ):
        print(line)


def _print_diff_rich(expected: Transcript, actual: Transcript) -> None:
    try:
        from rich.console import Console
        from rich.style import Style
        from rich.table import Table
        from rich.text import Text
    except ImportError:
        sys.exit("Loopstation: rich diff requires `pip install rich`")

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("expected", overflow="fold")
    table.add_column("actual", overflow="fold")

    for exp, act in zip_longest(
        _transcript_lines(expected),
        _transcript_lines(actual),
        fillvalue="",
    ):
        if exp == act:
            table.add_row(exp, act)
        else:
            exp_cell = Text(exp or "·", style=Style(dim=True) if not exp else Style(on_color="dark_red"))
            act_cell = Text(act or "·", style=Style(dim=True) if not act else Style(on_color="dark_green"))
            table.add_row(exp_cell, act_cell)

    Console().print(table)


def _print_diff_vim(expected: Transcript,
                    actual: Transcript,
                    test_file: str,
                    ) -> None:
    label = os.path.splitext(os.path.basename(test_file))[0]
    diff_dir = tempfile.mkdtemp(prefix=f"loopstation-diff-{label}-")
    expected_path = os.path.join(diff_dir, "expected")
    actual_path = os.path.join(diff_dir, "actual")

    for path, lines in (
        (expected_path, _transcript_lines(expected)),
        (actual_path, _transcript_lines(actual)),
    ):
        with open(path, "w") as file:
            file.write("\n".join(lines))
            file.write("\n")

    print(f"Loopstation: diff files written to {diff_dir}")
    cmd = "vim -d " + " ".join(shlex.quote(path) for path in (expected_path, actual_path))
    print(f"  {cmd}")
