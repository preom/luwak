from luwak import GenerationComponent
from luwak.generate import *

class DatabaseManager(GenerationComponent):
    """ Abstraction for db operations. """

    def __init__(self, settings):
        super(DatabaseManager, self).__init__(settings)
        self.dbFilePath = os.path.join(self.settings['project_path'], 'db', self.settings['db_name'])

    def get_conn(self):
        """ Get sql connection and cursor. 

            Returns:
                tuple: (cursor, connection) from sqlite3 module.
        """

        conn = sqlite3.connect(self.dbFilePath, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        return (conn, cursor)


    def get_list(self, table, col, distinct=False):
        """ Return a list of row objects.

        Attributes:
            table: Table name.
            col: Column name; defaults to '*'.
            distinct: If select operation should be distinct. Defaults to False.

        Returns:
            [Row]: A list of row objects where the row factory is sqlite3.Row.
                Meaning that column values can be accessed using the column
                name as the key. For example: rowObject['column_name'].

        """
        conn, cursor = self.get_conn()

        if col is None:
            col = '*'

        if distinct:
            distinct = "distinct"
        else:
            distinct = ''

        sqlString = "SELECT {distinct} {col} from {table}".format(table=table, col=col, distinct=distinct)
        cursor.execute(sqlString)

        return cursor.fetchall()

    def fname_formatter(self, absFPath):
        """ Formats an absolute filepath to the format used as a key in the db. 

        Attributes: 
            absFPath: Absolute path to the file to format.

        Returns:
            str: filepath relative to the output directory.

        """

        sourceDir = os.path.join(self.settings['project_path'], self.settings['source_dir'])
        relativeFname = os.path.relpath(fpath, sourceDir) 

        return relativeFname

    def update_tags(self, fnameKey, tags):
        """ Update the tags for a given filename. 

        Attributes:
            fnameKey: Filename that's used as a key. Use fname_formatter to make
                sure that the filename is the standard form used in the db.
            tags: List of new tags for the article.

        """

        conn, cursor = self.get_conn()

        cursor.execute('select tag from tags where filename=?', (fnameKey,))

        tagSet = set(tags)
        dbTagSet = set([row['tag'] for row in cursor.fetchall()])

        toDelete =  dbTagSet - tagSet
        toAdd = tagSet - dbTagSet

        for tagName in toAdd:
            cursor.execute('Insert into tags (filename, tag) values (?, ?)', (fnameKey, tagName))

        for tagName in toDelete:
            cursor.execute('Delete from tags where filename=? and tag=?', (fnameKey, tagName))

        conn.commit()
        conn.close()
