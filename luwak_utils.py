#!/home/preom/Workarea/projects/luwak_env/bin/python

from luwak.settings import Settings
from luwak.generate import *
from luwak.pagination import *

import argparse
import sys
import os
import shutil
import sqlite3

import time

from pygments.formatters import HtmlFormatter

def process_start(*args, **kwargs):

    CONFIG_FILENAME = Settings.CONFIG_FILENAME

    params = vars(args[0])

    def make_directory(dirname):
        os.mkdir(dirname)
        if params['is_verbose']:
            print "Directory made: " + dirname


    if params['is_verbose']:
        print "VARS:" + str(vars(args[0]))

    if params['destination'] is not None:
        os.chdir(params['destination'])

        if params['is_verbose']:
            print "Path set to: " + os.getcwd();

    # Make root project folder
    make_directory(params['project_name'])
    os.chdir(params['project_name'])

    # Make database
    dbDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db')
    with open(os.path.join(dbDir, 'main.sql'), 'r') as f:
        sqlScript = f.read()

    make_directory('db')
    oldDir = os.getcwd()
    os.chdir('db')
    conn = sqlite3.connect(Settings.default_data['db_name'])
    cursor = conn.cursor()
    cursor.executescript(sqlScript)
    conn.commit()
    os.chdir(oldDir)

    # Make output 
    output_dir = Settings.default_data['output_dir']
    make_directory(output_dir)

    # copy start template
    startTemplateDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates', 'start')
    for src in [os.path.join(startTemplateDir, i) for i in os.listdir(startTemplateDir)]:
        if os.path.isfile(src):
            shutil.copy(src, output_dir)
        else:
            print os.path.join(os.path.join(output_dir, os.path.basename(src)))
            shutil.copytree(src, os.path.join(output_dir, os.path.basename(src)))

    with open(os.path.join(output_dir, 'css', 'pygments.css'), 'w') as f:
        f.write(HtmlFormatter(style='monokai').get_style_defs('.codehilite'))


    # Make content directory
    source_dir = Settings.default_data['source_dir']
    make_directory(source_dir)
    olddir = os.getcwd()
    os.chdir(source_dir)
    testFilesDirPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests')
    for i in os.listdir(testFilesDirPath):
        pth = os.path.join(testFilesDirPath, i)
        if os.path.isfile(pth):
            shutil.copy(pth, '.')
    os.chdir(olddir)

    # Make config file
    Settings.generate_default_settings_file()

def process_generate(*args, **kwargs):
    startTime = time.time()

    CONFIG_FILENAME = Settings.CONFIG_FILENAME

    params = vars(args[0])

    if 'project_path' not in params:
        params['project_path'] = os.getcwd()

    proj_settings = GenerationComponent.load_project_file(params['project_path'])

    iterativeBuidler = IterativeBuilder(proj_settings)
    dbManager = DatabaseManager(proj_settings)

    content_loader = ContentLoader(proj_settings)
    contentReader = ContentReader(proj_settings)
    templater = TemplateCombinator(proj_settings)
    contentWriter = ContentWriter(proj_settings)

    contentFiles = content_loader.get_content_paths()

    if params['do_flush']:
        conn = sqlite3.connect(dbManager.dbFilePath)
        cursor = conn.cursor()
        cursor.execute('delete from records')
        cursor.execute('delete from meta')
        conn.commit()

    contentFiles = iterativeBuidler.content_filter(contentFiles)

    postList = []
    metaList = []

    conn = sqlite3.connect(dbManager.dbFilePath)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    toUpdateList = [] #TODO change name from toUpdateList
    sourceDir = os.path.join(proj_settings['project_path'], proj_settings['source_dir'])
    for fpath in contentFiles:
        relativeFname = os.path.relpath(fpath, sourceDir) 
        cursor.execute('select * from meta where filename=?', (relativeFname,))
        row = cursor.fetchone()
        meta = contentReader.generate_meta(fpath)
        category =  meta.get('category', [None])[0]

        if row:
            if 'category' in row.keys():
                storedCategory = row['category']
            else:
                storedCategory = None

            if storedCategory != category:
                toUpdateList.append((relativeFname, meta, 'update')), 

        else:
            toUpdateList.append((relativeFname, meta, 'add'))

    for relativeFname, meta, status in toUpdateList:
        category = meta.get('category', [None])[0]
        title = meta['title'][0]
        if status == 'add':
            cursor.execute('insert into meta (filename, category, title) values(?, ?, ?)', (relativeFname, category, title))
            conn.commit()

            cursor.execute('select count(*) from meta where category=? and title<?', (category, title))
            rowCount = cursor.fetchone()[0]

            # SKIP NULL VALUES:
            if category is None:
                continue

            if rowCount <= 0:
                cursor.execute('select * from meta where category=? order by category, title limit 2 offset ?', (category, rowCount))
                results = cursor.fetchall()
                prev = None
                current = results[0]

                if len(results) > 1:
                    next = results[1]
                else:
                    next = None

            else:
                cursor.execute('select * from meta where category=? order by category, title limit 3 offset ?', (category, rowCount - 1))
                results = cursor.fetchall()
                while (len(results) < 3):
                    results.append(None)

                prev, current, next = results 

            # Link Next
            if next:
                cursorArgs = (next['filename'], current['filename'])
                cursor.execute('update meta set nextFilename=? where filename=?', cursorArgs)

                cursorArgs = (current['filename'], next['filename'])
                cursor.execute('update meta set prevFilename=? where filename=?', cursorArgs)

            # Link previous
            if prev:
                cursorArgs = (prev['filename'], current['filename'])
                cursor.execute('update meta set prevFilename=? where filename=?', cursorArgs)

                cursorArgs = (current['filename'], prev['filename'])
                cursor.execute('update meta set nextFilename=? where filename=?', cursorArgs)

            conn.commit()


    for fpath in contentFiles:
        fname = os.path.basename(fpath)
        htmlContent = contentReader.generate_html(fpath)
        metaContent = contentReader.generate_meta(fpath)

        relativeFname = os.path.relpath(fpath, sourceDir) 
        cursor.execute('select * from meta where filename=?', (relativeFname,))
        row = cursor.fetchone()
        # transform from source filename to output filename
        if row['prevFilename']:
            metaContent['prev'] = [contentWriter.generate_name(row['prevFilename'])]
        if row['nextFilename']:
            metaContent['next'] = [contentWriter.generate_name(row['nextFilename'])]

        html = templater.combine(htmlContent, fname=fname, meta=metaContent)
        href = contentWriter.output(html, fname)
        postList.append((metaContent['title'][0], href))


    #index_html = templater.combine_index(postList)
    #contentWriter.output(index_html, 'index.html')

    pgDSource = PaginationDbDataSource(dbManager.dbFilePath)
    paginator = Paginator(pgDSource)
    for pageInfo in paginator.get_generator():
        index_html = templater.combine_index(pageInfo)
        print '225: ', pageInfo['currentPage']
        contentWriter.output(index_html, 'index{}.html'.format(pageInfo['currentPage'][0]))

    elapsedTime = time.time() - startTime
    print ">> -- Time: {:.4f} -- <<".format(elapsedTime)

if __name__ == "__main__":
    # root parser
    parser = argparse.ArgumentParser(description='cli for luwak')
    subparsers = parser.add_subparsers(title='Subcommands',
                                       description='List of subcommands')

    # 'startproject' parser
    parser_start = subparsers.add_parser('startproject', help='Creates a new luwak project')
    parser_start.add_argument('project_name', help='project name')
    parser_start.add_argument('-d', '--destination', help='Where to startproject', dest='destination')
    parser_start.add_argument('-v', '--verbose', help='verbose', dest='is_verbose', action='store_true')
    parser_start.set_defaults(func=process_start)

    # 'generate' parser
    parser_generate = subparsers.add_parser('generate', help='Generates luwak project content')
    parser_generate.add_argument('-p', '--path', help='Path to root luwak project (where the config file is)', dest='project_path')
    parser_generate.add_argument('-f', '--flush', help='', dest='do_flush', action='store_true')
    parser_generate.set_defaults(func=process_generate)

    args = parser.parse_args()
    args.func(args)
