from typing import Iterable
import mmap

from .record import Record
from .lib import _get_int


class Group(Record):
    def __init__(self, mmap: mmap.mmap, pointer: int):
        super().__init__(mmap, pointer)
        if self._header[0:4].decode('ascii') != 'GRUP':
            raise TypeError(f'Group record must have the type GRUP.')

    @property
    def label(self):
        if self.type == 0:
            return self._header[8:12].decode('ascii')
        elif self.type in [1, 6, 7, 8, 9]:
            raise NotImplementedError('Group label is only available for top-level groups.')
            # TODO: Return a FormID
        else:
            raise NotImplementedError('Group label is only available for top-level groups.')

    @property
    def type(self):
        return _get_int(self._header[12:16])

    @property
    def version(self):
        return int.from_bytes(self._header[18:20], 'little', signed=False)

    @property
    def is_top_level(self):
        return self.type == 0

    def _get_all_records(self, starting_pointer: int=0) -> Iterable[Record]:
        pointer = self._pointer + self.header_size + starting_pointer
        while pointer < self._pointer + self.size:
            if self._mmap[pointer:pointer + 4].decode('ascii') == 'GRUP':
                group = Group(self._mmap, pointer)
                if group.is_top_level:
                    yield from group._get_all_records()
                pointer += group.size
            else:
                record = Record(self._mmap, pointer)
                yield record
                pointer += record.size + Record.header_size
