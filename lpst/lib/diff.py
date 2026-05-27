import os, shlex, difflib, tempfile, subprocess
from enum import Enum
from itertools import zip_longest

from lpst.lib.transcript import Transcript

def raw_diff(expected: Transcript, actual: Transcript) -> None:
    for line in difflib.unified_diff(
        expected.get_strs(argv=True),
        actual.get_strs(argv=True),
        fromfile="expected",
        tofile="actual",
        lineterm="",
    ):
        print(line)


def rich_diff(expected: Transcript, actual: Transcript) -> None:
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
            table.add_row(Text(exp or "·"), Text(act or "·"))
        else:
            exp_style = "white on dark_red" if exp else "dim"
            act_style = "white on dark_green" if act else "dim"
            exp_cell = Text(exp or "·", style=exp_style)
            act_cell = Text(act or "·", style=act_style)
            table.add_row(exp_cell, act_cell)

    Console().print(table)


def vim_diff(expected: Transcript, actual: Transcript) -> None:
    diff_dir = tempfile.mkdtemp(prefix=f"loopstation-diff-")
    expected_path = os.path.join(diff_dir, "expected")
    actual_path = os.path.join(diff_dir, "actual")

    with open(expected_path, 'w') as file:
        file.write('\n'.join(expected.get_strs(argv=True)) + '\n')
    with open(actual_path, 'w') as file:
        file.write('\n'.join(actual.get_strs(argv=True)) + '\n')

    subprocess.run(['vim', '-d',
                    shlex.quote(expected_path),
                    shlex.quote(actual_path)])

class DiffMode(Enum):
    RICH = rich_diff
    RAW = raw_diff
    VIM = vim_diff
    NONE = lambda x,y: None
DIFF_MODE_STRS = "rich", "raw", "vim", "none"
