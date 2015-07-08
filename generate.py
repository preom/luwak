import json
import os

import markdown

from settings import Settings

import sys

from bs4 import BeautifulSoup

import pdb
import datetime

import sqlite3


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

        except IOError:
            print " >>> ----------------------------- <<< "
            print " >>> Error loading the config file <<< "
            print " >>> ----------------------------- <<< "
            sys.exit(0) 

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
        templateSoup = BeautifulSoup(templateSoup.encode_contents())

        def cleanup():
            return BeautifulSoup(templateSoup.encode_contents())

        def date_formatter(metaDate):
            date = datetime.datetime.strptime(metaDate[0], '%Y-%m-%d')
            return date.strftime('%B %d, %Y')

        def tag_formatter(metaTags):
            tagString = "<span class='tag label label-default'> <span class='glyphicon glyphicon-tag'></span> {}</span>"
            tagHtml = ''.join([tagString.format(tag) for tag in meta['tags']])

        def prev_formatter(metaPrev):
            tagString = '<a href=\'{}\'><span aria-hidden="true" class="glyphicon glyphicon-menu-left"></span> Prev </a>'
            return tagString.format(metaPrev[0])

        def next_formatter(metaNext):
            tagString = '<a href=\'{}\'>Next <span aria-hidden="true" class="glyphicon glyphicon-menu-right"></span></a>'
            return tagString.format(metaNext[0])


        metaTags = ['date', 'tags', 'title', 'prev', 'next']
        formatters = [date_formatter, tag_formatter, None, prev_formatter, next_formatter]
        template_class = ['luwak-date', 'luwak-tags', 'luwak-title', 'luwak-prev', 'luwak-next']

        assert(len(metaTags) == len(formatters) == len(template_class))

        for mTag, frmt, cls in zip(metaTags, formatters, template_class):
            if mTag in meta:
                tag = templateSoup.find(class_=cls)
                if frmt:
                    tagContent = frmt(meta[mTag])
                else:
                    tagContent = meta[mTag][0]

                if tagContent:
                    soup = BeautifulSoup(tagContent, 'html.parser')
                else:
                    continue

                try:
                    tag.append(soup)
                except:
                    print "Error with parsing " + mTag

                templateSoup = cleanup()

        #TODO Fix this arbitrary piece of code
        if len(templateSoup) < 3000:
            tag = templateSoup.find(class_='to-top')
            if tag:
                tag['class'].append('hidden')

        #print templateSoup
        endProduct = templateSoup.prettify()

        return endProduct

    def combine_index(self, pageInfo):
        def a_formatter(title, href):
            return "<a href='{1}'>{0}</a>".format(title, href)

        templateHtml = self.get_template('index')
        postListHtml = []
        for title, href, article in pageInfo['postList']:

            aHtml = '<a href=\'{1}\'>{0}</a>'.format(title.title(), href)
            dateHtml = '<span>{}</span>'.format(article['created'].strftime("%b %d, %y"))
            postStr = """
                <div class=\'index-post\'>
                    <div class=\'post-title\'>{aHtml}</div>
                    <div class=\'post-date\'>{dateHtml}</div>
                </div>
            """
            postListHtml.append(postStr.format(aHtml=aHtml,dateHtml=dateHtml))

        listSoup = BeautifulSoup('<hr>'.join(postListHtml))    
        templateSoup = BeautifulSoup(templateHtml)

        tag = templateSoup.find(class_='luwak-index')
        paginationTag = templateSoup.find(class_='luwak-pagination')

        if not tag:
            raise ValueError('No luwak-index in index template')
        else:
            tag.append(listSoup)


        leftAdjacent = [a_formatter(title, href) for title, href in pageInfo['leftAdjacentPages']]
        rightAdjacent = [a_formatter(title, href) for title, href in pageInfo['rightAdjacentPages']]

        currentpage = a_formatter(pageInfo['currentPage'][0], pageInfo['currentPage'][1])

        page_list = leftAdjacent + [currentpage] + rightAdjacent
        for ind, val in enumerate(page_list):
            if val == currentpage:
                cls = 'active'
            else:
                cls = ''

            page_list[ind] = "<li class='{}'>{}</li>".format(cls, val)


        page_list = ['<ul class="pagination pull-right">'] + page_list + ['</ul>']

        paginationSoup = BeautifulSoup(''.join(page_list))

        tag = templateSoup.find(class_='luwak-pagination')

        if paginationTag:
            paginationTag.append(paginationSoup)
        else:
            print "WARNING: no page index"

        return templateSoup.prettify()

class ContentWriter(GenerationComponent):
    def __init__(self, settings):
        super(ContentWriter, self).__init__(settings)

    def generate_name(self, fname):
        newName = ''.join(fname.split('.')[:-1]+['.html'])
        return newName

    def output(self, html, fname=None):
        output_dir = self.settings['output_dir']
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

class IterativeBuilder(GenerationComponent):
    def __init__(self, settings):
        super(IterativeBuilder, self).__init__(settings)

    def content_filter(self, contentList):
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

class DatabaseManager(GenerationComponent):
    def __init__(self, settings):
        super(DatabaseManager, self).__init__(settings)
        self.dbFilePath = dbPath = os.path.join(self.settings['project_path'], 'db', self.settings['db_name'])


class DefaultGenerator(GenerationComponent):
    def __init__(self, settings):
        super(DefaultGenerator, self).__init__(settings)

        self.content_loader = ContentLoader(self.settings)
        self.content_reader = ContentReader(self.settings)
        self.template = TemplateCombinator(self.settings)
        self.content_writer = ContentWriter(self.settings)

    def generate(self):
        pass


