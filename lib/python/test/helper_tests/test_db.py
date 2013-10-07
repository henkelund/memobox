import unittest, os
from sqlite3 import Connection, OperationalError, Cursor
from random import randint
from helper.db import DBHelper, DBSelect
import re

class TestDBHelper(unittest.TestCase):
    """DBHelper test case class"""

    def setUp(self):
        """Initiate DBHelper singleton"""

        if os.path.isfile('/tmp/box.db'):
            os.unlink('/tmp/box.db')
        DBHelper().set_db('/tmp/box.db')
        self._helper = DBHelper()
        self._helper.query("""
            CREATE TABLE "test_table" (
                "col_a" INTEGER PRIMARY KEY AUTOINCREMENT,
                "col_b" INTEGER
            )
        """)
        self._num_rows = randint(128, 255)
        for i in range(self._num_rows):
            self._helper.query(
                'INSERT INTO "test_table" ("col_b") VALUES (?)',
                [randint(0, 99)]
            )

    def tearDown(self):
        """Clean up after test"""

        DBHelper().set_db(None)
        os.unlink('/tmp/box.db')

    def test_set_db(self):
        """Test DBHelper.set_db"""

        self.assertIsInstance(self._helper.get_connection(), Connection)
        self._helper.set_db(None)
        self.assertIsNone(self._helper.get_connection())
        self.assertRaises(OperationalError, self._helper.set_db, '.')
        self._helper.set_db(':memory:')
        self.assertIsInstance(self._helper.get_connection(), Connection)

    def test_quote_identifier(self):
        """Test DBHelper identifier quoting"""

        quote = DBHelper.quote_identifier
        self.assertEqual(quote('id'), '"id"')
        self.assertEqual(quote('"id"'), '"""id"""')
        self.assertEqual(quote('tbl.col'), '"tbl"."col"')
        self.assertEqual(quote('tbl.col', 'tc'), '"tbl"."col" AS "tc"')

    def test_query(self):
        """Test query execution"""

        cursor = self._helper.query('SELECT DATE() AS "date"')
        self.assertIsInstance(cursor, Cursor)
        self.assertIn('date', cursor.fetchone().keys())
        self.assertRaises(OperationalError, self._helper.query, 'SYNTAX ERROR')

    def test_describe_table(self):
        """Test describing a table"""

        desc = self._helper.describe_table('test_table')
        self.assertIn('col_a', desc)
        self.assertIn('col_b', desc)
        self.assertNotIn('col_c', desc)
        self.assertEqual(desc['col_a']['pk'], 1)
        self.assertEqual(desc['col_b']['pk'], 0)
        self.assertEqual(desc['col_b']['type'], 'INTEGER')

    def test_insert(self):
        """Test helper insert method"""

        ids = self._helper.insert('test_table', (
            {'col_b': randint(0, 99)},
            {'col_b': randint(0, 99)},
            {'col_b': randint(0, 99)}
        ))
        self.assertEqual(len(ids), 3)
        self.assertEqual(ids[0] + 1, ids[1])
        self.assertEqual(ids[0] + 2, ids[2])
        last = ids[2]
        ids = self._helper.insert('test_table', {'col_b': randint(0, 99)})
        self.assertEqual(ids[0], last + 1)
        self.assertRaises(
            OperationalError,
            self._helper.insert,
            'missing_table',
            {'col_b': 0}
        )
        ids = self._helper.insert('test_table', {})
        self.assertEqual(len(ids), 0)

    def test_select_from(self):
        """Test the SELECT <columns> FROM part of DBSelect"""

        select = DBSelect('a')
        sql = re.sub(r'\s+', ' ', select.render())
        self.assertEqual(sql, 'SELECT "a".* FROM "a"')

        select.set_from('b', ())
        sql = re.sub(r'\s+', ' ', select.render())
        self.assertEqual(sql, 'SELECT "a".* FROM "b" INNER JOIN "a"')

        select.set_from('c', ('d', 'e'))
        sql = re.sub(r'\s+', ' ', select.render())
        self.assertEqual(
            sql,
            'SELECT "a".*, "c"."d", "c"."e" ' +
                'FROM "c" INNER JOIN "b" INNER JOIN "a"'
        )

        count = self._helper.query(
            DBSelect('test_table', {'count': 'COUNT(*)'}).render()
        ).fetchone()
        self.assertTrue(type(count['count']) == int)
        self.assertTrue(count['count'] >= 0)

    def test_select_columns(self):
        """Test DBSelect.columns"""

        select = DBSelect('a', {})
        select.columns({'c': 'b'})
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "a"."b" AS "c" FROM "a"'
        )
        select.left_join('b', 'a.b = b.a', {})
        select.columns('*', 'b')
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "a"."b" AS "c", "b".* FROM "a" LEFT JOIN "b" ON a.b = b.a'
        )

    def test_select_join(self):
        """Test the DBSelects' *_join mehtods"""

        self._helper.query('CREATE TABLE a (x INTEGER)')
        self._helper.query('CREATE TABLE b (y INTEGER)')
        self._helper.insert('a', ({'x': 1}, {'x': 2}, {'x': 3}))
        self._helper.insert('b', ({'y': 2}, {'y': 3}, {'y': 4}))
        sql = DBSelect('a', {'n': 'COUNT(*)'}).inner_join('b', 'a.x = b.y', ())
        self.assertTrue(self._helper.query(sql.render()).fetchone()['n'] == 2)
        sql = DBSelect('a', {'n': 'COUNT(*)'}).left_join('b', 'a.x = b.y', ())
        self.assertTrue(self._helper.query(sql.render()).fetchone()['n'] == 3)
        # Right and outer joins are currently not supported by SQLite
        #sql = DBSelect('a', {'n': 'COUNT(*)'}).right_join('b', 'a.x = b.y', ())
        #self.assertTrue(self._helper.query(sql.render()).fetchone()['n'] == 3)
        #sql = DBSelect('a', {'n': 'COUNT(*)'}).full_join('b', 'a.x = b.y', ())
        #self.assertTrue(self._helper.query(sql.render()).fetchone()['n'] == 4)

    def test_select_where(self):
        """Test the WHERE part of DBSelect"""

        select = DBSelect('test_table')
        select.where('"col_a" = ?', 1)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "test_table".* FROM "test_table" WHERE ("col_a" = ?)'
        )
        self.assertEqual(len(select.query().fetchall()), 1)
        select.or_where('"col_a" = ?', 2)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "test_table".* FROM "test_table" ' +
                'WHERE ("col_a" = ?) OR ("col_a" = ?)'
        )
        self.assertEqual(len(select.query().fetchall()), 2)
        select.where('"col_a" IN (?)', (3, 4, 5))
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "test_table".* ' +
                'FROM "test_table" ' +
                    'WHERE ("col_a" = ?) ' +
                        'OR ("col_a" = ?) ' +
                        'AND ("col_a" IN (?, ?, ?))'
        )
        self.assertEqual(len(select.query().fetchall()), 1)

    def test_select_distinct(self):
        """Test the DISTINCT directive"""

        select = DBSelect('a')
        select.distinct()
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT DISTINCT "a".* FROM "a"'
        )
        select.distinct(False)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "a".* FROM "a"'
        )

    def test_select_limit(self):
        """Test LIMIT and OFFSET parts"""

        select = DBSelect('test_table')
        select.limit(10)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "test_table".* FROM "test_table" LIMIT 10'
        )
        self.assertEqual(len(select.query().fetchall()), 10)
        select.limit(10, self._num_rows - 5)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "test_table".* FROM "test_table" LIMIT %d, 10'
                % (self._num_rows - 5,)
        )
        self.assertEqual(len(select.query().fetchall()), 5)

    def test_select_order(self):
        """Test the ORDER BY part of DBSelect"""

        self._helper.query('CREATE TABLE a (x INTEGER, y INTEGER)')
        self._helper.insert('a', (
            {'x': 1, 'y': 1},
            {'x': 2, 'y': 2},
            {'x': 3, 'y': 2},
        ))
        select = DBSelect('a').order('x')
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "a".* FROM "a" ORDER BY "x" ASC'
        )
        self.assertEqual(select.query().fetchone()['x'], 1)
        select = DBSelect('a').order('y', 'DESC').order('x')
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "a".* FROM "a" ORDER BY "y" DESC, "x" ASC'
        )
        self.assertEqual(select.query().fetchone()['x'], 2)

    def test_select_unset(self):
        """Test unsetting parts of SELECT"""

        select = DBSelect('a', {'c': 'col'}
                    ).left_join('b', 'a.c = b.d', {'d': 'col'}
                    ).where('a.col = ?', 1
                    ).order('b.d', 'DESC'
                    ).limit(1, 2
                    ).distinct(True)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT DISTINCT "a"."col" AS "c", "b"."col" AS "d" ' +
                'FROM "a" LEFT JOIN "b" ON a.c = b.d ' +
                'WHERE (a.col = ?) ' +
                'ORDER BY "b"."d" DESC ' +
                'LIMIT 2, 1'
        )
        select.unset(select.FROM | select.COLUMNS).set_from('x')
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT DISTINCT "x".* ' +
                'FROM "x" WHERE (a.col = ?) ORDER BY "b"."d" DESC LIMIT 2, 1'
        )
        select.unset(select.WHERE)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT DISTINCT "x".* ' +
                'FROM "x" ORDER BY "b"."d" DESC LIMIT 2, 1'
        )
        select.unset(select.DISTINCT | select.ORDER | select.LIMIT)
        self.assertEqual(
            re.sub(r'\s+', ' ', str(select)),
            'SELECT "x".* FROM "x"'
        )

    def test_select_clone(self):
        """Test cloning a SELECT"""

        select1 = DBSelect('a', {'c': 'col'}
                    ).left_join('b', 'a.c = b.d', {'d': 'col'}
                    ).where('a.col = ?', 1
                    ).order('b.d', 'DESC'
                    ).limit(1, 2
                    ).distinct(True)
        select2 = select1.clone()
        self.assertEqual(str(select1), str(select2))
        select2.or_where('b.col = ?', 1)
        self.assertNotEqual(str(select1), str(select2))
        select1.unset(select1.WHERE)
        select2.unset(select2.WHERE)
        self.assertEqual(str(select1), str(select2))

    def test_select_update(self):
        """Test executing UPDATEs based on SELECTs"""

        select = DBSelect('test_table').where('col_a = ?', 1)
        self.assertEqual(select.query_update({'col_b': 512}), 1)
        select = DBSelect('test_table').order('col_a').limit(3, 1)
        self.assertEqual(select.query_update({'col_b': 512}), 3)
        select = DBSelect('test_table').where('col_b = ?', 512)
        self.assertEqual(select.query_update({'col_b': 1024}), 4)

    def test_select_delete(self):
        """Test executing DELETEs based on SELECTs"""

        select = (DBSelect('test_table')
                    .order('col_a', 'DESC')
                    .limit(self._num_rows - 10))
        self.assertEqual(select.query_delete(), self._num_rows - 10)
        select = DBSelect('test_table').where('col_a = ?', 1)
        self.assertEqual(select.query_delete(), 1)
        select = DBSelect('test_table').where('col_a IN (?)', (1, 2, 3, 4))
        self.assertEqual(select.query_delete(), 3)

