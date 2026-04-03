from io import TextIOWrapper

class Transcript:
    def __init__(self, header: str):
        self.transcript = header + '\n'

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
            data_str = data_str[:-1].replace('\n', '\n'+prefix) + data_str[-1]

        self.transcript += data_str
        if not self.transcript.endswith('\n'):
            self.transcript += '\n\\'
        # Transcript now definitely ends with newline and maybe \

    def input_prefix(self):
        self.transcript += '> '
    def output_prefix(self):
        self.transcript += '[ '

    def print(self):
        print("--- LOOPSTATION: TRANSCRIPT ---")
        print(self.transcript)
        print("--- LOOPSTATION: END TRANSCRIPT ---")
    def save(self, file: TextIOWrapper):
        file.write(self.transcript)
