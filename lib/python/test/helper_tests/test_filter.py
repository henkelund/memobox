import unittest, os
from helper.filter import FilterHelper
from helper.db import DBHelper, DBSelect
from helper.install import InstallHelper
from model.file import FileModel

class TestFilterHelper(unittest.TestCase):
    """FilterHelper test case class"""

    def setUp(self):
        """FilterHelper test set up"""

        if os.path.isfile('/tmp/box.db'):
            os.unlink('/tmp/box.db')
        DBHelper().set_db('/tmp/box.db')
        InstallHelper.reset()
        FilterHelper.install()

    def tearDown(self):
        """Clean up after test"""

        InstallHelper.reset()
        DBHelper().set_db(None)
        os.unlink('/tmp/box.db')
        FileModel._group_index = {} # clear cached attr groups

    def test_filter(self):
        """Test FilterHelper functions"""

        # create a type filter
        type_filter = FilterHelper.create_filter('type', 'Type')
        FilterHelper.add_filter_option(type_filter, 1, 'Text')
        FilterHelper.add_filter_option(type_filter, 2, 'Audio')
        FilterHelper.add_filter_option(type_filter, 3, 'Image')

        # create a size filter
        size_filter = FilterHelper.create_filter('size', 'Size')
        FilterHelper.add_filter_option(size_filter, 1, 'Small')
        FilterHelper.add_filter_option(size_filter, 2, 'Medium')
        FilterHelper.add_filter_option(size_filter, 3, 'Large')

        f = FileModel({
            'name': 'textfile',
            'type': 'text',
            'size': '10'
        }).save()
        FilterHelper.set_filter_values(f, 'type', 1)
        FilterHelper.set_filter_values(f, 'size', 1)

        f = FileModel({
            'name': 'audiofile',
            'type': 'audio',
            'size': '100'
        }).save()
        FilterHelper.set_filter_values(f, 'type', 2)
        FilterHelper.set_filter_values(f, 'size', 2)

        f = FileModel({
            'name': 'hybridfile',
            'type': 'hybrid',
            'size': '1000'
        }).save()
        FilterHelper.set_filter_values(f, 'type', (1, 3))
        FilterHelper.set_filter_values(f, 'size', (2, 3))

        fileset = FileModel.all()
        FilterHelper.apply_filter('type', 1, fileset)

        # fileset should contain 'textfile' and 'hybridfile'
        self.assertEqual(len(fileset), 2)
        self.assertIn(fileset[0].name(), ('textfile', 'hybridfile'))
        self.assertIn(fileset[1].name(), ('textfile', 'hybridfile'))

        fileset = FileModel.all()
        FilterHelper.apply_filter('size', 2, fileset)

        # fileset should contain 'audiofile' and 'hybridfile'
        self.assertEqual(len(fileset), 2)
        self.assertIn(fileset[0].name(), ('audiofile', 'hybridfile'))
        self.assertIn(fileset[1].name(), ('audiofile', 'hybridfile'))

        fileset = FileModel.all()
        FilterHelper.apply_filter('type', 1, fileset)
        FilterHelper.apply_filter('size', 2, fileset)

        # fileset should only contain 'hybridfile'
        self.assertEqual(len(fileset), 1)
        self.assertEqual(fileset[0].name(), 'hybridfile')

