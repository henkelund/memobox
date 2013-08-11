import unittest
from model.device import DeviceModel
from helper.install import InstallHelper
from helper.db import DBHelper
import os

class TestDeviceModel(unittest.TestCase):
    """DeviceModel test case class"""

    def setUp(self):
        """DeviceModel test set up"""

        InstallHelper.reset()
        DeviceModel.install()

    def tearDown(self):
        """Clean up after test"""

        DBHelper().query(
            'DROP TABLE IF EXISTS %s'
                % DBHelper.quote_identifier(DeviceModel._table))
        InstallHelper.reset()

    def test_get_transfer_dirs(self):
        """Test DeviceModel.get_transfer_dirs"""

        device = DeviceModel()
        device.directory('marklar')
        self.assertEqual(len(device.get_transfer_dirs()), 0)
        device.directory('fixture/device')
        dirs = device.get_transfer_dirs()
        self.assertTrue(len(device.get_transfer_dirs()) > 0)
        for d in dirs:
            self.assertTrue(os.path.isdir(d))

    def test_load_by_dir(self):
        """Test DeviceModel.load_by_dir"""

        device = DeviceModel().load_by_dir('marklar')
        self.assertIsNone(device.id())
        device = DeviceModel().load_by_dir('fixture')
        self.assertIsNone(device.id())
        device = DeviceModel().load_by_dir('fixture/device')
        self.assertEqual(device.id(), 1)

