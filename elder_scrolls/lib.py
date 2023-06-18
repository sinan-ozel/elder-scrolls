import os
import mmap

STRING_ENCODINGS = ['utf-8', 'windows-1252']

def _get_bit(longword: bytes, bit: int):
    try:
        return bool(int.from_bytes(longword, 'little', signed=False) & 2 ** bit)
    except TypeError:
        if longword is None:
            return None


def _get_int(content: bytes):
    return int.from_bytes(content, 'little', signed=False)


def _get_str(content: bytes, encoding='utf-8'):
    for encoding in STRING_ENCODINGS:
        try:
            return content.decode(encoding).strip('\0')
        except UnicodeDecodeError:
            pass


class Loader:
    """Base class for reading binary files."""
    def __init__(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self._file = open(self.file_path, 'rb')
        self._mmap = mmap.mmap(self._file.fileno(), length=0, access=mmap.ACCESS_READ)

    def _read_bytes(self, pos: int, length: int=1) -> bytes:
        self._mmap.seek(pos)
        return self._mmap.read(length)

    def _read_string(self, _pos, encoding='utf-8'):
        _bytes = self._read_bytes(_pos)
        while _bytes[-1] != 0:
            _pos += 1
            _bytes += self._read_bytes(_pos)

        return _bytes[:-1].decode(encoding)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_val, trace):
        self._file.close()
