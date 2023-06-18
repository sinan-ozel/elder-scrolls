import mmap
import zlib
from typing import Union, Iterator

from .field import Field
from .lib import _get_bit, _get_int, _get_str

class Record:
    """A record is a block of data in a file. It has a header and a content."""
    header_size = 24

    def __init__(self, mmap: mmap.mmap, pointer: int):
        self._pointer = pointer
        self._mmap = mmap  # TODO: Use this to read the content of the record
        self._header = mmap[pointer:pointer + self.header_size]
        if self._header[0:4].decode('ascii') != 'GRUP':
            if self.__class__.__name__ == 'Group':
                raise TypeError(f'{self.__class__.__name__} cannot be initialized as Group.')
            self._field_positions = {}
            self._pos = {}
            self._is_parsing_complete = False
        else:
            if self.__class__.__name__ != 'Group':
                raise TypeError(f'Group record must be of type Group, not {self.__class__.__name__}.')

    @property
    def type(self):
        return self._header[0:4].decode('ascii')

    @property
    def size(self):
        return _get_int(self._header[4:8])

    def __len__(self):
        if self._is_parsing_complete:
            return len(self._pos)
        else:
            return len(self._get_all_fields())

    def __iter__(self):
        for field in self.get_all_fields():
            yield field

    def __getitem__(self, key: Union[str, slice]) -> bytes:
        if isinstance(key, slice):
            return self._mmap[key]
        if isinstance(key, str):
            if len(key) == 4 and key.upper() == key:
                return self.get_field(key)

    # TODO: Implement __setitem__ to allow changing the value of a field
    # TODO: Implement __enter__ and __exit__ to allow using the record in a with statement

    def __contains__(self, field: Union[Field, str]):
        if isinstance(field, Field):
            if self._is_parsing_complete:
                return field.name in self._field_positions
            else:
                return field.name in self.get_all_fields()
        elif isinstance(field, str):
            if self._is_parsing_complete:
                return field in self._field_positions
            else:
                return field in self.get_all_fields()

    def get_field(self, field_name: str) -> Field:
        try:
            return self._get_field_at_position(self._field_positions[field_name][0])
        except KeyError:
            if not self._is_parsing_complete:
                return self._get_field(field_name)
            else:
                raise KeyError(f'Field {field_name} not found in record.')

    def get_fields(self, field_name: str) -> Iterator[Field]:
        if field_name in self._field_positions:
            for pos in self._field_positions[field_name]:
                field = self._get_field_at_position(pos)
                yield field
            pos += Field.header_size + field.size
        else:
            pos = self._pointer + self.header_size
        if not self._is_parsing_complete:
            for field in self._get_fields(field_name, pos):
                yield field

    def get_all_fields(self) -> Iterator[Field]:
        if self._is_parsing_complete:
            for pos in self._pos:
                field = self._get_field_at_position(pos)
                yield field
        else:
            for field in self._get_all_fields():
                yield field

    @property
    def content(self) -> bytes:
        if self.is_compressed:
            try:
                return self._uncompressed_content
            except AttributeError:
                start = self._pointer + self.header_size + 4
                end = start + self.size
                self._uncompressed_content = zlib.decompress(self._mmap[start:end],
                                                             zlib.MAX_WBITS)
                return self._uncompressed_content
        else:
            try:
                return self._content
            except AttributeError:
                start = self._pointer + self.header_size
                end = start + self.size
                self._content = self._mmap[start:end]
                return self._content

    @property
    def editor_id(self):
        try:
            return str(self['EDID'])
        except KeyError:
            return None

    @property
    def full_name(self):
        try:
            return str(self['FULL'])
        except KeyError:
            return None

    @property
    def is_deleted(self):
        return self._get_flag(2)

    @property
    def is_disabled(self):
        return self._get_flag(8)

    @property
    def is_compressed(self):
        return self._get_flag(18)

    def _get_flag(self, bit):
        """Returns True if the flag is set, False if not."""
        return _get_bit(self._header[8:12], bit)

    def _get_field_at_position(self, position: int):
        field_size = _get_int(self._mmap[position + 4:position + 6])
        return Field(self._mmap[position:position + Field.header_size + field_size])

    def _register_field(self, field_name: str, position: int):
        if not self._is_parsing_complete and position not in self._pos:
            if field_name in self._field_positions:
                self._field_positions[field_name].append(position)
                self._pos[position] = field_name
            else:
                self._field_positions[field_name] = [position]
                self._pos[position] = field_name

    def _get_field(self, field_name: str) -> Field:
        _pos = self._pointer + self.header_size
        while _pos < self._pointer + self.header_size + self.size:
            field_name_at_pos = self._mmap[_pos:_pos + 4].decode('ascii')
            self._register_field(field_name_at_pos, _pos)
            field_size = _get_int(self._mmap[_pos + 4:_pos + 6])
            if field_name == field_name_at_pos:
                return Field(self._mmap[_pos:_pos + Field.header_size + field_size])
            _pos += Field.header_size + field_size
        self._is_parsing_complete = True


    def _get_fields(self, field_name: str, starting_position: int=None) -> Iterator[Field]:
        if starting_position is None:
            _pos = self._pointer + self.header_size
        else:
            _pos = starting_position
        while _pos < self._pointer + self.header_size + self.size:
            field_name_at_pos = self._mmap[_pos:_pos + 4].decode('ascii')
            self._register_field(field_name_at_pos, _pos)
            field_size = _get_int(self._mmap[_pos + 4:_pos + 6])
            if field_name == field_name_at_pos:
                yield Field(self._mmap[_pos:_pos + Field.header_size + field_size])
            _pos += Field.header_size + field_size
        if starting_position is None:
            self._is_parsing_complete = True

    def _get_all_fields(self) -> Iterator[Field]:
        _pos = self._pointer + self.header_size
        while _pos < self._pointer + self.header_size + self.size:
            field_name_at_pos = self._mmap[_pos:_pos + 4].decode('ascii')
            self._register_field(field_name_at_pos, _pos)
            field_size = _get_int(self._mmap[_pos + 4:_pos + 6])
            yield Field(self._mmap[_pos:_pos + Field.header_size + field_size])
            _pos += Field.header_size + field_size
        self._is_parsing_complete = True


class TES4(Record):

    @property
    def author(self):
        return str(self['CNAM'])

    @property
    def masters(self):
        try:
            return self._masters
        except AttributeError:
            self._masters = [str(master) for master in self.get_fields('MAST')]
            return self._masters

    @property
    def is_esm(self):
        return self._get_flag(0)

    @property
    def is_esl(self):
        return self._get_flag(9)


class NPC_(Record):

    @property
    def is_female(self):
        return self._get_bit(self.acbs, 0)

    @property
    def is_essential(self):
        return self._get_bit(self.acbs, 1)

    @property
    def is_preset(self):
        return self._get_bit(self.acbs, 2)

    @property
    def respawns(self):
        return self._get_bit(self.acbs, 3)

    @property
    def auto_calculate_stats(self):
        return self._get_bit(self.acbs, 4)

    @property
    def is_unique(self):
        return self._get_bit(self.acbs, 5)

    @property
    def is_levelling_up_with_pc(self):
        return self._get_bit(self.acbs, 7)

    @property
    def is_protected(self):
        return self._get_bit(self.acbs, 11)

    @property
    def is_summonable(self):
        return self._get_bit(self.acbs, 14)

    @property
    def has_opposite_gender_animations(self):
        return self._get_bit(self.acbs, 19)

    @property
    def is_ghost(self):
        return self._get_bit(self.acbs, 29)

    @property
    def is_invulnerable(self):
        return self._get_bit(self.acbs, 31)

    @property
    def level(self):
        if self.is_levelling_up_with_pc:
            divider = 1000
        else:
            divider = 1
        return int.from_bytes(self.acbs[8:10], 'little', signed=False) / divider

    @property
    def face_geom_file_name(self) -> str:
        return f'00{str(self.form_id.objectindex)[2:].rjust(8, "0")}.nif'

    def get_face_geom_path_name(self, mod_file_name: str) -> str:
        """Return the path under data for the FaceGenData mesh."""
        return '\\'.join(['Meshes',
                          'Actors',
                          'Character',
                          'FaceGenData',
                          'FaceGeom',
                          mod_file_name,
                          self.face_geom_file_name])

    @property
    def face_tint_file_name(self) -> str:
        return f'00{str(self.form_id.objectindex)[2:].rjust(8, "0")}.dds'

    def get_face_tint_path_name(self, mod_file_name: str) -> str:
        """Return the path under data for the FaceGenData mesh."""
        return '\\'.join(['Textures',
                          'Actors',
                          'Character',
                          'FaceGenData',
                          'FaceTint',
                          mod_file_name,
                          self.face_tint_file_name])


class BOOK(Record):
    pass