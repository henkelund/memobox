import sqlite3 as sqlite
from werkzeug.contrib.cache import NullCache

class DBHelper(object):
    """Helper class for SQLite DB access"""

    _instance = None

    def __new__(cls, db=':memory:', cache=NullCache(), *args, **kwargs):
        """Override __new__ to implement singleton pattern"""

        if not cls._instance:
            cls._instance = super(DBHelper, cls).__new__(cls, *args, **kwargs)
            cls._instance._conn = None
            cls._instance.set_db(db)
            cls._instance._cache = cache
        return cls._instance

    def __del__(self):
        """Destructor"""

        if self._conn is not None:
            self._conn.close()

    @staticmethod
    def _row_factory(cursor, row):
        """Dict row factory function"""

        data = {}
        for key, col in enumerate(cursor.description):
            data[col[0]] = row[key]
        return data

    @staticmethod
    def quote_identifier(identifier, alias = None):
        """Prepare a string for SQLite identifier use"""

        quote = lambda string: '"%s"' % string.replace('"', '""')
        parts = map(quote, identifier.split('.'))
        id_str = '.'.join(parts)

        if alias is not None:
            id_str += ' AS ' + quote(alias)

        return id_str

    def get_connection(self):
        """Retrive current SQLite connection"""
        return self._conn

    def set_db(self, db):
        """Set SQLite DB filename"""

        if self._conn is not None:
            self._conn.close()

        if db is None:
            self._conn = None
        else:
            self._conn = sqlite.connect(db)
            self._conn.row_factory = DBHelper._row_factory
            self._conn.text_factory = str
            self._conn.cursor().execute('PRAGMA foreign_keys = ON')

        return self

    def query(self, sql, bind = []):
        """Execute the given SQL and return a sqlite3.Cursor object"""
        return self._conn.cursor().execute(sql, bind)

    def describe_table(self, table, schema = None):
        """Return a dict describing the given table"""

        cache_key = 'DESCRIBE_%s.%s' % (schema or '', table)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        sql = 'PRAGMA '
        if schema is not None:
            sql += self.quote_identifier(schema) + '.'
        sql += 'table_info(%s)' % self.quote_identifier(table)

        desc = {}
        cursor = self.query(sql)
        for row in cursor.fetchall():
            desc[row['name']] = row

        self._cache.set(cache_key, desc)

        return desc

    def insert(self, table, bind):
        """Insert data into a table."""

        desc = self.describe_table(table)
        if not desc:
            # The table doesn't seem to exist
            raise sqlite.OperationalError
        else:
            desc = desc.keys()

        if type(bind) is dict:
            bind = (bind,)

        ids = []
        for row in bind:
            data = {}
            for key in row.keys():
                if key in desc:
                    data[self.quote_identifier(key)] = row[key]
            if not data:
                continue
            sql = 'INSERT INTO %s (%s) VALUES (%s)' % (
                self.quote_identifier(table),
                ', '.join(data.keys()),
                ', '.join('?' * len(data))
            )
            ids.append(self.query(sql, data.values()).lastrowid)

        return ids

