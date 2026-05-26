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

    @classmethod
    def load(cls, file) -> Transcript:
        dicts = json.load(file)
        argv = dicts[0]['argv']
        transcript = cls(argv)
        for d in dicts[1:]:
            transcript._lines.append(LpstLine(**d))
        transcript._init_iters()
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

    def transcribe_input(self, data: bytes):
        self._transcribe(Prefix.INPUT, data)

    def transcribe_output(self, data: bytes):
        self._transcribe(Prefix.OUTPUT, data)

    def _init_iters(self):
        self._input_iter = (l for l in self._lines if l.is_input_or_wait())
        self._output_iter = (l for l in self._lines if l.is_output())

    def get_next_input(self) -> bytes | int: # input bytes or wait time
        line = next(self._input_iter, None)
        if line is None:
            return Transcript.END_INPUT
        else:
            return line.get_data()

    def get_strs(self) -> list[str]:
        return [line._to_str(times=False) for line in self._lines]

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
    '''
        input_queue, output_queue = b"", b""
        for line in self._lines:
            match line.
            if line.is_input():
                if 
    '''
