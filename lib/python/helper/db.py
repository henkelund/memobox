import sqlite3 as sqlite
from werkzeug.contrib.cache import NullCache
import re

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

class DBSelect(object):
    """Helper for building SQLite SELECT queries"""

    def __init__(self, table, cols='*'):
        """Constructor"""

        self._distinct = False
        self._tables = []
        self._columns = []
        self._wheres = []
        self._orders = []
        self._limit = None
        self._offset = None
        self._bind = []
        self.set_from(table, cols)

    def __str__(self):
        """String representation of this SELECT object"""
        return self.render()

    def _unique_alias(self, name):
        """Create a unique table alias within this select"""

        if isinstance(name, basestring):
            name = name.split('.')

        alias = name = name[-1]

        aliases = []
        for table in self._tables:
            aliases.append(table['alias'])

        i = 2
        while alias in aliases:
            alias = '%s_%s' % (name, i)
            i = i + 1

        return alias

    def _table_cols(self, alias, cols):
        """Specify columns to be selected for given table alias"""

        if isinstance(cols, basestring):
            self._columns.append((alias, cols, None))
        elif isinstance(cols, (tuple, list)):
            for col in cols:
                self._columns.append((alias, col, None))
        elif isinstance(cols, dict):
            for col_alias in cols.keys():
                self._columns.append((alias, cols[col_alias], col_alias))

        return self

    def _join(self, join_type, name, cond, cols, schema=None):
        """Join an additional table"""

        alias = table_name = ''
        if isinstance(name, (tuple, list)):
            alias = name[1]
            table_name = name[0]
        else:
            alias = self._unique_alias(name)
            table_name = name

        table = {
            'alias' : alias,
            'join_type' : join_type,
            'schema' : schema,
            'table_name' : table_name,
            'join_condition' : cond
        }

        if join_type == 'FROM':
            self._tables.insert(0, table)
        else:
            self._tables.append(table)

        self._table_cols(alias, cols)

        return self

    def _where(self, condition, value, andor):
        """Add a WHERE condition"""

        cond = ''
        if len(self._wheres) > 0:
            cond = '%s ' % andor

        if value is not None:
            if isinstance(value, (basestring, int, float, bool)):
                self._bind += (value,)
            else:
                self._bind += value
                if len(value) > 1 and condition.count('?') == 1:
                    condition = condition.replace(
                                    '?', ', '.join('?' * len(value)))

        self._wheres.append('%s(%s)' % (cond, condition))

        return self

    def distinct(self, flag=True):
        """Add a DISTINCT directive to this SELECT statement"""
        self._distinct = flag
        return self

    def where(self, condition, value=None):
        """Add an AND WHERE condition"""
        return self._where(condition, value, 'AND')

    def or_where(self, condition, value=None):
        """Add an OR WHERE condition"""
        return self._where(condition, value, 'OR')

    def set_from(self, name, cols='*', schema=None):
        """Specify the FROM directive for this SELECT"""
        return self._join('FROM', name, None, cols, schema)

    def join(self, name, cond, cols='*', schema=None):
        """Join a table"""
        return self.inner_join(name, cond, cols, schema)

    def inner_join(self, name, cond, cols='*', schema=None):
        """Inner join a table"""
        return self._join('INNER JOIN', name, cond, cols, schema)

    def left_join(self, name, cond, cols='*', schema=None):
        """Left join a table"""
        return self._join('LEFT JOIN', name, cond, cols, schema)

    def right_join(self, name, cond, cols='*', schema=None):
        """Right join a table"""
        return self._join('RIGHT JOIN', name, cond, cols, schema)

    def full_join(self, name, cond, cols='*', schema=None):
        """Full join a table"""
        return self._join('FULL JOIN', name, cond, cols, schema)

    def cross_join(self, name, cond, cols='*', schema=None):
        """Cross join a table"""
        return self._join('CROSS JOIN', name, cond, cols, schema)

    def natural_join(self, name, cond, cols='*', schema=None):
        """Natural join a table"""
        return self._join('NATURAL JOIN', name, cond, cols, schema)

    def order(self, field, direction='ASC'):
        """Add an ORDER to this SELECT"""

        self._orders.append((
            field,
            'ASC' if direction.upper() == 'ASC' else 'DESC'
        ))
        return self

    def limit(self, limit, offset=None):
        """Add a LIMIT and OFFSET"""

        self._limit = limit
        self._offset = offset
        return self

    def _render_distinct(self):
        """Render the DISTINCT part of this SELECT"""

        sql = ''
        if self._distinct:
            sql = ' DISTINCT'

        return sql

    def _render_columns(self):
        """Render the columns part of this SELECT string"""

        columns = []
        for column in self._columns:

            name = ''

            if re.search(r'\(.*\)', column[1]) is not None:
                # Don't quote things that looks like functions
                name = column[1]
            else:
                name = '%s.%s' % (
                    DBHelper.quote_identifier(column[0]),
                    '*' if column[1] == '*'
                        else DBHelper.quote_identifier(column[1])
                )

            if column[2] is not None:
                name = '%s AS %s' % (
                    name,
                    DBHelper.quote_identifier(column[2])
                )

            columns.append(name)

        return ' %s' % ', '.join(columns)

    def _render_from(self):
        """Render the FROM part of this SELECT string"""

        froms = []

        for table in self._tables:

            join_type = ('INNER JOIN'
                            if table['join_type'] == 'FROM'
                            else table['join_type'])

            sql = ''
            if len(froms) > 0:
                sql += ' %s ' % join_type

            name = table['table_name']
            if table['schema'] is not None:
                name = '%.%' % (table['schema'], name)
            name = DBHelper.quote_identifier(name)

            if table['alias'] != table['table_name']:
                name = '%s AS %s' % (
                    name,
                    DBHelper.quote_identifier(table['alias'])
                )

            sql += name
            if len(froms) > 0 and table['join_condition']:
                sql += ' ON %s' % table['join_condition']

            froms.append(sql)

        return ' FROM %s' % '\n'.join(froms)

    def _render_where(self):
        """Render the WHERE part of this SELECT string"""

        sql = ''
        if len(self._wheres) > 0:
            sql = ' WHERE %s' % '\n\t'.join(self._wheres)

        return sql

    def _render_order(self):
        """Render the ORDER BY part of this SELECT"""

        sql = ''
        if len(self._orders) > 0:
            q = DBHelper.quote_identifier
            orders = []
            for order in self._orders:
                orders.append('%s %s' % (q(order[0]), order[1]))

            sql = ' ORDER BY %s' % ', '.join(orders)

        return sql

    def _render_limit(self):
        """Render the LIMIT and OFFSET parts of this SELECT"""

        sql = ''
        if self._limit is not None:
            sql = ' LIMIT'
            if self._offset is not None:
                sql += ' %d,' % self._offset
            sql += ' %d' % self._limit

        return sql

    def render(self):
        """Render a SQLite SELECT string"""

        sql = 'SELECT'
        sql += self._render_distinct()
        sql += self._render_columns()
        sql += self._render_from()
        sql += self._render_where()
        sql += self._render_order()
        sql += self._render_limit()
        return sql

    def query(self):
        """Execute this SELECT statement and return a sqlite3.Cursor"""
        return DBHelper().query(self.render(), self._bind)

