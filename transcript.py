from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import StrEnum
from copy import copy
import json

class Prefix(StrEnum):
    INPUT = "> "
    OUTPUT = "< "
    WAIT = "~ " # TODO: implement wait

class Encoding(StrEnum):
    UTF = "u"
    HEX = "x"
    TIME = "t" # seconds

@dataclass
class LpstLine:
    prefix: str
    encoding: str
    data: str | int # int for time

    def get_data(self) -> bytes | int:
        match self.encoding:
            case Encoding.UTF:
                return self.data.encode()
            case Encoding.HEX:
                return bytes.fromhex(self.data)
            case _: # time
                return self.data

    def data_to_str(self) -> str:
        match self.encoding:
            case Encoding.TIME:
                return str(round(self.data, 1)) + '\n'
            case _:
                # We escape backslashes, then add a single backslash if
                # no newline - an odd number of trailing backslashes
                # could only be this LpstLine-appended no newline marker
                data = self.data.replace('\\', '\\\\')
                if not data.endswith('\n'): data += '\\\n'
                return data

    def __str__(self):
        return str(self.encoding) + str(self.prefix) + self.data_to_str()

    def is_input(self) -> bool:
        # waits are inputs for us
        return self.prefix == Prefix.INPUT or self.prefix == Prefix.WAIT

class Transcript:
    argv: list[str]
    _lines: list[LpstLine]
    _input_iter: iter[LpstLine] | None
    END_INPUT = -1

    def __init__(self, argv: list[str]):
        ''' * argv: all transcripts start with an executable '''
        self.argv = argv
        self._lines = []
        self._input_iter = None

    @classmethod
    def load(cls, file):
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
            data_str = data.decode('utf-8')
        except UnicodeDecodeError:
            data_str = data.hex()
            line.encoding = Encoding.HEX
        line.data = data_str
        self._lines.append(line)

    def transcribe_input(self, data: bytes):
        self._transcribe(Prefix.INPUT, data)

    def transcribe_output(self, data: bytes):
        self._transcribe(Prefix.OUTPUT, data)

    # TODO: maybe a better way to do this, like a class hierarchy
    # between loaded and recorded transcripts?
    def _init_iters(self):
        self._input_iter = (l for l in self._lines if l.is_input())

    def get_next_input(self) -> bytes | int: # input bytes or wait time
        line = next(self._input_iter, None)
        if line is None:
            return Transcript.END_INPUT
        else:
            return line.get_data()

    def print(self):
        print("--- LOOPSTATION: START TRANSCRIPT ---")
        print(" ".join([f"[{arg}]" for arg in self.argv]))
        for line in self._lines:
            print(str(line), end='')
        print("--- LOOPSTATION: END TRANSCRIPT ---")

    # TODO: take path instead
    # FAR TODO: compact save instead of json
    def save(self, file: TextIOWrapper):
        argv = [{'argv': self.argv}]
        dicts = argv + [asdict(line) for line in self._lines]
        json.dump(dicts, file, indent=2)

    def __eq__(self, other):
        return all([s == o for s, o in zip(self._lines, other._lines)])
