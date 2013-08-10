import unittest
from helper.install import InstallHelper
from helper.db import DBHelper, DBSelect

class TestInstallHelper(unittest.TestCase):
    """InstallHelper test case class"""

    def test_install(self):
        """Test InstallHelper.install"""

        InstallHelper.reset()
        module = 'sample_module'
        q = DBHelper.quote_identifier
        install_routines = ["""
            CREATE TABLE IF NOT EXISTS %s (
                id INTEGER
            )
        """ % q(module)]
        InstallHelper.install(module, install_routines)
        self.assertIn('id', DBHelper().describe_table(module))
        self.assertEqual(InstallHelper.version(module), 1)
        install_routines.append(
            lambda: DBHelper().insert(module, [{'id': 1}, {'id': 2}]))
        InstallHelper.install(module, install_routines)
        self.assertEqual(
            DBSelect(module, {'c': 'COUNT(*)'}).query().fetchone()['c'],
            2
        )
        self.assertEqual(InstallHelper.version(module), 2)
        install_routines.append(
            'ALTER TABLE %s ADD COLUMN %s TEXT' % (q(module), q('col')))
        InstallHelper.install(module, install_routines)
        self.assertIn('col', DBHelper().describe_table(module))
        self.assertEqual(InstallHelper.version(module), 3)
        InstallHelper.reset()

