import unittest
from sqlite3 import Connection, OperationalError
from helper.db import DBHelper

class TestDBHelper(unittest.TestCase):
    """DBHelper test case class"""

    def setUp(self):
        """Initiate DBHelper singleton"""
        self._helper = DBHelper()

    def test_set_db(self):
        """Test DBHelper.set_db"""
        self.assertIsInstance(self._helper.get_connection(), Connection)
        self._helper.set_db(None)
        self.assertIsNone(self._helper.get_connection())
        self.assertRaises(OperationalError, self._helper.set_db, '.')

