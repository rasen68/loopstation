from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import StrEnum
import re

def _is_str(obj) -> bool:
    return isinstance(obj, str)

def _is_float(obj) -> bool:
    return isinstance(obj, float)

_HEX_RE = re.compile("[0-9a-f]*")

class Prefix(StrEnum):
    INPUT = "> "
    OUTPUT = "< "
    WAIT = "~ "

class Encoding(StrEnum):
    UTF = "u"
    HEX = "x"
    TIME = "t" # s

@dataclass
class LpstLine:
    prefix: str
    encoding: str
    data: str | float # float for time

    # called after @dataclass __init__
    def __post_init__(self):
        # assertions for wait and hex
        if self.is_wait():
            assert self.encoding == Encoding.TIME
            assert _is_float(self.data)
        else:
            assert _is_str(self.data)
            if self.encoding == Encoding.HEX:
                assert _HEX_RE.match(self.data)

    def _data_processed(self) -> str:
        # Escape backslashes so single backslash can mean no newline
        data = self.data.replace('\\', '\\\\')
        if self.data.endswith('\n'):
            data = data.removesuffix('\n')
        else:
            data += '\\'

        # Add prefix to newlines for nicer formatting
        data = data.replace('\n', '\n' + self.prefix)
        return data

    def get_data(self) -> bytes | int:
        match self.encoding:
            case Encoding.UTF:
                return self.data.encode()
            case Encoding.HEX:
                return bytes.fromhex(self.data)
            case _: # time
                return self.data

    def _to_str(self, times: bool=True) -> str:
        match self.encoding:
            case Encoding.TIME:
                if not times:
                    return ''
                data = str(round(self.data, 1))
            case _:
                data = self._data_processed()
        return str(self.encoding) + str(self.prefix) + data

    def __str__(self) -> str:
        return self._to_str()

    def __add__(self, other: LpstLine) -> LpstLine:
        assert self.prefix == other.prefix
        if self.encoding == other.encoding:
            data = self.data + other.data
            return LpstLine(self.prefix, self.encoding, data)
        else: # one of them is hex
            self_data = self.data if self.is_hex() else self.data.encode().hex()
            other_data = other.data if other.is_hex() else other.data.encode().hex()
            data = self_data + other_data
            return LpstLine(self.prefix, Encoding.HEX, data)

    def __iadd__(self, other: LpstLine):
        new_line = self + other
        self.encoding = new_line.encoding
        self.data = new_line.data

    def dict(self) -> dict[str, str | int]:
        return asdict(self)

    def print(self, times: bool=True):
        print(self._to_str(times))

    def is_input(self) -> bool:
        return self.prefix == Prefix.INPUT

    def is_wait(self) -> bool:
        return self.prefix == Prefix.WAIT

    def is_output(self) -> bool:
        return self.prefix == Prefix.OUTPUT

    def is_input_or_wait(self) -> bool:
        return self.is_input() or self.is_wait()

    def is_utf(self) -> bool:
        return self.encoding == Encoding.UTF

    def is_hex(self) -> bool:
        return self.encoding == Encoding.HEX
