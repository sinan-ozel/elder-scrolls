import struct
from .lib import _get_str, _get_int


class Field:
    header_size = 6

    def __init__(self, content: bytes):
        if len(content) < self.header_size:
            raise ValueError(f'Field content is too small: {len(content)}')
        self._pos = 0
        self.name = _get_str(content[0:4])
        self.size = _get_int(content[4:6])
        self.bytes = content[self.header_size:self.header_size + self.size]

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.bytes[item]
        elif isinstance(item, slice):
            return self.bytes[item]
        else:
            raise TypeError(f'Item must be an integer or slice, not {type(item)}')

    def __repr__(self):
        return f'{self.name}: {self.bytes}'

    def __hex__(self):
        return hex(_get_int(self.bytes))

    def __str__(self):
        return _get_str(self.bytes)

    def __int__(self):
        return _get_int(self.bytes)

    def __float__(self, offset=0):
        return struct.unpack('f', self.bytes)[0 + offset]

    def __len__(self):
        return self.header_size + self.size

    def __call__(self):
        if self.name in FIELD_TYPES:
            if isinstance(FIELD_TYPES[self.name], tuple):
                _pos = 0
                value = tuple()
                for _type in FIELD_TYPES[self.name]:
                    if _type == 'float32':
                        value.append(self.__float__(_pos))
                        _pos += 4
                    elif _type == 'uint32':
                        value.append(_get_int(self.bytes[_pos:_pos + 4]))
                        _pos += 4
                return value
            elif FIELD_TYPES[self.name] == 'zstring':
                return _get_str(self.bytes)
            else:
                raise NotImplementedError(f'Field type {self.name} is not implemented yet')
        else:
            return self.bytes

FIELD_TYPES = {
    'HEDR': ('float32', 'uint32', 'uint32'),
    'CNAM': 'zstring',
    'SNAM': 'zstring',
    'MAST': 'zstring',
    'EDID': 'zstring',
}