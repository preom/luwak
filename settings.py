#!/usr/bin/python

import json

import unittest
import os

import logging

logger = logging.getLogger('settingsLogger')

class Settings(object):

    CONFIG_FILENAME = 'luwak.rc'
    
    default_data = {
        'output_dir': 'output',
        'source_dir': 'content',
        'tags_dir': 'tags',
        'project_path': '',
        'db_name': 'main_db.sqlite3'
    }

    def __init__(self):
        self.settings_data = self.default_data

    def validate(self, dirPath, fixErrors=True):
        """ Validate a settings file.

            Attributes:
                dirPath (str): Absolute path to the root of the project directory.
                fixErrors (bool): Try and fix any erros found. Defaults to True.

            Returns:
                bool: True if everything is ok, False otherwise. 

        """
        file_path = self.generate_settings_file(dirPath)
        settings = self.get_settings_file(dirPath)

        msgPreamble = "Settings Validation: \n"
        msg = "{preamble}{reason}\n"

        if settings['project_path'] != dirPath:
            msgReason = 'Wrong project path - fixing to correct path.'
            logger.info(msg.format(preamble=msgPreamble, reason=msgReason))

            settings['project_path'] = dirPath

        self.update_settings_file(dirPath, settings)


    def get_settings_file(self, dirPath):
        """ Return a json settings file. 

        """
        file_path = self.generate_settings_file(dirPath)

        with open(file_path, 'r') as f:
            return json.loads(f.read())

    def update_settings_file(self, dirPath, contents):
        """ Update a json settings file.

        """
        file_path = self.generate_settings_file(dirPath)

        with open(file_path, 'w') as f:
            f.write(json.dumps(contents, 
                               sort_keys=True,
                               indent=4,
                               separators=(',', ': ')))

    def generate_settings_file(self, dirPath):
        """ Return the settings filepath. 

        """
        return os.path.join(dirPath, Settings.CONFIG_FILENAME)

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
