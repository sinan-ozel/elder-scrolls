import pytest
from elder_scrolls import ElderScrollsFile, Record
from .conftest import SKYRIM_FULL_PATH


def test_file_not_found():
    """Test if FileNotFoundError is raised when trying to open a file that does not exist."""
    with pytest.raises(FileNotFoundError):
        ElderScrollsFile('./esp/non_existent_file.esp')


def test_open_file():
    """Test if a file can be opened."""
    with ElderScrollsFile('./esp/test_basic_esp_functionality.esp') as test_file:
        print('First four characters in file: ', test_file[0:4])
        assert test_file[0:4] == b'TES4'


@pytest.mark.depends(on=['test_open_file'])
def test_record_parsing():
    with ElderScrollsFile('./esp/test_basic_esp_functionality.esp') as test_file:
        header_record = Record(test_file._mmap, 0)
        assert header_record._pointer == 0
        assert header_record.size == 215
        assert header_record.get_field('HEDR')
        assert header_record._is_parsing_complete == False
        assert header_record._pos == {24: 'HEDR'}
        assert header_record._field_positions == {'HEDR': [24]}

        header_record = Record(test_file._mmap, 0)
        assert 'Test Author' == str(header_record.get_field('CNAM'))
        assert header_record._is_parsing_complete == False
        assert header_record._pos == {24: 'HEDR', 42: 'CNAM'}
        assert header_record._field_positions == {'CNAM': [42], 'HEDR': [24]}

        header_record = Record(test_file._mmap, 0)
        assert ['Skyrim.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm'] == [str(f) for f in header_record.get_fields('MAST')]
        assert ['Skyrim.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm'] == [f() for f in header_record.get_fields('MAST')]

        header_record = Record(test_file._mmap, 0)
        assert 'Test Author' == str(header_record.get_field('CNAM'))
        assert ['Skyrim.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm'] == [str(f) for f in header_record.get_fields('MAST')]

        header_record = Record(test_file._mmap, 0)
        expected_fields = ['HEDR', 'CNAM', 'SNAM', 'MAST', 'DATA', 'MAST', 'DATA', 'MAST', 'DATA', 'MAST', 'DATA']
        expected_positions = {24: 'HEDR', 42: 'CNAM', 60: 'SNAM', 103: 'MAST', 120: 'DATA', 134: 'MAST', 154: 'DATA', 168: 'MAST', 190: 'DATA', 204: 'MAST', 225: 'DATA'}
        expected_field_positions = {'HEDR': [24], 'CNAM': [42], 'SNAM': [60], 'MAST': [103, 134, 168, 204], 'DATA': [120, 154, 190, 225]}

        header_record = Record(test_file._mmap, 0)
        assert header_record._is_parsing_complete == False
        assert expected_fields == [f.name for f in header_record._get_all_fields()]
        assert header_record._is_parsing_complete == True
        assert header_record._pos == expected_positions
        assert header_record._field_positions == expected_field_positions

        header_record = Record(test_file._mmap, 0)
        assert header_record._is_parsing_complete == False
        assert expected_fields == [f.name for f in header_record.get_all_fields()]
        assert header_record._is_parsing_complete == True
        assert len(header_record._pos) == 11
        assert expected_fields == [f.name for f in header_record.get_all_fields()]
        assert len(header_record._pos) == 11
        assert expected_fields == [f.name for f in header_record.get_all_fields()]
        assert len(header_record._pos) == 11

        header_record = Record(test_file._mmap, 0)
        assert expected_fields == [f.name for f in header_record]


@pytest.mark.depends(on=['test_record_parsing'])
def test_fields():
    with ElderScrollsFile('./esp/test_basic_esp_functionality.esp') as test_file:
        header_record = Record(test_file._mmap, 0)
        field = header_record.get_field('HEDR')
        assert field.name == 'HEDR'
        assert field.size == 12
        assert str(field) == 'š™Ù?"\x00\x00\x00\n\x08'


@pytest.mark.depends(on=['test_record_parsing'])
def test_header_record():
    with ElderScrollsFile('./esp/test_basic_esp_functionality.esp') as test_file:
        assert hasattr(test_file, 'header_record')
        assert test_file.header_record._pointer == 0
        assert test_file.header_record.size == 215
        assert test_file.header_record.author == 'Test Author'
        assert test_file.header_record.masters == ['Skyrim.esm', 'Dawnguard.esm', 'HearthFires.esm', 'Dragonborn.esm']
        assert test_file.header_record.is_esl == True
        assert test_file.header_record.is_esm == False

        assert test_file.author == test_file.header_record.author
        assert test_file.masters == test_file.header_record.masters
        assert test_file.record_count == 34


@pytest.mark.depends(on=['test_header_record', 'test_fields'])
def test_records():
    with ElderScrollsFile('./esp/test_basic_esp_functionality.esp') as test_file:
        records = [r for r in test_file._get_all_records()]
        expected_record_types = {'TES4', 'BOOK', 'NPC_', 'TXST',
                                 'ARMO', 'DIAL', 'KYWD', 'ARMA', 'INGR',
                                 'LVLI', 'QUST', 'WEAP', 'OTFT'}
        assert expected_record_types == {r.type for r in records}
        for record in records:
            print(record.type, record.is_compressed, end=' ')
            print(record.editor_id)
            for field in record:
                print('    ', field.name, field.bytes)
        assert expected_record_types == {r.editor_id for r in records}
        assert len(records) == test_file.record_count
        assert False


@pytest.mark.depends(on=['test_open_file'])
def test_skyrim_esm():
    with ElderScrollsFile(SKYRIM_FULL_PATH) as test_file:
        print('Records in file:', test_file.record_types)
        assert {'TREE', 'BOOK', 'NPC_'} <= test_file.record_types
        for record_type in test_file.record_types:
            print(record_type)
            assert is_type(record_type)