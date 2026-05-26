import os, shlex, difflib, tempfile, subprocess
from enum import StrEnum
from itertools import zip_longest

from lpst.lib.transcript import Transcript

class DiffMode(StrEnum):
    RAW = "raw"
    RICH = "rich"
    VIM = "vim"

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
        expected.get_strs(argv=True),
        actual.get_strs(argv=True),
        fromfile="expected",
        tofile="actual",
        lineterm="",
    ):
        print(line)


def _print_diff_rich(expected: Transcript, actual: Transcript) -> None:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("expected", overflow="fold")
    table.add_column("actual", overflow="fold")

    for exp, act in zip_longest(
        expected.get_strs(argv=True),
        actual.get_strs(argv=True),
        fillvalue="",
    ):
        if exp == act:
            table.add_row(exp, act)
        else:
            exp_cell = Text(exp or "·", style="dim" if not exp else "white on dark_red")
            act_cell = Text(act or "·", style="dim" if not act else "white on dark_green")
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
        (expected_path, expected.get_strs(argv=True)),
        (actual_path, actual.get_strs(argv=True)),
    ):
        with open(path, "w") as file:
            file.write("\n".join(lines))
            file.write("\n")

    print(f"Loopstation: diff files written to {diff_dir}")
    cmd = "vim -d " + " ".join(shlex.quote(path) for path in (expected_path, actual_path))
    subprocess.run(cmd, shell=True)
