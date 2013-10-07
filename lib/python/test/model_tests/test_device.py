import unittest
from model.device import DeviceModel
from helper.install import InstallHelper
from helper.db import DBHelper
import os

class TestDeviceModel(unittest.TestCase):
    """DeviceModel test case class"""

    def setUp(self):
        """DeviceModel test set up"""

        if os.path.isfile('/tmp/box.db'):
            os.unlink('/tmp/box.db')
        DBHelper().set_db('/tmp/box.db')
        InstallHelper.reset()
        DeviceModel.install()

    def tearDown(self):
        """Clean up after test"""

        InstallHelper.reset()
        DBHelper().set_db(None)
        os.unlink('/tmp/box.db')

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

