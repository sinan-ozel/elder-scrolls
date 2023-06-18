
from .lib import Loader


class BethesdaSoftwareArchive(Loader):
    """Parse a v104/105 (Skyrim) BSA File."""

    file_record_length = 16

    class path:
        @staticmethod
        def parse(path_string):
            return path_string.replace('/', '\\').lower()

        @staticmethod
        def join(split_path):
            return '\\'.join(split_path)

        @staticmethod
        def is_folder(path_string):
            return ('\\' in path_string) and ('.' in path_string)

        @staticmethod
        def is_file(path_string):
            return not super().is_folder_path(path_string)

    class Folder:
        def __init__(self, folder_index, folder_name, folder_record):
            folder_hash = BethesdaSoftwareArchive._calculate_hash(folder_name)
            if folder_hash != folder_record['hash']:
                raise ValueError(f'Folder name {folder_name} resolves to the hash {folder_hash}, '
                                 f'but the hash in the folder record is {folder_record["hash"]}')
            self.name = folder_name
            self.index = folder_index
            self._hash = folder_record['hash']
            self._file_count = folder_record['file_count']
            self._offset = folder_record['offset']

        def __len__(self):
            return self._file_count

        def __repr__(self):
            return {
                'hash': self._hash,
                'file_count': self._file_count,
                'offset': self._offset
            }

        def __int__(self):
            return self._hash

        def __str__(self):
            return self.name

        def __iter__(self):
            for file_name in self._file_names:
                yield file_name

        def __contains__(self, item):
            if isinstance(item, str):
                return item.lower() in self._file_names
            else:
                raise TypeError(f'BSA folder contains filenames only. Expected: string. Got: {type(item)}')

        # TODO: __getitem__

        @property
        def record(self):
            return {
                'hash': self._hash,
                'file_count': self._file_count,
                'offset': self._offset
            }

    def __enter__(self):
        self._file = open(self.file_path, 'rb')
        try:
            assert self._read_bytes(0, 4) == b'BSA\x00'
        except AssertionError:
            raise RuntimeError(f'Incorrect file header - is {self.file_path} a BSA file?')

        if self.version == 104:
            self.folder_record_length = 16
        elif self.version == 105:
            self.folder_record_length = 24
        else:
            raise RuntimeError(f'Unknown BSA file version: {self.version}')
        self._load_folder_records()
        self._load_folder_filenames()
        # TODO: Add __len__
        # TODO: Add __iter__ ?
        return self

    def __exit__(self, exception_type, exception_val, trace):
        self._file.close()

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise KeyError(f'{self.__class__.__name__} does not allow slicing '
                                'with a step. Use only one colon in slice, for example: [0:4]')
            return self._read_bytes(key.start, key.stop - key.start)
        elif isinstance(key, tuple):
            if len(key) >= 2 and [isinstance(key_part, str) for key_part in key]:
                return self._read_file_by_name(self.path.parse(key[0]), self.path.parse('\\'.join(key[1:])))
            else:
                raise KeyError(f"{self.__class__.__name__} allows tuple of two strings to return "
                                "a file by folder and file name. Example: ['Strings', 'Skyrim_en.dlstrings']")
        elif isinstance(key, str):
            if '.' in key:
                key = key.replace('/', '\\').split('\\')
                return self._read_file_by_name(self.path.parse(key[0]), self.path.parse('\\'.join(key[1:])))
            else:
                return self._get_folder(self.path.parse(key))
        elif isinstance(key, int):
            return self._get_folder_by_hash(key)
        else:
            raise KeyError

    def __contains__(self, key):
        if isinstance(key, tuple):
            if len(key) >= 2 and [isinstance(key_part, str) for key_part in key]:
                return bool(self._get_file_index(self.path.parse(key[0]), self.path.parse('\\'.join(key[1:]))))
            else:
                raise KeyError(f"{self.__class__.__name__} allows tuple of two strings to return "
                                "a file by folder and file name. Example: ['Strings', 'Skyrim_en.dlstrings']")
        if isinstance(key, int):
            return key in self._folders
        elif isinstance(key, str):
            hash = self._calculate_hash(self.path.parse(key))
            return hash in self._folders
            # TODO: Add files and full paths.
        else:
            raise NotImplementedError

    def _load_folder_records(self):
        self._folders = {}
        for idx in range(self.folder_count):
            folder_name = self._get_folder_name_by_index(idx)
            folder_record = self._get_folder_record_by_index(idx)
            self._folders[folder_record['hash']] = self.Folder(idx, folder_name, folder_record)

    def _load_folder_filenames(self):
        file_names = self._get_file_names()
        self._folder_filenames = {}
        i = 0
        for folder_hash in self._folders:
            self._folders[folder_hash]._file_names = []
            while len(self._folders[folder_hash]._file_names) < self._folders[folder_hash]._file_count:
                self._folders[folder_hash]._file_names += [file_names[i]]
                i += 1
        if i != len(file_names):
            raise RuntimeError(f"Following files are not in a folder: {file_names[i:]}")

    def _get_file_index(self, folder_name, file_name):
        folder_hash = self._calculate_hash(folder_name)
        try:
            return self._folders[folder_hash]._file_names.index(file_name.lower())
        except ValueError:
            raise FileNotFoundError(f"The file `{file_name}` not found under the folder `{folder_name}` in the BSA archive: {self.file_name}.")

    def _read_file_by_name(self, folder_name, file_name):
        file_record = self._get_file_record_by_name(folder_name, file_name)
        file_offset = file_record['offset']
        file_size = file_record['size']
        print(self[file_offset - 12:file_offset], self[file_offset:file_offset + 12])
        if self.are_file_names_embedded:
            raise NotImplementedError
        if file_record['is_compressed']:
            raise NotImplementedError
        return self[file_offset:file_offset + file_size]


    @staticmethod
    def _get_bit(longword: bytes, bit: int):
        try:
            return bool(int.from_bytes(longword, 'little', signed=False) & 2 ** bit)
        except TypeError:
            if longword is None:
                return None

    def _get_folder_record_by_index(self, idx):
        _pos = self.offset + idx * self.folder_record_length
        _bytes = self[_pos:_pos + self.folder_record_length]
        _pos_for_offset = 16 if self.version >= 105 else 12
        return {
            'hash': int.from_bytes(_bytes[0:8], 'little', signed=False),
            'file_count': int.from_bytes(_bytes[8:12], 'little', signed=False),
            'offset': int.from_bytes(_bytes[_pos_for_offset:_pos_for_offset + 4], 'little', signed=False),
        }

    def _get_folder_name_by_index(self, idx):
        offset = self._get_folder_record_by_index(idx)['offset']
        return self._read_string(offset - self.total_file_name_length + 1)

    def _get_file_names(self):
        last_folder_index = self.folder_count - 1
        last_folder_offset = self._get_folder_record_by_index(last_folder_index)['offset']
        last_folder_file_count = self._get_folder_record_by_index(last_folder_index)['file_count']
        file_count = 0
        for idx in range(self.folder_count):
            file_count += self._get_folder_record_by_index(idx)['file_count']
        last_folder_name = self._read_string(last_folder_offset - self.total_file_name_length + 1)
        file_name_list_offset = last_folder_offset - self.total_file_name_length + 1 + len(last_folder_name) + 1 + last_folder_file_count * self.file_record_length
        file_names = []
        while len(file_names) < file_count:
            file_name = self._read_string(file_name_list_offset)
            file_name_list_offset += len(file_name) + 1
            file_names += [file_name]
        if len(file_names) != self.file_count:
            raise RuntimeError(f"File count in the header is {self.file_count} but the list of file names is {len(file_names)}")
        return file_names

    # def _get_files_in_folder_by_index(self, folder_idx):
    #     folder_record = self._get_folder_record_by_index(folder_idx)
    #     file_count = folder_record['file_count']
    #     for file_idx in range(file_count):
    #         yield self._read_file_record_by_index(folder_idx, file_idx)

    def _read_file_record_bytes(self, folder_idx):
        folder_offset = self._get_folder_record_by_index(folder_idx)['offset']
        folder_name = self._read_string(folder_offset - self.total_file_name_length + 1)
        file_count = self._get_folder_record_by_index(folder_idx)['file_count']
        file_offset = folder_offset - self.total_file_name_length + 1 + len(folder_name) + 1 + file_count * self.file_record_length
        _bytes = self[file_offset:file_offset + self.file_record_length]
        return _bytes

    def _read_file_record_bytes_by_index(self, folder_idx, file_idx):
        folder_offset = self._get_folder_record_by_index(folder_idx)['offset']
        folder_name = self._read_string(folder_offset - self.total_file_name_length + 1)
        file_offset = folder_offset - self.total_file_name_length + 1 + len(folder_name) + 1 + file_idx * self.file_record_length
        _bytes = self[file_offset:file_offset + self.file_record_length]
        assert len(_bytes) == 16
        return _bytes

    def _read_file_record_by_index(self, folder_idx, file_idx):
        _bytes = self._read_file_record_bytes_by_index(folder_idx, file_idx)
        return {
            'hash': int.from_bytes(_bytes[0:8], 'little', signed=False),
            'size': int.from_bytes(_bytes[8:12], 'little', signed=False),
            'is_compressed': self._get_bit(_bytes[8:12], 29) ^ self.is_compressed_by_default,
            'offset': int.from_bytes(_bytes[12:16], 'little', signed=False),
        }

    def _get_file_record_by_name(self, folder_name, file_name):
        folder = self[folder_name]
        file_idx = self._get_file_index(folder_name, file_name)
        file_record = self._read_file_record_by_index(folder.index, file_idx)
        return file_record

    @property
    def folders(self):
        return list(self._folders.values())

    @property
    def folder_names(self):
        return [folder.name for folder in self._folders.values()]

    @staticmethod
    def _calculate_hash(path):
        """Returns tes4's two hash values for filename.

        Based on the code found at: https://en.uesp.net/wiki/Oblivion_Mod:Hash_Calculation

        In turn, based on TimeSlips code with cleanup and pythonization.
        """
        extensions = {'.kf': 0x80, '.nif': 0x8000, '.dds': 0x8080, '.wav': 0x80000000}
        path = path.lower()
        if any([path.endswith(ext) for ext in extensions]):
            ext = '.' + path.lower().split('.')[-1]
            base = path[:-len(ext)]
        else:
            ext = ''
            base = path

        chars = list(map(ord, base))
        hash1 = chars[-1] | (chars[-2] if len(chars) > 2 else 0) << 8 | len(chars) << 16 | chars[0] << 24
        if ext in extensions:
            hash1 |= extensions[ext]

        uint, hash2, hash3 = 0xffffffff, 0 , 0
        for char in chars[1:-2]:
            hash2 = ((hash2 * 0x1003F) + char ) & uint

        for char in ext:
            hash3 = ((hash3 * 0x1003F) + ord(char)) & uint

        hash2 = (hash2 + hash3) & uint

        return (hash2<<32) + hash1


    def _get_folder_by_hash(self, hash):
        return self._folders.get(hash)


    def _get_folder(self, folder_name):
        folder_name = folder_name.lower()
        folder_name = folder_name.strip('\\')
        hash = self._calculate_hash(folder_name)
        if hash not in self._folders:
            raise FileNotFoundError(f'Folder `{folder_name}` not found in the BSA archive: {self.file_name}')
        return self._get_folder_by_hash(hash)


    @property
    def version(self):
        return int.from_bytes(self[4:8], 'little', signed=False)

    @property
    def offset(self):
        return int.from_bytes(self[8:12], 'little', signed=False)

    @property
    def folder_count(self):
        return int.from_bytes(self[16:20], 'little', signed=False)

    @property
    def file_count(self):
        return int.from_bytes(self[20:24], 'little', signed=False)

    @property
    def total_folder_name_length(self):
        return int.from_bytes(self[24:28], 'little', signed=False)

    @property
    def total_file_name_length(self):
        return int.from_bytes(self[28:32], 'little', signed=False)

    @property
    def has_folder_names(self):
        return self._get_bit(self[12:16], 0)

    @property
    def has_file_names(self):
        return self._get_bit(self[12:16], 1)

    @property
    def is_compressed_by_default(self):
        return self._get_bit(self[12:16], 2)

    @property
    def are_file_names_embedded(self):
        return self._get_bit(self[12:16], 8)

    @property
    def contains_meshes(self):
        return self._get_bit(self[30:32], 0)

    @property
    def contains_textures(self):
        return self._get_bit(self[30:32], 1)


