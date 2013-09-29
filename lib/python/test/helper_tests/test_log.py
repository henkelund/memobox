import unittest
from helper.log import LogHelper
from helper.install import InstallHelper
from helper.db import DBHelper
from model.log import LogModel

class TestLogHelper(unittest.TestCase):
    """LogHelper test case class"""

    def setUp(self):
        """LogHelper test set up"""

        InstallHelper.reset()

    def tearDown(self):
        """Clean up after test"""

        DBHelper().query(
            'DROP TABLE IF EXISTS %s'
                % DBHelper.quote_identifier(LogModel._table))
        InstallHelper.reset()

    def test_log(self):
        """Test LogHelper functions"""

        LogHelper.set_level(LogModel.WARN)
        entry = LogHelper.crit('Critical Error')
        self.assertGreater(entry.id(), 0)
        self.assertEqual(entry.message(), 'Critical Error')
        entry = LogHelper.warn('A Warning')
        self.assertGreater(entry.id(), 0)
        self.assertEqual(entry.message(), 'A Warning')
        entry = LogHelper.info('Just Information')
        self.assertIsNone(entry)
        LogHelper.set_level(LogModel.INFO)
        entry = LogHelper.info('Just Information')
        self.assertIsNotNone(entry)

