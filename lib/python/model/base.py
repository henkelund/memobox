from werkzeug.contrib.cache import BaseCache, NullCache
from helper.db import DBHelper, DBSelect

class BaseModel(object):
    """Base class for models"""

    _table = None
    _pk = None
    _cache = NullCache()
    _data = {}

    @classmethod
    def set_cache(cls, cache):
        """Set a class level cache instance"""

        if isinstance(cache, BaseCache):
            cls._cache = cache

    @classmethod
    def clean_data(cls, data):
        """Clean the given dict from non-savable data"""

        cache_key = 'DESCRIBE_%s' % cls._table
        desc = cls._cache.get(cache_key)
        if type(desc) is not dict:
            desc = DBHelper().describe_table(cls._table)
            cls._cache.set(cache_key, desc)

        clean_data = {}
        for key in data.keys():
            if key == cls._pk:
                continue
            elif key in desc:
                #TODO: type cast?
                clean_data[key] = data[key]

        return clean_data

    def __init__(self, data={}):
        """Initialize class instance"""
        self._data = data.copy()

    def id(self):
        """Return primary key value of this model instance"""
        return self.get_data(self.__class__._pk)

    def get_data(self, key=None):
        """Retrieve attribute values from this model"""

        if key is None:
            return self._data
        elif key in self._data:
            return self._data[key]
        else:
            return None

    def set_data(self, key, value=None):
        """Update attribute values of this model"""

        if type(key) is dict:
            self._data = key
        else:
            self._data[key] = value

        return self

    def unset_data(self, key=None):
        """Remove attribute values from this model"""

        if type(key) is None:
            self._data = {}
        elif key in self._data:
            del self._data[key]

        return self

    def add_data(self, data):
        """Add attribute values to this model"""

        self._data.update(data)
        return self

    def __getattr__(self, name):
        """Magic proxy for 'get_data' and 'set_data'"""

        def getfnc(value=type(None)):
            if value is type(None):
                return self.get_data(name)
            else:
                return self.set_data(name, value)
        return getfnc

    def _db_select(self, key=None):
        """Return a DBSelect querying for this model"""

        if not key:
            key = self.__class__._pk
        where = '%s = ?' % (DBHelper.quote_identifier(key),)
        return DBSelect(self.__class__._table
                    ).where(where, self.get_data(key)).limit(1)

    def load(self, value, key=None):
        """Load data matching 'value' into this model"""

        if not key:
            key = self.__class__._pk
        self.set_data(key, value)
        data = self._db_select(key).query().fetchone()
        if type(data) is dict:
            self.add_data(data)
        else:
            self.unset_data(key)

        return self

    def save(self):
        """Store this models data"""

        data = self.__class__.clean_data(self._data)
        if self.id():
            del data[self.__class__._pk]
            self._db_select().query_update(data)
        else:
            ids = DBHelper().insert(self.__class__._table, data)
            self.set_data(self.__class__._pk, ids[0])

        return self

    def delete(self):
        """Remove this model from the database"""

        if self.id():
            self._db_select().query_delete()
            self.unset_data(self.__class__._pk)

        return self

