import unittest
from werkzeug.contrib.cache import FileSystemCache, NullCache
from model.base import BaseModel, BaseModelSet
from helper.db import DBHelper, DBSelect

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

    def test_model_all(self):
        """Test BaseModel.all"""

        modelset = SampleModel.all()
        self.assertIsInstance(modelset, BaseModelSet)

    def test_modelset_len(self):
        """Test len(BaseModelSet)"""

        count = DBSelect(
                    SampleModel._table,
                    'COUNT(*) as "c"'
                ).query().fetchone()['c']
        self.assertEqual(len(SampleModel.all()), count)
        self.assertEqual(len(SampleModel.all().limit(1)), 1)
        self.assertEqual(len(SampleModel.all().limit(0)), 0)
        models = SampleModel.all().limit(1)
        self.assertEqual(len(models), 1)
        self.assertEqual(models.total_size(False), count)
        self.assertEqual(models.total_size(True), count)

    def test_modelset_iteration(self):
        """Test BaseModelSet for loop"""

        models = SampleModel.all()
        c = len(models) # loads all models
        i = 0
        for model in models: # w/o resetting
            self.assertIsInstance(model, BaseModel)
            i = i + 1
        self.assertEqual(c, i)
        i = 0
        for model in models.reset():
            self.assertIsInstance(model, BaseModel)
            i = i + 1
        self.assertEqual(c, i)

    def test_modelset_array_access(self):
        """Test BaseModelSet array access"""

        models = SampleModel.all()
        for i in range(len(models)):
            self.assertIsInstance(models[i], BaseModel)
            models[i] = None
            self.assertIsNone(models[i])
        self.assertGreater(len(models), 0)
        for i in reversed(range(len(models))):
            del models[i]
        self.assertEqual(len(models), 0)
        self.assertRaises(IndexError, models.__getitem__, 0)
        self.assertRaises(IndexError, models.__setitem__, 0, None)
        self.assertRaises(IndexError, models.__delitem__, 0)

