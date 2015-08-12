from generate import GenerationComponent
from luwak.db import DatabaseManager


class CategoryGenerator(GenerationComponent):
    def __init__(self, settings):
        super(CategoryGenerator, self).__init__(settings)

    def get_tags(self, fname=None):
        """ Get a list of all the tags in the database as a row object. 

            Attributes:
                fname: Standardized form of the filename stored in the database.

            Returns: 
                [str]: list of tags.

        """
        dbManager = DatabaseManager(self.settings)
        conn, cursor = dbManager.get_conn()

        sqlString = 'Select distinct tag from tags order by tag'

        cursor.execute(sqlString)
        return cursor.fetchall()

    def get_fnames_from_tag(self, tagName):
        """ Get filenames with a tag matching tagName. """
        dbManager = DatabaseManager(self.settings)
        conn, cursor = dbManager.get_conn()

        sqlString = 'Select tags.filename, title from tags left join meta on tags.filename=meta.filename where tags.tag="{}"'.format(tagName)

        cursor.execute(sqlString)

        return cursor.fetchall()


    def tag_page(self, tagName):
        """ Return the links to posts that use 'tagName' """
        pass
