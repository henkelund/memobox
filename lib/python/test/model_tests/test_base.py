import unittest
from werkzeug.contrib.cache import FileSystemCache, NullCache
from model.base import BaseModel
from helper.db import DBHelper

class SampleModel(BaseModel):
    _table = 'sample_model'
    _pk = '_id'

class TestBaseModel(unittest.TestCase):
    """BaseModel test case class"""

    def setUp(self):
        """BaseModel test set up"""

        cache = FileSystemCache('/tmp/werkzeug')
        cache.clear()
        BaseModel.set_cache(cache)
        self._db = DBHelper()
        self._db.query("""
            CREATE TABLE "sample_model" (
                "_id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "some_attribute" INTEGER,
                "another_attribute" TEXT
            )
        """)
        self._db.insert(SampleModel._table, (
            {'_id': 1, 'some_attribute': 10, 'another_attribute': 'ten'},
            {'_id': 2, 'some_attribute': 20, 'another_attribute': 'twenty'},
            {'_id': 3, 'some_attribute': 30, 'another_attribute': 'thirty'}
        ))

    def tearDown(self):
        """Clean up after test"""
        self._db.query('DROP TABLE IF EXISTS "sample_model"')

    def test_set_cache(self):
        """Test BaseModel.set_cache"""

        self.assertIsInstance(BaseModel._cache, FileSystemCache)
        old_cache = BaseModel._cache
        BaseModel.set_cache(NullCache())
        self.assertIsInstance(BaseModel._cache, NullCache)
        SampleModel.set_cache(old_cache)
        self.assertIsInstance(BaseModel._cache, NullCache)
        self.assertIsInstance(SampleModel._cache, FileSystemCache)

    def test_clean_data(self):
        """Test BaseModel.clean_data"""

        sample_data = {'some_attribute': 10, 'nonexistent': '...'}
        clean_data = SampleModel.clean_data(sample_data)
        self.assertEqual(clean_data, {'some_attribute': 10})

    def test_id(self):
        """Test BaseModel.id"""

        model = SampleModel({SampleModel._pk: 'primary_key_value'})
        self.assertEqual(model.id(), 'primary_key_value')

    def test_get_set_unset_add(self):
        """Test BaseModel getters / setters"""

        model = SampleModel()
        model.set_data({'one': -1, 'two': -1})
        model.set_data({'two': 2})
        model.add_data({'one': 1, 'three': 3, 'five': 5})
        model.set_data('four', 4)
        model.unset_data('five')
        self.assertEqual(model.get_data(), {'one': 1, 'two': 2, 'three': 3, 'four': 4})
        self.assertEqual(model.get_data('three'), 3)
        self.assertEqual(model.four(), 4)
        model.four('IV')
        self.assertEqual(model.get_data('four'), 'IV')
        self.assertEqual(model.four(), 'IV')

    def test_load(self):
        """Test BaseModel.load"""

        model = SampleModel()
        model.load(2)
        self.assertEqual(model.id(), 2)
        self.assertEqual(model.another_attribute(), 'twenty')
        model.load(100)
        self.assertIsNone(model.id())
        model.load('thirty', 'another_attribute')
        self.assertEqual(model.some_attribute(), 30)

    def test_save(self):
        """Test BaseModel.save"""

        model = SampleModel()
        model.set_data({'some_attribute': 40, 'another_attribute': 'fourty'})
        model.save()
        self.assertIsNotNone(model.id())
        model2 = SampleModel().load(model.id())
        self.assertEqual(model2.some_attribute(), 40)

    def test_delete(self):
        """Test BaseModel.delete"""

        model = SampleModel().load(3)
        self.assertEqual(model.id(), 3)
        model.delete()
        self.assertIsNone(model.id())
        model2 = SampleModel().load(3)
        self.assertEqual(model2.get_data(), {})

