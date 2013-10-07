import unittest
from helper.install import InstallHelper
from helper.db import DBHelper
from model.file import (
    FileModel,
    VISIBILITY_VISIBLE,
    VISIBILITY_HIDDEN,
    VISIBILITY_IN_HIDDEN_DIR
)
import os, hashlib

class TestFileModel(unittest.TestCase):
    """FileModel test case class"""

    def setUp(self):
        """ExtendedModel test set up"""

        if os.path.isfile('/tmp/box.db'):
            os.unlink('/tmp/box.db')
        DBHelper().set_db('/tmp/box.db')
        InstallHelper.reset()
        FileModel.install()

    def tearDown(self):
        """Clean up after test"""

        InstallHelper.reset()
        DBHelper().set_db(None)
        os.unlink('/tmp/box.db')
        FileModel._group_index = {} # clear cached attr groups

    def _get_file(self, ext):
        """Get a file by extension"""
        for r, d, f in os.walk('fixture'):
            for filename in f:
                if filename.endswith('.%s' % ext.lstrip('.')):
                    return os.path.join(r, filename)
        return None

    def test_guesswork(self):
        """Test file factory helper functions"""

        file_type = FileModel.guess_type('bild.JPG')
        self.assertEqual(file_type[0], 'image/jpeg')
        extension = FileModel.guess_extension('bild.JPG')
        self.assertEqual(extension, 'jpg')
        extension = FileModel.guess_extension('bild')
        self.assertIsNone(extension)
        extension = FileModel.guess_extension('bild', file_type[0])
        self.assertEqual(extension, 'jpe')
        vis = FileModel.guess_visibility
        self.assertEqual(vis('/path/to/visible'), VISIBILITY_VISIBLE)
        self.assertEqual(vis('/path/to/.hidden'), VISIBILITY_HIDDEN)
        self.assertEqual(vis('/path/.to/hidden'), VISIBILITY_IN_HIDDEN_DIR)
        self.assertEqual(vis('/.path/to/.hidden'),
                                VISIBILITY_IN_HIDDEN_DIR | VISIBILITY_HIDDEN)

    def test_checksum(self):
        """Test file checksum calculator"""

        filename = self._get_file('txt')
        contents = ''
        with open(filename) as fh:
            contents = fh.read()
        hasher = hashlib.sha256()
        hasher.update(contents)
        self.assertEqual(
            FileModel.calculate_checksum(filename, 1),
            hasher.hexdigest())

    def test_factory(self):
        """Test file factory function"""

        filename = self._get_file('txt')
        pk = FileModel.factory(filename).save().id()
        self.assertIsNotNone(pk)
        model = FileModel().load(pk)
        self.assertEqual(model.name(), os.path.basename(filename))
        self.assertEqual(model.extension(), 'txt')
        self.assertEqual(
            model.abspath(),
            os.path.dirname(os.path.abspath(filename)))

    def test_image_type(self):
        """Test image specific functionality"""

        filename = self._get_file('jpg')
        pk = FileModel.factory(filename).save().id()
        model = FileModel().load(pk)
        self.assertGreater(model.width(), 0)
        self.assertGreater(model.height(), 0)

