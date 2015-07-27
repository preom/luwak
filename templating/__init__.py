import os
import json
import datetime
import logging

from luwak.generate import GenerationComponent
from luwak.settings import Settings

from bs4 import BeautifulSoup

from jinja2 import FileSystemLoader, Environment

TEMPLATE_RC_NAME = 'luwak_template.rc'

# Returns path to template config file so far, useless
# TODO change to using local template folder
def load_template_file(settings=None):
    """ Load absolute path to luwak template config file.

    Get the correct template config file using the settings file and returning the
    correct defualt template. If not settings object is given, use the first template
    found in the default templates directory (uses os.listdir which has an arbitrary 
    order).

    Note:
        Default templates can be created using the templates folder in the 
        luwak source directory. 

    Attributes:
        settings: Instance of a settings object.

    Returns:
        str: absolute file path.

    """ 

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

class CombinatorBase(object):
    def __init__(self, templateSettings, templateDirPath):
        """
        templateDirPath is specified because templates are meant to be mobile.

        Attributes:
            templateSettings (dict):  template settings. 

        """
        self.templateSettings = templateSettings
        self.templateDirPath = templateDirPath

    def combine(self, template, context, templateType):
        pass

    def load_template(self, templateType):
        pass

    def _load_template_name(self, templateType=None):
        if templateType is None:
            templateType = 'default'

        try:
            return self.templateSettings[templateType]
        except KeyError:
            errorMsg = """
            Template doesn't have that kind of file. If this is a custom 
            template, make sure the correct type is added."""

            print templateType
            print errorMsg


class Bs4Combinator(CombinatorBase):
    def combine(self, type) :
        if type is None or type == 'default':
            templateHtml = self.get_template()
            templateSoup = BeautifulSoup(templateHtml)
            htmlSoup = BeautifulSoup(html)

            tag = templateSoup.find(class_='luwak-content')
            tag.insert(1, htmlSoup)
            templateSoup = BeautifulSoup(templateSoup.encode_contents())

            def cleanup():
                """ Return a cleaned version of a beautifulsoup object.

                    BeautifulSoup has a bug that prevents finding tags correctly
                    after inserting a soup object. Use this function to decod the 
                    template soup into text and then parse that string into a 
                    BeautifulSoup object again.

                """
                return BeautifulSoup(templateSoup.encode_contents())

            # Formatters for the data to be injected
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

            endProduct = templateSoup.prettify()

            return endProduct
        elif type == 'list':
            templateHtml = self.get_template('list')
            def a_formatter(title, href):
                if not href:
                    href = ''
                return "<a href='{1}'>{0}</a>".format(title, href)

            linksHtml = ''.join([a_formatter(title, href) for title, href in links])
            linksSoup = BeautifulSoup(linksHtml)
            templateSoup = BeautifulSoup(templateHtml)

            tag = templateSoup.find(class_='luwak-list')
            tag.append(linksSoup)

            if listTitle:
                tag = templateSoup.find(class_='luwak-list-title')
                tag.string.replace_with(listTitle)

            return templateSoup.prettify()
        elif type == 'index':
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

class JinjaCombinator(CombinatorBase):
    def __init__(self, *args):
        super(JinjaCombinator, self).__init__(*args)
        self.env = Environment(loader=FileSystemLoader(self.templateDirPath))
     
    def combine(self, context, templateType=None):
        template = self.load_template(templateType)
        return template.render(context)

    def load_template(self, templateType):
        templateName = self._load_template_name(templateType)
        return self.env.get_template(templateName)

class TemplateLoader(object):
    pass

def get_combinator(settings):
    """ Get combinator based on template settings type. """


class TemplateCombinator(GenerationComponent):
    """ Insert values into a template """

    def __init__(self, settings):
        super(TemplateCombinator, self).__init__(settings)
        self.combinator = get_combinator(settings)

    def _get_template_dir(self):
        """ Get template directory

        """
        defaultTemplatesDir = os.path.join(os.path.dirname(__file__), 'templates')
        defaultTemplates = os.listdir(defaultTemplatesDir)
        defaultTemplate = 'default'

        try:
            localTemplatesDir = os.path.join(self.settings['project_path'], 'templates')
            foundTemplates = os.listdir(localTemplatesDir)
        except:
            logging.warning('No local templates directory found.')
            foundTemplates = []

        if 'template' not in self.settings:
            return os.path.join(defaultTemplatesDir, 'default')

        elif os.path.isdir(self.settings['template']):
            return self.settings['template']
        elif self.settings['template'] in foundTemplates:
            return os.path.join(localTemplatesDir, self.settings['template'])
        else:
            raise ValueError("Couldn't find specified template")

    def combine(self, ctx, templateType=None):
        """Injects values into a html template.

        Use for standard type article i.e. with a title, content, tags, etc.

        Attributes:
            html: Html code to be inserted into the template.
            fname: Filename of the source file. Defaults to None.
            meta: Meta values of the source file. Defaults to an empty dict.

        Returns:
            str: html code with given values inserted.

        """
        templateDir = self._get_template_dir()
        templateRcPath = os.path.join(templateDir, TEMPLATE_RC_NAME)
        try:
            with open(templateRcPath) as f:
                templateRc = json.loads(f.read())
        except IOError:
            print "Couldn't load template rc folder... Is it a valid template?"
            raise 

        if 'loader_type' not in templateRc:
            logging.warning("template should have a type")
        elif templateRc['loader_type'] == 'default':
            pass
        elif templateRc['loader_type'] == 'jinja':
            combinator = JinjaCombinator(templateRc, templateDir)
        else:
            ValueError('Not a valid option for template rc.')

        output = combinator.combine(ctx, templateType=templateType)

        return output

    def combine_html_wrapper(self, html='', fname=None, meta=dict()):
        context = meta
        context['main_content'] = html
        context['fname'] = html

        return self.combine(context)

    def combine_template(self, template, ctx):
        pass

if __name__ == '__main__':
    pass
