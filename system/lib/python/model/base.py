from werkzeug.contrib.cache import BaseCache, NullCache
from helper.db import DBHelper, DBSelect
from helper.install import InstallHelper

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

    def clean_data(self, data):
        """Clean the given dict from non-savable data"""

        cache_key = 'DESCRIBE_%s' % self._table
        desc = self.__class__._cache.get(cache_key)
        if type(desc) is not dict:
            desc = DBHelper().describe_table(self._table)
            self.__class__._cache.set(cache_key, desc)

        clean_data = {}
        for key in data.keys():
            if key == self._pk:
                continue
            elif key in desc:
                #TODO: type cast?
                clean_data[key] = data[key]

        return clean_data

    def get_table(self):
        """"""
        return self._table or self.__class__._table

    def __init__(self, data={}):
        """Initialize class instance"""
        self._data = data.copy()
        self._init()

    def _init(self):
        """Internal constuctor"""
        pass

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

    def has_data(self, key):
        """Check if this model has data for a given key"""
        return key in self._data

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
        return DBSelect(self.get_table()
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

        data = self.clean_data(self._data)
        if self.id():
            self._db_select().query_update(data)
        else:
            ids = DBHelper().insert(self.get_table(), data)
            self.set_data(self.__class__._pk, ids[0])

        return self

    def delete(self):
        """Remove this model from the database"""

        if self.id():
            self._db_select().query_delete()
            self.unset_data(self.__class__._pk)

        return self

    @classmethod
    def _install(cls):
        """Return a list of install routines"""
        return ()

    @classmethod
    def install(cls):
        """Install model"""
        InstallHelper.install(cls._table, cls._install())

    @classmethod
    def all(cls):
        """Get a model collection"""
        return BaseModelSet(cls)

class BaseModelSet(DBSelect):
    """Base class for model collections"""

    def __init__(self, model_class):
        """Initialize"""

        self._model_class = model_class
        self._main_table = model_class._table
        self._total_size = None
        self.reset()
        super(BaseModelSet, self).__init__((self._main_table, 'm'))

    def __iter__(self):
        """Rewind internal pointer"""

        if self._current is not None:
            self._current = 0

        return self

    def __len__(self):
        """Implements len(self)"""
        return self.size()

    def __delitem__(self, key):
        """Implements array access deletion"""

        self.load()
        del self._items[key]

    def __getitem__(self, key):
        """Implements array access retrieval"""

        self.load()
        return self._items[key]

    def __setitem__(self, key, value):
        """Implements array access assignment"""

        self.load()
        self._items[key] = value

    def reset(self):
        """Clear this set to its initial state"""

        self._cursor = None
        self._current = None
        self._items = None
        self.unset(self.WHERE | self.ORDER | self.LIMIT | self.OFFSET)

        return self

    def next(self):
        """Implements iteration"""

        if self._cursor is None:
            self._cursor = self.query()
            self._items = []

        if self._current is None:
            data = self._cursor.fetchone()

            if type(data) is dict:
                model = self._model_class(data)
                model._table = self._main_table
                self._items.append(model)
                return model

            self._current = len(self._items)
            raise StopIteration
        else:
            if self._current < len(self._items):
                model = self._items[self._current]
                self._current += 1
                return model
            else:
                raise StopIteration

    def load(self):
        """Load all pending data into this model set"""

        if self._current is None:
            for model in self: # drains self._cursor
                pass

        return self

    def size(self):
        """Count the number of models in this set"""

        self.load()
        return len(self._items)

    def total_size(self, cache=True):
        """Retrieve the total number of stored objects"""

        if not cache or self._total_size is None:
            select = self.clone().unset(
                    self.ORDER | self.LIMIT | self.OFFSET | self.COLUMNS
                ).columns({'c': 'COUNT(*)'})
            self._total_size = select.query().fetchone()['c']
        return self._total_size

    def _prepare_filter_condition(self, spec):
        """Filter helper to determine condition based on value"""

        cond = '= ?'
        value = spec

        if type(spec) is dict:
            for key in spec.keys():
                lower = key.lower()
                if lower in ('eq', '=', '=='):
                    value = spec[key]
                elif lower in ('ne', 'neq', '!', '!=', '<>'):
                    cond = '!= ?'
                    value = spec[key]
                elif lower in ('gt', '>'):
                    cond = '> ?'
                    value = spec[key]
                elif lower in ('lt', '<'):
                    cond = '< ?'
                    value = spec[key]
                elif lower in ('ge', 'gte', '>='):
                    cond = '>= ?'
                    value = spec[key]
                elif lower in ('le', 'lte', '<='):
                    cond = '<= ?'
                    value = spec[key]
                elif lower == 'in':
                    cond = 'IN (?)'
                    value = spec[key]
                elif lower == 'null':
                    cond = 'IS NULL' if spec[key] else 'IS NOT NULL'
                    value = None
                elif lower == 'like':
                    cond = 'LIKE ?'
                    value = spec[key]
                elif lower in ('between', '><'):
                    cond = 'BETWEEN ? AND ?'
                    value = spec[key]

        return (cond, value)

    def _prepare_filter_attribute(self, attribute):
        """Prepare attribute for use in WHERE"""
        #TODO: check attribute against describe table?
        return DBHelper.quote_identifier(attribute)

    def add_filter(self, attribute, value):
        """Add a filter to this set"""

        if type(attribute) not in (list, tuple):
            attribute = (attribute,)
            value = (value,)

        for i in range(len(attribute)):
            op = ''
            cp = ''
            if len(attribute) > 1:
                if i == 0:
                    op = '('
                elif i == len(attribute) - 1:
                    cp = ')'
            attr = self._prepare_filter_attribute(attribute[i])
            cond = self._prepare_filter_condition(value[i])
            where = self.where if i == 0 else self.or_where
            where('%s%s %s%s' % (op, attr, cond[0], cp), cond[1])

        return self

