import json
import os

import markdown

from luwak import settings as Settings
from luwak import GenerationComponent
from luwak.db import DatabaseManager

import sys

import pdb
import datetime

import sqlite3


class ContentLoader(GenerationComponent):
    """ Responsible for finding potential content files """

    def __init__(self, settings):
        super(ContentLoader, self).__init__(settings)

    def get_content_paths(self):
        """ Get paths to all potential source files to be processed using the 
            settings attribute. 

            Returns:
                list of absolute filepaths.

        """ 
        settings_source = self.settings['source_dir']
        sources = []
        files = []

        oldpath = os.getcwd()

        # json source can be a list or string
        if type(settings_source) == str or type(settings_source) == unicode:
            sources.append(settings_source)
        else:
            sources.extend(settings_source)

        os.chdir(self.settings['project_path'])

        def walkerror(oserr):
            print "ERR: " + oserr.filename

        def make_abspath(fname):
            if os.path.isabs(fname):
                return fname
            else:
                return os.path.abspath(fname)

        sources = map(make_abspath, sources)        

        for src in sources:
            for dirpath, dirname, filenames in os.walk(src, onerror=walkerror):
                files.extend([os.path.join(dirpath, filename) for filename in filenames])

        files = filter(self.file_filter_func, files) 

        os.chdir(oldpath)

        return files

    @staticmethod
    def file_filter_func(filename):
        """ Filters the content files based . 

        Use this function to filter by things such as file extension.

        Returns:
            bool: True if file is valid, False otherwise.

        """

        valid_extensions = ['.md']
        
        result = False
        for extension in valid_extensions:
            if filename.endswith(extension):
                result = True
                break

        return result


class ContentReader(GenerationComponent):
    """ Parse the contents of a source file.

    Assume that the content file is markdown and process using the python
    markdown module.

    Note:
        Default markdown extensions for meta and syntax highlitng are also used.

    """

    def __init__(self, settings):
        super(ContentReader, self).__init__(settings)

    def generate_html(self, fpath):
        """ Transform contents of a source file into html.

        Attributes:
            fpath: Absolute filepath to the file to transform.

        Returns:
            str: html string

        """

        html = ''
        sourceContents = ''

        with open(fpath, 'r') as f:
            sourceContents = f.read()

        if fpath.endswith('.md'):
            md = markdown.Markdown(extensions=[
                'markdown.extensions.meta', 
                'markdown.extensions.fenced_code', 
                'markdown.extensions.codehilite'])
            html = md.convert(sourceContents)
        else:
            raise Exception("No reader known for: " + fpath)

        if not html:
            print 'Err: empty content file: ' + os.path.basename(fpath)

        return html

    def generate_meta(self, fpath):
        """ Gather any meta data related to the filepath given.

        Use the markdown extension to gather meta information. 

        Attributes:
            fpath: absolute filepath to the filename.

        Returns:
            dict: dict of meta values.


        TODO:
            - Use a separate file as a source for meta information based on filename

        """

        meta = {}

        if fpath.endswith('.md'):
            md = markdown.Markdown(extensions=['markdown.extensions.meta'])
            with open(fpath,'r') as f:
                md.convert(f.read())

            for k, v in md.Meta.items():
                meta[k] = v

        return meta



class ContentWriter(GenerationComponent):
    """ Use to write contents to a file. """

    def __init__(self, settings):
        super(ContentWriter, self).__init__(settings)

    def generate_name(self, fname):
        """ Take a filename (not path) and return a canonical filename """

        if not fname:
            raise ValueError("Expected a valid filename")

        root, ext = os.path.splitext(fname)
        newName = root + '.html'
        return newName

    def generate_dir(self, dirType):
        """ Generate the directory to be used based on dirType.

            Use to control the structure of luwak project directories by
            establishing a specific structure.

            Attributes:
                dirType (str): Directory type; valid types are: 'tags'.

            Returns:
                str: Absolute path to directory in the luwak project.

            Todo:
                rename method since it implies that it actually generates a
                directory and not a directory name.

        """
        validDirTypes = ['tags']
        settingsValues = ['tags_dir']

        lookup = dict(zip(validDirTypes, settingsValues))

        if dirType not in validDirTypes:
            raise ValueError("")

        outputDir = os.path.join(self.settings['project_path'], self.settings['output_dir'], self.settings[lookup[dirType]])

        return outputDir

    def output(self, html, fname=None, dirPath=None):
        """ Writes html code to a file.

        Use to output final versions of processed content to the output 
        directory.

        Attributes:
            html: Content to be written (assumed to be html code).
            fname: Related filename (e.g. filename of the original source file).
                Defaults to None.
            dirPath: Absolute directory path to place the file in. Defaults to None.

        Returns:
            str: Filename relative to the output directory.

        Note:
            Instead of using the dirPath attribute, use output_specific to 
            output to specific directories in the output directory.

        """
        if dirPath is None:
            output_dir = self.settings['output_dir']
        else:
            output_dir = dirPath

        project_path = self.settings['project_path']
        newName = ''

        newName = self.generate_name(fname)

        oldDir = os.getcwd()
        os.chdir(project_path)
        os.chdir(output_dir)
        with open(newName, 'w') as f:
            f.write(html)
        os.chdir(oldDir)

        return newName

    def output_specific(self, html, fname, dirType):
        """ Wrapper for output method with a specific directory type.

        Use to output to specific directory categories in the output directory
        such as the 'tags' directory. Refer to the generate_dir method used
        to see what valid directories exist and where they are in the output
        directory.

        Notes:
            Bulk of code logic moved to self.generate_dir

        """
        return self.output(html, fname, dirPath=self.generate_dir(dirType))


class IterativeBuilder(GenerationComponent):
    """ Use to implement iterative builds. """

    def __init__(self, settings):
        super(IterativeBuilder, self).__init__(settings)

    def content_filter(self, contentList):
        """ Filter files that haven't been updated.

        Check files against the database, return those that have been recently 
        modified and update db. If the file isn't found in database, add it.

        Attributes:
            contentList: List of absolute filepaths to be filtered.

        Returns:
            List of filepaths that have been updated that are a subset of 

                contentList.

        """ 
        dbManager = DatabaseManager(self.settings)
        dbPath = dbManager.dbFilePath

        conn = sqlite3.connect(dbPath, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        sourceDir = os.path.join(self.settings['project_path'], self.settings['source_dir'])
        resultList = []

        for fpath in contentList:
            relativeFname = os.path.relpath(fpath, sourceDir) 
            modtime = datetime.datetime.fromtimestamp(os.stat(fpath).st_mtime)

            cursor.execute('select * from records where filename=?', (relativeFname,))
            row = cursor.fetchone()
            if row is None:
                cursor.execute('insert into records values(?, ?)', (relativeFname, modtime))
                conn.commit()
            else:
                dbModtime = row['modified']
                if (modtime > dbModtime): # check if updated
                    #TODO Delete this
                    cursor.execute('update records set modified=? where filename=?', (modtime, relativeFname))
                    conn.commit()
                else:
                    continue

            resultList.append(fpath)

        if len(resultList) == 0:
            print ">>>----------------<<<"
            print ">>> All up to date <<<"
            print ">>>----------------<<<"

        return resultList

    def update(self, contentList):
        """ Updates files.

        Attributes:
            contentList: list of filenames to update in database. 

        """
        pass


class DefaultGenerator(GenerationComponent):
    """ Wrapper for the content processing pipeline.

    Use all the derived GenerationComponent classes to provide an interface
    to process source content. 

    Note: 
        Currently not implemented.

    """

    def __init__(self, settings):
        super(DefaultGenerator, self).__init__(settings)

        self.content_loader = ContentLoader(self.settings)
        self.content_reader = ContentReader(self.settings)
        self.template = TemplateCombinator(self.settings)
        self.content_writer = ContentWriter(self.settings)

    def generate(self):
        pass


