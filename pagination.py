import sqlite3
from generate import DatabaseManager

class PaginationDataSource(object):
    """ Adapter between data and Pagination class.

    """

    def __init__(self, pageSize=10):
        self.pageSize = pageSize

    def get_generator(self):
        """ Returns a iterable generator 

        Note: Low memory usage, but slower

        """
        pass

class PaginationDbDataSource(PaginationDataSource):
    """ Uses a db source e.g. sqlite3 as a data source.

        Note:
            page index begins at 1
    """

    def __init__(self, dbfilepath=None):
        super(PaginationDbDataSource, self).__init__()

        if not dbfilepath:
            raise ValueError("PaginationDbDataSource requires a path to a database")

        self.conn = sqlite3.connect(dbfilepath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.table = 'meta'
        self.cursor.execute('select count(*) as total from {}'.format(self.table))
        self.totalCount = self.cursor.fetchone()['total']
        self.pageCount = self.totalCount/self.pageSize

    def get_generator(self):
        """ Return a generator that produces index pages.

        Note: 
            function shouldn't make any writes to db

        """
        cursor = self.cursor

        for pageIndex in range(0, self.pageCount + 1):
            limit = self.pageSize 
            offset = (pageIndex) * limit
            cursor.execute('select * from {} limit ? offset ?'.format(self.table), (limit, offset))
            page = cursor.fetchall()

            yield (pageIndex + 1, page)


class Paginator(object):
    """ Takes a data source and outputs a nested data structure.

    TODO: 
        Add start page number
    """

    def __init__(self, paginationDataSource):
        self.paginationDataSource = paginationDataSource
        self.pagePreviewSize = 4
        self.outputString = 'index{}.html'

    def indexHrefFormatter(self, pagenum):
        if pagenum == 1:
            pagenum = ""

        return self.outputString.format(pagenum)



    def get_generator(self):
        """ Returns a generator that procues page index info.

        """
        for pageIndex, page in self.paginationDataSource.get_generator():

            pageInfo = dict()
            postList = []


            for article in page:
                # load from row object to dict
                title = article['title']
                filename = article['filename']
                created = article['created']

                #TODO: load from db instead to presrve data integrity
                newName = ''.join(filename.split('.')[:-1]+['.html'])
                href = newName

                postList.append((title, href, article))

            pageInfo['postList'] = postList

            pageInfo['currentPage'] = pageIndex

            pageInfo['leftAdjacentPages'] =  \
                [i for i in range(max(pageIndex-self.pagePreviewSize, 1), pageIndex)]

            if 1 in pageInfo['leftAdjacentPages']:
                pageInfo['firstPage'] = None
            else: 
                pageInfo['firstPage'] = 1

            pageInfo['rightAdjacentPages'] = \
                [i for i in range(pageIndex+1, min(pageIndex+self.pagePreviewSize, self.paginationDataSource.pageCount) + 1)]

            if self.paginationDataSource.pageCount in pageInfo['rightAdjacentPages']:
                pageInfo['lastPage'] = None
            else: 
                pageInfo['lastPage'] = self.paginationDataSource.pageCount

            for l in [pageInfo['leftAdjacentPages'], pageInfo['rightAdjacentPages']]:
                l[:] = [(i, self.indexHrefFormatter(i)) for i in l]

            for l in ['firstPage', 'lastPage', 'currentPage']:
                # pageInfo[l] can evaluate to False if index is 0
                if pageInfo[l] is not None:
                    pageInfo[l] = (pageInfo[l], self.indexHrefFormatter(pageInfo[l]))

            yield pageInfo

