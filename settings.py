#!/usr/bin/python

import json

import unittest
import os

class Settings(object):

    CONFIG_FILENAME = 'luwak.rc'
    
    default_data = {
        'output_dir': 'output',
        'source_dir': 'content',
        'project_path': ''
    }

    def __init__(self):
        self.settings_data = self.default_data

    def genrate_settings_file(self):
        pass

    @staticmethod
    def generate_default_settings_file(dir_path=None):
        if not dir_path:
            dir_path = os.getcwd()

        file_path = os.path.join(dir_path, Settings.CONFIG_FILENAME)

        with open(file_path, 'w') as f:
            settings = Settings.default_data
            settings['project_path'] = os.path.abspath(dir_path)

            f.write(json.dumps(Settings.default_data, 
                               sort_keys=True,
                               indent=4,
                               separators=(',', ': ')))

class SettingsReader(object):
    pass

class SettingsTest(unittest.TestCase):
    
    def test_default_file_generation(self):
        Settings.generate_default_settings_file('output')

if __name__ == '__main__':
    unittest.main()

