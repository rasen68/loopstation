from __future__ import annotations
from itertools import zip_longest
from copy import copy
import json

from lpst.lib.line import Prefix, Encoding, LpstLine

class Transcript:
    argv: list[str]
    _lines: list[LpstLine]
    _input_iter: iter[LpstLine] | None
    _output_iter: iter[LpstLine] | None
    END_INPUT = -1

    def __init__(self, argv: list[str]) -> Transcript:
        ''' * argv: all transcripts start with an executable '''
        self.argv = argv
        self._lines = []
        self._input_iter = None
        self._output_iter = None

    def _init_iters(self):
        self._input_iter = (l for l in self._lines if l.is_input_or_wait())
        self._output_iter = (l for l in self._lines if l.is_output())

    @classmethod
    def load(cls, file) -> Transcript:
        dicts = json.load(file)
        argv = dicts[0]['argv']
        transcript = cls(argv)
        for d in dicts[1:]:
            transcript._lines.append(LpstLine(**d))
        transcript._init_iters()
        transcript.rechunk()
        return transcript

    def _transcribe(self, prefix: Prefix, data: bytes):
        ''' * data: bytes to write to self.text             '''
        ''' this should be called when self.text ends with  '''
        ''' a loopstation prefix ('> ' or '[ '), appended   '''
        ''' by transcribe_input and transcribe_output       '''
        if not data: return # no reason to write blank lines
        line = LpstLine(prefix, Encoding.UTF, "")
        try:
            line.data = data.decode('utf-8')
        except UnicodeDecodeError:
            line.data = data.hex()
            line.encoding = Encoding.HEX
        self._lines.append(line)

    def _get_line(self, i: int) -> LpstLine:
        return self._lines[i]

    def rechunk(self):
        line_ptr = 1
        while line_ptr < len(self._lines):
            first, second = self._lines[line_ptr-1:line_ptr+1]
            if first.prefix == second.prefix:
                first += second
                self._lines.pop(line_ptr)
            else:
                line_ptr += 1
        return

    def transcribe_input(self, data: bytes):
        self._transcribe(Prefix.INPUT, data)

    def transcribe_output(self, data: bytes):
        self._transcribe(Prefix.OUTPUT, data)

    def transcribe_wait(self, data: float):
        line = LpstLine(Prefix.WAIT, Encoding.TIME, data)

    def get_next_input(self) -> bytes | int: # input bytes or wait time
        line = next(self._input_iter, None)
        if line is None:
            return Transcript.END_INPUT
        else:
            return line.get_data()

    def get_strs(self, *, times=False, argv=False) -> list[str]:
        lines = [line._to_str(times=times) for line in self._lines]
        if argv:
            argv_line = "$ " + " ".join(f"[{arg}]" for arg in self.argv)
            return [argv_line, *lines]
        else:
            return lines

    def print(self):
        print("--- LOOPSTATION: START TRANSCRIPT ---")
        print("$ " + " ".join([f"[{arg}]" for arg in self.argv]))
        for line in self._lines:
            line.print()
        print("--- LOOPSTATION: END TRANSCRIPT ---")

    # FAR TODO: compact save instead of json
    def save(self, filename: str):
        argv = [{'argv': self.argv}]
        dicts = argv + [line.dict() for line in self._lines]
        with open(filename, 'x') as f:
            json.dump(dicts, f, indent=2)

    def __eq__(self, other) -> bool:
        if self.argv != other.argv: return False
        return all([s == o for s, o in zip_longest(self._lines, other._lines)])
