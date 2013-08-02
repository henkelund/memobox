import unittest
from sqlite3 import Connection, OperationalError, Cursor
from random import randint
from helper.db import DBHelper

class TestDBHelper(unittest.TestCase):
    """DBHelper test case class"""

    def setUp(self):
        """Initiate DBHelper singleton"""

        self._helper = DBHelper()
        self._helper.query("""
            CREATE TABLE 'test_table' (
                "col_a" INTEGER PRIMARY KEY AUTOINCREMENT,
                "col_b" INTEGER
            )
        """)

    def tearDown(self):
        """Clean up after test"""

        if self._helper.get_connection() is not None:
            self._helper.query("DROP TABLE 'test_table'")

    def test_set_db(self):
        """Test DBHelper.set_db"""

        self.assertIsInstance(self._helper.get_connection(), Connection)
        self._helper.set_db(None)
        self.assertIsNone(self._helper.get_connection())
        self.assertRaises(OperationalError, self._helper.set_db, '.')

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

