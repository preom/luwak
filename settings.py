#!/usr/bin/python

import json
import unittest
import os
import sys

import logging

logger = logging.getLogger('settingsLogger')


CONFIG_FILENAME = 'luwak.rc'

default_data = {
    'output_dir': 'output',
    'source_dir': 'content',
    'tags_dir': 'tags',
    'project_path': '',
    'db_name': 'main_db.sqlite3'
}

def generate_default_settings_file(dir_path=None):
    if not dir_path:
        dir_path = os.getcwd()

    file_path = os.path.join(dir_path, CONFIG_FILENAME)

    with open(file_path, 'w') as f:
        settings = default_data
        settings['project_path'] = os.path.abspath(dir_path)

        f.write(json.dumps(default_data, 
                           sort_keys=True,
                           indent=4,
                           separators=(',', ': ')))


def validate(dirPath, fixErrors=True):
    """ Validate a settings file.

        Attributes:
            dirPath (str): Absolute path to the root of the project directory.
            fixErrors (bool): Try and fix any erros found. Defaults to True.

        Returns:
            bool: True if everything is ok, False otherwise. 

    """
    settings = get_settings_file(dirPath)
    errors = False

    msgPreamble = "Settings Validation: \n"
    msg = "{preamble}{reason}\n"

    if settings['project_path'] != dirPath:
        errors = True
        msgReason = 'Wrong project path - fixing to correct path.'
        logger.info(msg.format(preamble=msgPreamble, reason=msgReason))

        settings['project_path'] = dirPath

    if errors and fixErrors:
        update_settings_file(dirPath, settings)

def get_settings_file(dirPath):
    """ Return a json settings file. 

    """
    file_path = get_settings_filepath(dirPath)

    try:
        with open(file_path, 'r') as f:
            return json.loads(f.read())
    except IOError:
        config_access_error()

def config_access_error():
        print ''
        print " >>> ----------------------------- <<< "
        print " >>> Error loading the config file <<< "
        print " >>> ----------------------------- <<< "
        sys.exit(0) 

def get_settings_filepath(dirPath):
    """ Return the settings filepath. 

    """
    return os.path.join(dirPath, CONFIG_FILENAME)

def update_settings_file(dirPath, contents):
    """ Update a json settings file.

    Attributes:
        contents (dict): Settings file.

    """
    file_path = get_settings_filepath(dirPath)

    try: 
        with open(file_path, 'w') as f:
            f.write(json.dumps(contents, 
                               sort_keys=True,
                               indent=4,
                               separators=(',', ': ')))
    except IOError:
        config_access_error()

def load_project_file(dirPath=None):
    """ Load settings object from filepath using the Settings module.

        If path is not given, use the current working directory.

        Attributes:
            dirPath (str): absolute path to the project directory containing
                the settigs file.

        Returns:
            An instance of the Settings class.

    """
    if not dirPath:
        dirPath = '.'

    if not os.path.isdir(dirPath):
        raise ValueError('Not a directory', dirPath)


    settings = get_settings_file(dirPath)

    return settings
