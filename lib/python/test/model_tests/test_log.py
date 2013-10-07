import unittest, os
from model.log import LogModel
from helper.install import InstallHelper
from helper.db import DBHelper
from datetime import datetime

class TestLogModel(unittest.TestCase):
    """LogModel test case class"""

    def setUp(self):
        """LogModel test set up"""

        if os.path.isfile('/tmp/box.db'):
            os.unlink('/tmp/box.db')
        DBHelper().set_db('/tmp/box.db')
        InstallHelper.reset()
        LogModel.install()

    def tearDown(self):
        """Clean up after test"""

        InstallHelper.reset()
        DBHelper().set_db(None)
        os.unlink('/tmp/box.db')

    def test_add_entry(self):
        """Test adding a log entry"""

        message = 'A Debug Message'
        LogModel({'message': message}).save()
        self.assertEqual(
            LogModel.all().limit(1).next().message(),
            message
        )

