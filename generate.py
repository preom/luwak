import json
import os

import markdown

from settings import Settings

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
                print filenames
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
            html = markdown.markdown(sourceContents)
        else:
            raise Exception("No reader known for: " + fpath)

        if not html:
            print 'Err: empty content file: ' + os.path.basename(fpath)

        return html

class TemplateCombinator(GenerationComponent):
    def __init__(self, settings):
        super(TemplateCombinator, self).__init__(settings)

    def combine(self, html, fname=None):
        """ 
        Takes html and produces a final html file combined with a template.
        Can use the fname to find meta information to be used in the template 
        generation process.

        """

        simpleTemplate = \
        """
        <html><head></head><body>{0}</body></html>
        """

        endProduct = simpleTemplate.format(html)

        return endProduct


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
            f.write(html)

        os.chdir(oldDir)




class DefaultGenerator(GenerationComponent):
    def __init__(self, settings):
        super(DefaultGenerator, self).__init__()

        self.content_loader = ContentLoader(self.settings)
        self.content_reader = ContentReader(self.settings)
        self.template = TemplateCombinator(self.settings)
        self.content_writer = ContentWriter(self.settings)

    def generate(self):
        pass
