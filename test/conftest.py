import os
from configparser import ConfigParser

config = ConfigParser()
config.read('test.ini')

SKYRIM_FULL_PATH = os.path.join(config['Skyrim']['Folder'],
                                'Data',
                                'Skyrim.esm')
