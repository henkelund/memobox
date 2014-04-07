from base import BaseModel, BaseModelSet
from helper.db import DBHelper, DBSelect
from helper.install import InstallHelper

class AttributeModel(BaseModel):
    """Extended attribute model"""

    _pk = '_id'

    def __init__(self, data={}, parent=None, datatype=None):
        """Initialize attribute model by parent table and data type"""

        super(AttributeModel, self).__init__(data)
        if parent is not None and datatype is not None:
            self._table = '%s_attribute_%s' % (parent, datatype)

    def all(self):
        """Get an attribute model collection"""
        return AttributeModelSet(self)

class AttributeModelSet(BaseModelSet):
    """Attribute collection class"""

    def __init__(self, model):
        """Initialize"""

        self._model_class = model.__class__
        self._main_table = model._table
        self._total_size = None
        self.reset()
        super(BaseModelSet, self).__init__((model._table, 'm'))

class ExtendedModel(BaseModel):
    """Base class for extended models"""

    _table = 'extended_model' # used for install helper reference
    _group_index = {}

    def _init(self):
        """Internal constuctor"""
        self._stored_attrs = None

    def load(self, value, key=None):
        """Load data matching 'value' into this model"""

        super(ExtendedModel, self).load(value, key)
        if self.id():
            self._load_extended_data(True)

        #TODO: Try to load by extended attribute if parent load fails

        return self

    def save(self):
        """Store this extended models data"""

        #TODO: Implement transaction support in DBHelper

        super(ExtendedModel, self).save()
        self._load_extended_data(False)

        updated = False
        attrs = self.get_attributes()
        if attrs is None:
            return self

        for attr in attrs:
            code = attr['code']
            if not code in self._data:
                continue
            if code in self._stored_attrs:
                stored_attr = self._stored_attrs[code]
                if self._data[code] is None:
                    stored_attr.delete()
                    updated = True
                else:
                    if stored_attr.value() != self._data[code]:
                        stored_attr.value(self._data[code]).save()
                        updated = True
            elif self._data[code] is not None:
                AttributeModel({
                        'attribute': attr['_id'],
                        'parent': self.id(),
                        'value': self._data[code]
                    },
                    attr['parent'],
                    attr['type']
                ).save()
                updated = True

        if updated: # invalidate load cache
            self._stored_attrs = None

        return self

    def _load_extended_data(self, force=False):
        """Load values from related attribute tables into this model"""

        if not force and type(self._stored_attrs) is dict:
            return self
        elif not self.id():
            return self

        attrs = self.get_attributes()
        if not type(attrs) is list or len(attrs) == 0:
            return self

        attr_ids = {'text': [], 'integer': [], 'real': [], 'blob': []}
        attr_codes = {}
        for attr_data in attrs:
            attr_ids[attr_data['type']].append(attr_data['_id'])
            attr_codes[attr_data['_id']] = attr_data['code']

        self._stored_attrs = {}
        for datatype in attr_ids.keys():
            if not len(attr_ids[datatype]):
                continue
            attr_set = AttributeModel({}, self._table, datatype).all(
                            ).where('parent = ?', self.id()
                            ).where('attribute IN (?)', attr_ids[datatype])
            for attr_model in attr_set:
                code = attr_codes[attr_model.attribute()]
                if not self.has_data(code):
                    self.set_data(code, attr_model.value())
                self._stored_attrs[code] = attr_model

        return self

    def get_attribute_group(self):
        """Implement in subclass"""
        return None

    def get_attributes(self):
        """Get attributes related to this model and group"""
        return self.get_all_attributes(self.get_attribute_group())

    @classmethod
    def get_all_attributes(cls, group=None):
        """Get attributes related to this model class"""

        parent = cls._table

        if not parent:
            return None

        cache_key = 'ATTRIBUTES_%s' % parent
        if group is not None:
            group = cls._get_attribute_group(group)
            if group is None:
                return None
            cache_key = '%s_%d' % (cache_key, group)

        attributes = cls._cache.get(cache_key)
        if type(attributes) is list:
            return attributes

        select = DBSelect(('attribute_group', 'g'), ()
                    ).inner_join(
                        ('attribute_group_attribute', 'ga'),
                        '"g"."_id" = "ga"."group"', ()
                    ).inner_join(
                        ('attribute', 'a'),
                        '"ga"."attribute" = "a"."_id"'
                    ).where('"a"."parent" = ?', parent)

        if group is not None:
            select.where('"g"."_id" = ?', group)

        attributes = select.query().fetchall()
        if type(attributes) is list:
            cls._cache.set(cache_key, attributes)

        return attributes

    @classmethod
    def _get_attribute_table(cls, datatype):
        """Get attribute table name for the given data type"""
        return '%s_attribute_%s' % (cls._table, datatype)

    @classmethod
    def _get_attribute_group(cls, group_id, create=False):
        """Retrieve an attribute group id"""

        if (cls._table in cls._group_index
                and group_id in cls._group_index[cls._table]):
            return cls._group_index[cls._table][group_id]

        group_desc = {
            '_id': group_id,
            'code': str(group_id).replace(' ', '_'),
            'label': str(group_id.replace('_', ' ')).capitalize()
        }

        cls._group_index[cls._table] = {}
        for field in ('_id', 'code', 'label'):
            select = DBSelect('attribute_group').where(
                            '%s = ?' % field, group_desc[field]).where(
                            'type = ?', cls._table).limit(1)
            group = select.query().fetchone()
            if type(group) is dict:
                cls._group_index[cls._table][group_id] = group['_id']
                return cls._group_index[cls._table][group_id]

        if not create:
            return None

        ids = DBHelper().insert('attribute_group', {
            'code': group_desc['code'],
            'label': group_desc['label'],
            'type': cls._table
        })

        if len(ids) > 0:
            cls._group_index[cls._table][group_id] = ids[0]
            return cls._group_index[cls._table][group_id]

        return None

    @classmethod
    def _create_attribute(cls, code, label, datatype, groups):
        """Create a new attribute for this model"""

        ids = DBHelper().insert('attribute', {
            'code': code,
            'label': label,
            'parent': cls._table,
            'type': datatype
        })
        
        for group in groups: 
	        group_id = cls._get_attribute_group(group, True)
	        for new_id in ids:
	            DBHelper().insert('attribute_group_attribute', {
	                'group': group_id,
	                'attribute': new_id
	            })

    @classmethod
    def _create_attribute_tables(cls):
        """Install attribute tables for this model"""

        q = DBHelper.quote_identifier
        for datatype in ('text', 'integer', 'real', 'blob'):
            table_name = cls._get_attribute_table(datatype)
            idx = '%s_ATTR_%s' % (cls._table.upper(), datatype.upper())            

            DBHelper().query("""
                CREATE TABLE %s (
                    "_id"       INTEGER PRIMARY KEY AUTOINCREMENT,
                    "attribute" INTEGER,
                    "parent"    INTEGER,
                    "value"     %s,
                    FOREIGN KEY ("attribute") REFERENCES "attribute"("_id")
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY ("parent") REFERENCES %s(%s)
                        ON DELETE CASCADE ON UPDATE CASCADE
                );
                """ % (q(table_name), datatype.upper(),
                            q(cls._table), q(cls._pk))
            )
            DBHelper().query("""
                CREATE UNIQUE INDEX "UNQ_%s_ATTR_PARENT"
                    ON %s ("attribute", "parent");
                """ % (idx, q(table_name))
            )
            DBHelper().query("""
                CREATE INDEX "IDX_%s_ATTR" ON %s ("attribute");
                """ % (idx, q(table_name))
            )
            DBHelper().query("""
                CREATE INDEX "IDX_%s_PARENT" ON %s ("parent");
                """ % (idx, q(table_name))
            )
            DBHelper().query("""
                CREATE INDEX "IDX_%s_VALUE" ON %s ("value");
                """ % (idx, q(table_name))
            )

    @classmethod
    def _install(cls):
        """Install attribute meta data tables"""

        return (
            lambda: (
                DBHelper().query("""
                    CREATE TABLE "attribute" (
                        "_id"    INTEGER PRIMARY KEY AUTOINCREMENT,
                        "code"   TEXT NOT NULL DEFAULT "",
                        "label"  TEXT NOT NULL DEFAULT "",
                        "parent" TEXT NOT NULL DEFAULT "",
                        "type"   TEXT NOT NULL DEFAULT ""
                    )
                """),
                DBHelper().query("""
                    CREATE TABLE "attribute_group" (
                        "_id"   INTEGER PRIMARY KEY AUTOINCREMENT,
                        "code"  TEXT NOT NULL DEFAULT "",
                        "label" TEXT NOT NULL DEFAULT "",
                        "type"  TEXT NOT NULL DEFAULT ""
                    )
                """),
                DBHelper().query("""
                    CREATE TABLE "attribute_group_attribute" (
                        "_id"       INTEGER PRIMARY KEY AUTOINCREMENT,
                        "group"     TEXT NOT NULL DEFAULT "",
                        "attribute" TEXT NOT NULL DEFAULT "",
                        FOREIGN KEY ("group") REFERENCES "attribute_group"("_id")
                            ON DELETE CASCADE ON UPDATE CASCADE,
                        FOREIGN KEY ("attribute") REFERENCES "attribute"("_id")
                            ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """)
            ),
        )

    @classmethod
    def all(cls):
        """Get an extended model collection"""
        return ExtendedModelSet(cls)

class ExtendedModelSet(BaseModelSet):
    """Base class for extended model set"""

    def _prepare_filter_attribute(self, attribute):
        """Prepare attribute for use in WHERE"""

        if not hasattr(self, '_attrs'):
            self._attrs = self._model_class.get_all_attributes()

        if not hasattr(self, '_joined_attrs'):
            self._joined_attrs = {}

        # if this attributes value table hasn't already been joined
        if attribute not in self._joined_attrs.keys():

            attr_model = None
            for attr in self._attrs:
                if attr['code'] == attribute:
                    attr_model = attr
                    break

            # attribute not found, check if it could be a static column
            if attr_model is None:
                return super(ExtendedModelSet, self
                                )._prepare_filter_attribute(attribute)

            q = DBHelper.quote_identifier
            alias = '_%s_tbl' % attribute
            table = (
                self._model_class._get_attribute_table(attr_model['type']),
                alias
            )
            conds = (
                # match main table pk against attribute value table parent
                '%s = %s' % (
                    q('m.%s' % self._model_class._pk), q('%s.parent' % alias)
                ),
                # match value attribute id against attribute id
                '%s = %d' % (
                    q('%s.attribute' % alias), attr_model[AttributeModel._pk]
                )
            )
            self.left_join(table, ' AND '.join(conds), {attribute: 'value'})
            self._joined_attrs[attribute] = q('%s.value' % alias)

        return self._joined_attrs[attribute]

