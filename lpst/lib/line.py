from dataclasses import dataclass, asdict
from enum import StrEnum
import re

def _is_str(obj) -> bool:
    return isinstance(obj, str)

def _is_int(obj) -> bool:
    return isinstance(obj, int)

_HEX_RE = re.compile("[0-9a-f]*")

class Prefix(StrEnum):
    INPUT = "> "
    OUTPUT = "< "
    WAIT = "~ " # TODO: record wait

class Encoding(StrEnum):
    UTF = "u"
    HEX = "x"
    TIME = "t" # ms

@dataclass
class LpstLine:
    prefix: str
    encoding: str
    data: str | int # int for time

    # called after @dataclass __init__
    def __post_init__(self):
        # assertions for wait and hex
        if self.is_wait():
            assert self.encoding == Encoding.TIME
            assert _is_int(self.data)
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
                data = str(round(self.data, 1)) + '\n'
            case _:
                data = self._data_processed()
        return str(self.encoding) + str(self.prefix) + data

    def __str__(self) -> str:
        return self._to_str()

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
