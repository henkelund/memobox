from helper.install import InstallHelper
from helper.db import DBHelper, DBSelect
from model.file import FileModel

class FilterHelper(object):
    """Filter helper class"""

    _filter_table = 'file_filter'
    _filter_option_table = 'file_filter_option'
    _filter_value_table = 'file_filter_value'

    @classmethod
    def get_filter_id(cls, filter_id):
        """Find filter id from filter id or code"""
        
        if not hasattr(cls, '_filter_ids'):
            cls._filter_ids = {}

        if filter_id not in cls._filter_ids:
            filters = DBSelect(cls._filter_table).query().fetchall()
            for row in filters:
                cls._filter_ids[row['_id']] = row['_id']
                cls._filter_ids[row['code']] = row['_id']

        return (cls._filter_ids[filter_id]
                    if filter_id in cls._filter_ids else None)

    @classmethod
    def filter_has_option(cls, filter_id, value):
        """Check if a given filter option exists"""

        filter_id = cls.get_filter_id(filter_id)

        if not hasattr(cls, '_filter_options'):
            cls._filter_options = {}

        if (filter_id not in cls._filter_options
                or value not in cls._filter_options[filter_id]):
            options = DBSelect(cls._filter_option_table).query().fetchall()
            for row in options:
                if row['filter'] not in cls._filter_options:
                    cls._filter_options[row['filter']] = []
                cls._filter_options[row['filter']].append(row['value'])

        return (filter_id in cls._filter_options
                and value in cls._filter_options[filter_id])

    @classmethod
    def create_filter(cls, code, label=None):
        """Create a new filter"""

        if not label:
            label = code.capitalize()

        ids = DBHelper().insert(
            cls._filter_table,
            {'code': code, 'label': label}
        )

        return ids[0] if len(ids) > 0 else None

    @classmethod
    def add_filter_option(cls, filter_id, value, label=None):
        """Add an option to the given filter"""

        if cls.filter_has_option(filter_id, value):
            return

        filter_id = cls.get_filter_id(filter_id)
        if not label:
            label = str(value)

        DBHelper().insert(
            cls._filter_option_table,
            {'filter': filter_id, 'value': value, 'label': label}
        )

    @classmethod
    def set_filter_values(cls, file_id, filter_id, values=None):
        """Set the values for the given file and filter"""

        if isinstance(file_id, FileModel):
            file_id = file_id.id()

        filter_id = cls.get_filter_id(filter_id)

        DBSelect(cls._filter_value_table
            ).where('file = ?', file_id
            ).where('filter = ?', filter_id
            ).query_delete()

        if not values:
            return
        elif type(values) not in (list, tuple):
            values = (values,)

        for value in values:
            DBHelper().insert(cls._filter_value_table, {
                'file': file_id,
                'filter': filter_id,
                'value': value
            })

    @classmethod
    def apply_filter(cls, filter_id, values, fileset):
        """Apply a filter to the given file set"""

        filter_id = cls.get_filter_id(filter_id)
        if not filter_id:
            return fileset

        alias = '_flt_%d' % filter_id
        fileset.distinct(True).inner_join(
            (cls._filter_value_table, alias),
            'm.%s = %s.file AND %s.filter = %d' % (
                FileModel._pk, alias, alias, filter_id),
            ()
        ).where('%s.value IN (?)' % alias, values)

        return fileset

    @staticmethod
    def install():
        """Install filter tables"""

        FileModel.install()
        q = DBHelper.quote_identifier
        filter_table = q(FilterHelper._filter_table)
        option_table = q(FilterHelper._filter_option_table)
        value_table = q(FilterHelper._filter_value_table)
        file_table = q(FileModel._table)
        file_table_pk = q(FileModel._pk)

        InstallHelper.install('filter', (
            lambda: (
                DBHelper().query("""
                    CREATE TABLE %s (
                        "_id"   INTEGER PRIMARY KEY AUTOINCREMENT,
                        "code"  TEXT NOT NULL DEFAULT '',
                        "label" TEXT NOT NULL DEFAULT ''
                    )
                """ % filter_table),
                DBHelper().query("""
                    CREATE UNIQUE INDEX "UNQ_FILE_FILTER_CODE"
                        ON %s ("code")
                """ % filter_table),
                DBHelper().query("""
                    CREATE TABLE %s (
                        "filter" INTEGER NOT NULL DEFAULT 0,
                        "value"  INTEGER NOT NULL DEFAULT 0,
                        "label"  TEXT NOT NULL DEFAULT '',
                        FOREIGN KEY ("filter") REFERENCES %s("_id")
                            ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """ % (option_table, filter_table)),
                DBHelper().query("""
                    CREATE UNIQUE INDEX "UNQ_FILE_FILTER_OPTION_FILTER_VALUE"
                        ON %s("filter", "value")
                """ % option_table),
                DBHelper().query("""
                    CREATE TABLE %s (
                        "file"   INTEGER NOT NULL DEFAULT 0,
                        "filter" INTEGER NOT NULL DEFAULT 0,
                        "value"  INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY ("file") REFERENCES %s(%s)
                            ON DELETE CASCADE ON UPDATE CASCADE,
                        FOREIGN KEY ("filter") REFERENCES %s("_id")
                            ON DELETE CASCADE ON UPDATE CASCADE
                    )
                """ % (value_table, file_table, file_table_pk, filter_table)),
                DBHelper().query("""
                    CREATE UNIQUE INDEX "UNQ_FILE_FILTER_VALUE"
                        ON %s("file", "filter", "value")
                """ % value_table),
                DBHelper().query("""
                    CREATE INDEX "IDX_FILE_FILTER_VALUE_FILE" ON %s("file")
                """ % value_table),
                DBHelper().query("""
                    CREATE INDEX "IDX_FILE_FILTER_VALUE_FILTER" ON %s("filter")
                """ % value_table),
                DBHelper().query("""
                    CREATE INDEX "IDX_FILE_FILTER_VALUE_VALUE" ON %s("value")
                """ % value_table)
            ),
        ))

