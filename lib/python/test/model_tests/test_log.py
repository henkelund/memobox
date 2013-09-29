import unittest
from model.log import LogModel
from helper.install import InstallHelper
from helper.db import DBHelper
from datetime import datetime

class TestLogModel(unittest.TestCase):
    """LogModel test case class"""

    def setUp(self):
        """LogModel test set up"""

        InstallHelper.reset()
        LogModel.install()

    def tearDown(self):
        """Clean up after test"""

        DBHelper().query(
            'DROP TABLE IF EXISTS %s'
                % DBHelper.quote_identifier(LogModel._table))
        InstallHelper.reset()

    def test_add_entry(self):
        """Test adding a log entry"""

        message = 'A Debug Message'
        LogModel({'message': message}).save()
        self.assertEqual(
            LogModel.all().limit(1).next().message(),
            message
        )

