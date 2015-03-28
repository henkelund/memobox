import sqlite3 as sqlite
import re
from copy import deepcopy
from flask import jsonify, g

class DBHelper(object):
    """Helper class for SQLite DB access"""

    _instance = None

    def __new__(cls, db=':memory:', fullpath='no', *args, **kwargs):
        """Override __new__ to implement singleton pattern"""

        if g and not g.islocalbox:
	        if fullpath == 'yes' or not hasattr(g, "sqlite_db"):
	            g.sqlite_db = super(DBHelper, cls).__new__(cls, *args, **kwargs)
	            g.sqlite_db._conn = None
	            g.sqlite_db.set_db(db)
	        return g.sqlite_db
        else:
	        if not cls._instance:
	            cls._instance = super(DBHelper, cls).__new__(cls, *args, **kwargs)
	            cls._instance._conn = None
	            cls._instance.set_db(db)
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
            self._conn = sqlite.connect(db, isolation_level=None) # Auto-commit
            self._conn.row_factory = DBHelper._row_factory
            self._conn.text_factory = str
            self._conn.cursor().execute('PRAGMA foreign_keys = ON')

        return self

    def query(self, sql, bind = []):
        """Execute the given SQL and return a sqlite3.Cursor object"""
        return self._conn.cursor().execute(sql, bind)

    def describe_table(self, table):
        """Return a dict describing the given table"""

        desc = {}
        cursor = self.query('PRAGMA table_info(%s)'
                                % self.quote_identifier(table))
        for row in cursor.fetchall():
            desc[row['name']] = row

        return desc

    def insert(self, table, bind, ignore=False):
        """Insert data into a table."""

        if type(bind) is dict:
            bind = (bind,)

        ids = []
        for row in bind:
            if not row:
                continue
            cols = [self.quote_identifier(key) for key in row.keys()]
            ign = ' OR IGNORE ' if ignore else ' '
            sql = 'INSERT%sINTO %s (%s) VALUES (%s)' % (
                ign,
                self.quote_identifier(table),
                ', '.join(cols),
                ', '.join('?' * len(row))
            )

            ids.append(self.query(sql, row.values()).lastrowid)

        return ids
        
    @staticmethod
    def islocal():
        return True

    @staticmethod
    def initdb(filename="index.db", fullpath=False):
    	dbname = ""
    	
        if fullpath:
            DBHelper(filename, 'yes')
        else:
			DBHelper("../data/"+filename)

    @staticmethod
    def loadconfig(username=None, dbfile=""):
        config = {}
        if dbfile is "":
            if username is not None:
                dbfile = "/backups/"+username+"/local.cfg"
            elif hasattr(g, "islocalbox") and g.islocalbox is False and hasattr(g, "username"):
                dbfile = "/backups/"+g.username+"/local.cfg"

            else:
                dbfile = "../data/local.cfg"

        with open(dbfile) as f:
            content = f.readlines()
        
        for line in content:
            if len(line.split("=")) == 2:
                config[line.split("=")[0]] = line.split("=")[1].replace('"', '').replace('\n', '')
            
        g.config = config
        
        return g.config

    @staticmethod
    def saveconfig(config, username=None, dbfile=""):
        if dbfile is "":
            if g.islocalbox is True:
                dbfile = "../data/local.cfg"
            elif username is not None:
                dbfile = "/backups/"+username+"/local.cfg"
            elif hasattr(g, "username"):
                dbfile = "/backups/"+g.username+"/local.cfg"

        RE = '(('+'|'.join(config.keys())+')\s*=)[^\r\n]*?(\r?\n|\r)'
        pat = re.compile(RE)

        def jojo(mat,dic = config ):
            return dic[mat.group(2)].join(mat.group(1,3))

        with open(dbfile,'rb') as f:
            content = f.read() 

        pat = re.compile(RE)

        with open(dbfile,'wb') as f:
            f.write(pat.sub(jojo,content))

        return DBHelper.loadconfig()
        
class DBSelect(object):
    """Helper for building SQLite SELECT queries"""

    DISTINCT = 1 << 0
    COLUMNS = 1 << 1
    FROM = 1 << 2
    WHERE = 1 << 3
    GROUP = 1 << 4    
    ORDER = 1 << 5
    LIMIT = 1 << 6
    OFFSET = 1 << 7
    ALL = DISTINCT | COLUMNS | FROM | WHERE | GROUP | ORDER | LIMIT | OFFSET

    def __init__(self, table, cols='*'):
        """Constructor"""

        self.unset(self.ALL)
        self.set_from(table, cols)

    def unset(self, parts=None):
        """Reset parts or all of this SELECT"""

        if parts is None:
            parts = self.ALL

        if parts & self.DISTINCT:
            self._distinct = False
        if parts & self.COLUMNS:
            self._columns = []
        if parts & self.FROM:
            self._tables = []
        if parts & self.WHERE:
            self._wheres = []
            self._bind = []
        if parts & self.GROUP:
            self._groups = []
        if parts & self.ORDER:
            self._orders = []
        if parts & self.LIMIT:
            self._limit = None
        if parts & self.OFFSET:
            self._offset = None

        return self

    def clone(self):
        """Create a copy of this SELECT"""

        clone = DBSelect('')
        clone._distinct = self._distinct
        clone._columns = deepcopy(self._columns)
        clone._tables = deepcopy(self._tables)
        clone._wheres = deepcopy(self._wheres)
        clone._bind = deepcopy(self._bind)
        clone._groups = deepcopy(self._groups)
        clone._orders = deepcopy(self._orders)
        clone._limit = self._limit
        clone._offset = self._offset
        return clone

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

    def columns(self, cols='*', table=None, reset=False):
        """Add columns to SELECT"""

        if reset == True:
        	self._columns = []
        	
        if table is None and self._tables:
            table = self._tables[0]['alias']

        self._table_cols(table, cols)
        return self

    def join(self, name, cond, cols='*', schema=None):
        """Join a table"""
        return self.inner_join(name, cond, cols, schema)

    def inner_join(self, name, cond, cols='*', schema=None):
        """Inner join a table"""
        return self._join('INNER JOIN', name, cond, cols, schema)

    def left_join(self, name, cond, cols='*', schema=None):
        """Left join a table"""
        return self._join('LEFT JOIN', name, cond, cols, schema)

    def left_outer_join(self, name, cond, cols='*', schema=None):
        """Left outer join a table"""
        return self._join('LEFT OUTER JOIN', name, cond, cols, schema)

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

    def group(self, field):
        """Add an GROUP to this SELECT"""

        self._groups.append((
            field
        ))

        return self


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

    def _table_to_string(self, table):
        """Convert the internal table representation to a string"""

        name = table['table_name']
        if table['schema'] is not None:
            name = '%.%' % (table['schema'], name)
        name = DBHelper.quote_identifier(name)

        if table['alias'] != table['table_name']:
            name = '%s AS %s' % (
                name,
                DBHelper.quote_identifier(table['alias'])
            )

        return name

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

            sql += self._table_to_string(table)
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

    def _render_group(self):
        """Render the ORDER BY part of this SELECT"""

        sql = ''
        if len(self._groups) > 0:
            q = DBHelper.quote_identifier
            groups = []
            for group in self._groups:
                groups.append('%s' % (q(group)))

            sql = ' GROUP BY %s' % ', '.join(groups)

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
        sql += self._render_group()
        sql += self._render_order()
        sql += self._render_limit()
        return sql

    def query(self):
        """Execute this SELECT statement and return a sqlite3.Cursor"""
        return DBHelper().query(self.render(), self._bind)

    def query_update(self, bind):
        """Issue an UPDATE query based on this SELECT"""

        sql = 'UPDATE'
        values = []
        if self._tables:
            sql = '%s %s' % (sql, self._table_to_string(self._tables[0]))
        if type(bind) == dict and dict:
            sql += ' SET '
            fields = []
            for key in bind:
                values += (bind[key],)
                fields.append('%s = ?' % (DBHelper.quote_identifier(key),))
            sql += ', '.join(fields)
        sql += self._render_where()
        sql += self._render_order()
        sql += self._render_limit()
        values += self._bind
        cursor = DBHelper().query(sql, values)
        return cursor.rowcount

    def query_delete(self):
        """Issue a DELETE query based on this SELECT"""

        sql = 'DELETE FROM'
        if self._tables:
            sql = '%s %s' % (sql, self._table_to_string(self._tables[0]))
        sql += self._render_where()
        sql += self._render_order()
        sql += self._render_limit()
        cursor = DBHelper().query(sql, self._bind)
        return cursor.rowcount

