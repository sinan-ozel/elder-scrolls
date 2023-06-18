from typing import Iterator

from .lib import Loader, _get_int
from .record import Record, TES4
from .group import Group


class ElderScrollsFile(Loader):
    """Parse a ESM/P/L file.

    Usage examples:

    from elder_scrolls import ElderScrollsFile

    with ElderScrollsFile(os.path.join(game_folder, 'Data', 'Skyrim.esm')) as skyrim_main_file:
        print(len(skyrim_main_file['BOOK']))  # print the number of BOOK records.

        print(skyrim_main_file.record_types)  # print types of records in file.

        for npc in skyrim_main_file['NPC_']:
            print(npc.form_id)  # Print form IDs of all NPCs.

        print(skyrim_main_file[0x1033ee])  # Return the record with the form ID 0x1033ee
    """

    def __init__(self, file_path):
        super().__init__(file_path)
        try:
            assert self._read_bytes(0, 4) == b'TES4'
        except AssertionError:
            raise RuntimeError('Incorrect file header - is this a TES4 file?')
        self.header_record = TES4(self._mmap, 0)
        self.is_esm = self.header_record.is_esm
        self.is_esl = self.header_record.is_esl
        self.masters = self.header_record.masters
        self.author = self.header_record.author
        self.record_count = _get_int(self.header_record['HEDR'][4:8])
        self._record_positions = {}
        self._pos = {}

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise KeyError(f'{self.__class__.__name__} does not allow slicing '
                                'with a step. Use only one colon in slice, for example: [0:4]')
            return self._read_bytes(key.start, key.stop - key.start)
        elif isinstance(key, int):
            raise NotImplementedError
        elif isinstance(key, Record):
            raise NotImplementedError
        elif isinstance(key, str):
            if len(key) == 4:
                return [record for record in self.records.values() if record.type == key]
            elif key[:2] == '0x':
                raise NotImplementedError
        else:
            raise KeyError

    def _get_type_at_position(self, pos: int) -> str:
        return self._mmap[pos:pos + 4].decode('ascii')

    def _get_record_at_position(self, pos: int) -> Record:
        return Record(self._mmap, pos)


    def _get_records_by_type(self, record_type: str, starting_position: int=0) -> Record:
        _pos = starting_position
        while _pos < len(self._mmap):
            if self._get_type_at_position(_pos) == 'GRUP':
                group = Group(self._mmap, _pos)
                print("=== GRUP ===", group.type, group.label)
                if group.is_top_level and group.label == record_type:
                    for record in group._get_all_records():
                        print(record.type)
                        yield record
                        _pos += record.size + record.header_size
                else:
                    _pos += group.size

            else:
                record = Record(self._mmap, _pos)
                print(record.type)
                if record.type == record_type:
                    yield record
                _pos += record.size + record.header_size


    def _get_all_records(self, starting_position: int=0) -> Record:
        _pos = starting_position
        while _pos < len(self._mmap):
            if self._get_type_at_position(_pos) == 'GRUP':
                group = Group(self._mmap, _pos)
                if group.is_top_level:
                    for record in group._get_all_records():
                        yield record
                _pos += group.size
            else:
                record = Record(self._mmap, _pos)
                yield record
                _pos += record.size + record.header_size
