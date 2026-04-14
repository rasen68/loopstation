from io import TextIOWrapper

class Transcript:
    def __init__(self, header: str):
        if not header.endswith('\n'):
            header += '\n'
        self.transcript = header
        self.input_counter = 0
        self.input_lines = []

    def transcribe(self, data: bytes):
        # Transcript must end with lpst prefix ("[ " or "> ")
        # Parent loop is responsible for appending these
        data = data.replace(b'\r\n', b'\n')
        try:
            data_str = data.decode('utf-8')
        except UnicodeDecodeError:
            data_str = data.hex()
            self.transcript = self.transcript[:-2] + 'x' + self.transcript[-2:]
        else:
            # In non-hex mode, add prefix to newlines
            prefix = self.transcript[-2:]
            data_str = data_str[:-1].replace('\n', '\n'+prefix) + data_str[-1:]

        self.transcript += data_str
        if not self.transcript.endswith('\n'):
            self.transcript += '\n\\'
        # Transcript now definitely ends with newline and maybe \

    def input_prefix(self):
        self.transcript += '> '
    def output_prefix(self):
        self.transcript += '[ '

    def get_input_lines(self):
        if self.input_lines:
            return self.inputlines
        else:
            return [l for l in self.transcript.splitlines()
                    if '>' in l.split(' ')[0]]

    def get_next_input(self) -> bytes:
        if self.input_counter >= len(self.get_input_lines()):
            return b''
        line = self.get_input_lines()[self.input_counter]
        self.input_counter += 1
        prefix, ret = line.split(' ', maxsplit=1)
        ret += '\n'
        if 'x' in prefix:
            return bytes.fromhex(ret)
        else:
            return ret.encode()

    def print(self):
        print("--- LOOPSTATION: TRANSCRIPT ---")
        print(self.transcript)
        print("--- LOOPSTATION: END TRANSCRIPT ---")
    def save(self, file: TextIOWrapper):
        file.write(self.transcript)
