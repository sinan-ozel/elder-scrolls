"""A module to read and edit TES (The Elder Scrolls) files.

Usage Example - Print Form IDs of all top-level NPC records in Skyrim.esm
    from elder_scrolls import ElderScrollsFileLoader

    game_folder = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Skyrim Special Edition\\'

    with ElderScrollsFileLoader(os.path.join(game_folder, 'Data', 'Skyrim.esm')) as skyrim_main_file:
        for npc in skyrim_main_file['NPC_']:
            print(npc.form_id)


Credits: This code is mainly written from the YouTube stream found at https://www.youtube.com/watch?v=w5TLMn5l0g0
and the explanation on the Wiki page: https://en.uesp.net/wiki/Skyrim_Mod:Mod_File_Format
"""
__version__ = '1.0.0'
__author__ = 'Sinan Ozel'


from .elder_scrolls_file import ElderScrollsFile
from .record import Record, TES4
from .field import Field