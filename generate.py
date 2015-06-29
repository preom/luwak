import json
import os

import markdown

from settings import Settings

import sys

from bs4 import BeautifulSoup

import pdb

class GenerationComponent(object):
    def __init__(self, settings):
        if type(settings) == str:
            settings = GenerationComponent.load_project_file(settings)

        self.settings = settings

    @staticmethod
    def load_project_file(path=None):
        if not path:
            path = '.'

        cwd = os.getcwd()

        if not os.path.isdir(path):
            raise ValueError('Not a directory', path)

        os.chdir(path)

        try:
            with open(Settings.CONFIG_FILENAME, 'r') as f:
                    settings = json.loads(f.read())

        except:
            print "Error loading the config file"
            raise

        os.chdir(cwd)

        return settings


class ContentLoader(GenerationComponent):
    def __init__(self, settings):
        super(ContentLoader, self).__init__(settings)

    def get_content_paths(self):
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
        valid_extensions = ['.md']
        
        result = False
        for extension in valid_extensions:
            if filename.endswith(extension):
                result = True
                break

        return result


class ContentReader(GenerationComponent):
    def __init__(self, settings):
        super(ContentReader, self).__init__(settings)

    def generate_html(self, fpath):
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

        meta = {}

        if fpath.endswith('.md'):
            md = markdown.Markdown(extensions=['markdown.extensions.meta'])
            with open(fpath,'r') as f:
                md.convert(f.read())

            for k, v in md.Meta.items():
                meta[k] = v

        return meta

# Returns path to template config file so far, useless
# TODO change to using local template folder
def load_template_file(settings=None):
    templateFilename = 'luwak_template.rc'
    defaultTemplatesPath = os.path.join(os.path.dirname(__file__), 'templates')
    defaultTemplates = os.listdir(defaultTemplatesPath)

    if settings and hasattr(self.settings, 'template'):
        template = self.settings.template 
    else:
        template = defaultTemplates[0]

    if template in defaultTemplates:
        return os.path.join(defaultTemplatesPath, template, templateFilename)
    else:
        return ValueError("not implemented yet...")

class TemplateCombinator(GenerationComponent):
    def __init__(self, settings):
        super(TemplateCombinator, self).__init__(settings)

    """
    Returns template string
    """
    def get_template(self, templateType='default'):
        templateConfigFilePath = load_template_file()
        templateDirPath = os.path.dirname(templateConfigFilePath)

        with open(templateConfigFilePath, 'r') as f:
            templateConfig = json.loads(f.read())

        # TODO match fname against rules

        with open(os.path.join(templateDirPath, templateConfig[templateType]), 'r') as f:
            templateHtml = f.read()

        return templateHtml


    def combine(self, html, fname=None, meta=dict()):
        """ 
        Takes html and produces a final html file combined with a template.
        Can use the fname to find meta information to be used in the template 
        generation process.

        """

        templateHtml = self.get_template()
        templateSoup = BeautifulSoup(templateHtml)
        htmlSoup = BeautifulSoup(html)

        tag = templateSoup.find(class_='luwak-content')
        tag.insert(1, htmlSoup)

        print meta

        if 'tags' in meta:
            htmlSoup = BeautifulSoup(''.join(["<span class='tag well'>{}</span> ".format(tag) for tag in meta['tags']]))
            tag = templateSoup.find(class_='luwak-tags')
            tag.insert(1, htmlSoup)

        if 'title' in meta:
            tag = templateSoup.find(class_='luwak-title')
            try:
                tag.string.replace_with(meta['title'][0])
            except:
                print "Warning template has no title or other error"

        #print templateSoup
        endProduct = templateSoup.prettify()

        return endProduct

    def combine_index(self, postList):
        templateHtml = self.get_template('index')
        postListHtml = []
        for title, href in postList:
            postListHtml.append('<a href=\'{1}\'>{0}</a>'.format(title, href))

        listSoup = BeautifulSoup('<br>'.join(postListHtml))    
        templateSoup = BeautifulSoup(templateHtml)

        tag = templateSoup.find(class_='luwak-index')

        print templateSoup
        print tag

        if not tag:
            raise ValueError('No luwak-index in index template')

        tag.insert(1, listSoup)

        return templateSoup.prettify()

class ContentWriter(GenerationComponent):
    def __init__(self, settings):
        super(ContentWriter, self).__init__(settings)

    def output(self, html, fname=None):
        output_dir = self.settings['output_dir']
        project_path = self.settings['project_path']
        newName = ''

        newName = ''.join(fname.split('.')[:-1]+['.html'])

        oldDir = os.getcwd()
        os.chdir(project_path)
        os.chdir(output_dir)
        with open(newName, 'w') as f:
            print type(f)
            f.write(html)

        os.chdir(oldDir)

        return newName


class DefaultGenerator(GenerationComponent):
    def __init__(self, settings):
        super(DefaultGenerator, self).__init__()

        self.content_loader = ContentLoader(self.settings)
        self.content_reader = ContentReader(self.settings)
        self.template = TemplateCombinator(self.settings)
        self.content_writer = ContentWriter(self.settings)

    def generate(self):
        pass
