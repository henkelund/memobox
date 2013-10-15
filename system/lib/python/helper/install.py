from helper.db import DBHelper, DBSelect
from inspect import isroutine

class InstallHelper(object):
    """Helper class for module version management"""

    _table = 'version'
    _state = None

    @classmethod
    def _initialize(cls, force=False):
        """Load version info from db"""

        if cls._state and not force:
            return

        if not DBHelper().describe_table(cls._table):
            DBHelper().query("""
                CREATE TABLE %s (
                    "module" TEXT PRIMARY KEY,
                    "version" INTEGER NOT NULL DEFAULT 0
                )
            """ % DBHelper.quote_identifier(cls._table))

        cls._state = {}
        for module in DBSelect(cls._table).query().fetchall():
            cls._state[module['module']] = module['version']

    @classmethod
    def reset(cls):
        """Reset all versions"""

        cls._state = None
        DBHelper().query('DROP TABLE IF EXISTS %s'
            % DBHelper.quote_identifier(cls._table))

    @classmethod
    def version(cls, module):
        """Check current version of module"""

        cls._initialize()
        return cls._state[module] if module in cls._state else 0

    @classmethod
    def _update_version(cls, module, version):
        """Update module version number"""

        cls._initialize()
        if module in cls._state:
            DBSelect(cls._table
                ).where('module = ?', module
                ).query_update({'version': version})
        else:
            DBHelper().insert(cls._table, {
                'module': module,
                'version': version
            })
        cls._initialize(True)

    @classmethod
    def install(cls, module, routines):
        """Run module install/upgrade routines"""

        if not routines:
            return

        version = cls.version(module)
        if version >= len(routines):
            return

        while version < len(routines):
            if isroutine(routines[version]):
                routines[version]()
            else:
                DBHelper().query(routines[version])
            version = version + 1

        cls._update_version(module, version)

