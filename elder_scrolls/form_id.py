class FormId:
    # TODO: Implement __index__
    # TODO: Implement __format__
    def __init__(self, byte):
        if not isinstance(byte, (bytes, str)):
            raise ValueError("Use a string or byte object to instantiate a Form ID.")
        if isinstance(byte, str):
            if byte[:2] != '0x':
                raise ValueError("When creating a Form ID with a string, use a hexadecimal value. For examle: FormId('0x13bab')")
            if len(byte) > 8:
                self._bytes = int(byte, 16).to_bytes(4, byteorder='little')
            else:
                self._bytes = int(byte, 16).to_bytes(3, byteorder='little')
        else:
            if not len(byte) <= 4:
                raise ValueError("Form IDs have to have the length 4 bytes or less.")
            self._bytes = byte

    def __getitem__(self, key):
        return self._bytes[key]

    def __int__(self):
        return int.from_bytes(self._bytes, 'little', signed=False)

    def __index__(self):
        return int.from_bytes(self._bytes, 'little', signed=False)

    def __hex__(self):
        return hex(int.from_bytes(self._bytes, 'little', signed=False))

    def __str__(self):
        return str(hex(int.from_bytes(self._bytes, 'little', signed=False)))

    def __len__(self):
        return len(self._bytes)

    def __eq__(self, other):
        if isinstance(other, FormId):
            return self._bytes == other._bytes
        elif isinstance(other, str):
            # TODO: Add unit test.
            if other.startswith('0x'):
                return str(self)[2:] == other[2:].lstrip('0')
            else:
                return str(self)[2:] == other.lstrip('0')

    @property
    def modindex(self) -> bytes:
        if len(self) == 4:
            return self._bytes[-1]

    @property
    def objectindex(self):
        if len(self) == 4:
            return FormId(self._bytes[:-1])
        else:
            return self
