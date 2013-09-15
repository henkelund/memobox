from model.device import DeviceModel
from model.extended import ExtendedModel
from helper.db import DBHelper
import sys, os, subprocess, re, mimetypes, hashlib, math, time

VISIBILITY_VISIBLE = 0
VISIBILITY_HIDDEN = (1 << 0)
VISIBILITY_IN_HIDDEN_DIR = (1 << 1)

class FileModel(ExtendedModel):
    """File Base Model"""

    _table = 'file'
    _pk = '_id'

    def get_attribute_group(self):
        """Get attribute group name"""
        return str(self.type()).capitalize()

    def get_type_specialist(self):
        """Return file type specialist class"""

        type_class_name = '%sType%s' % (
                            self.__class__.__name__,
                            self.get_attribute_group())

        type_class = None
        try:
            type_class = getattr(sys.modules[__name__], type_class_name)
        except AttributeError:
            type_class = FileModelTypeBase

        return type_class(self) if issubclass(
                                        type_class,
                                        FileModelTypeBase) else None

    def save(self):
        """Store this file models data"""

        if not self.id():
            # set timestamp for new files
            self.indexed_at(math.floor(time.time()))

        return super(FileModel, self).save()

    def _load_type_data(self, filename=None):
        """Load file type specific data into this model"""

        specialist = self.get_type_specialist()
        if specialist is not None:
            specialist.harvest(filename)
        return self

    @staticmethod
    def guess_type(filename):
        """Try to determine the type of 'filename'"""

        guess = mimetypes.guess_type(filename, strict=False)
        mime  = [guess[0], guess[1]]

        if mime[0] is None or mime[1] is None:
            try:
                lookup = subprocess.check_output([
                    'file',
                    '--brief',
                    '--mime-type',
                    '--mime-encoding',
                    filename
                ]).split('; ', 1)
                if mime[0] is None:
                    mime[0] = lookup[0]
                if mime[1] is None and len(lookup) > 1:
                    mime[1] = (re.sub(r'^charset=|\n$', '', lookup[1]).strip())
            except subprocess.CalledProcessError:
                pass

        mime[0] = mime[0].strip('; ')
        return mime

    @staticmethod
    def guess_extension(filename, mime=None):
        """Try to determine the extension of 'filename'"""

        extension = None
        basename = os.path.basename(filename)
        segments = basename.split('.')
        if len(segments) > 1:
            extension = segments.pop().lower()
        elif mime is not None:
            extension = mimetypes.guess_extension(
                                str(mime), strict=False).lstrip('.')

        return extension

    @staticmethod
    def calculate_checksum(filename, bufsize=65536):
        """Calculate a sha256 checksum for the given file"""

        hasher = hashlib.sha256()
        fh = open(filename, 'rb')
        buf = fh.read(bufsize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fh.read(bufsize)
        fh.close()

        return hasher.hexdigest()

    @staticmethod
    def guess_visibility(filename):
        """Guess file visibility based on file name and location"""

        visibility = VISIBILITY_VISIBLE

        name = os.path.basename(filename)
        hidden_file_patterns = [
            r'^\.', r'\.tmp$', r'\.bak$', r'\.pyc$', r'\.part$', r'~$',
            r'^Thumbs\.db$', r'^Desktop\.ini$', r'^Icon\?$', r'^ehthumbs\.db$',
            r'^\$RECYCLE\.BIN$', r'^autorun\.inf$'
        ]
        for pattern in hidden_file_patterns:
            if not re.search(pattern, name) is None:
                visibility = VISIBILITY_HIDDEN
                break

        path = os.path.dirname(filename)
        segments = path.split(os.sep)
        hidden_dir_patterns = [
            r'^\.', r'\.tmp$', r'^tmp$', r'\.bak$', r'cache$', r'^__MACOSX$'
        ]
        for name in segments:
            for pattern in hidden_dir_patterns:
                if not re.search(pattern, name) is None:
                    visibility = visibility | VISIBILITY_IN_HIDDEN_DIR
            if visibility & VISIBILITY_IN_HIDDEN_DIR:
                break

        return visibility

    @classmethod
    def factory(self, filename):
        """Harvest data from 'filename' and return a populated FileModel"""

        if not os.path.isfile(filename):
            return None

        # determine file system properties
        name = os.path.basename(filename)
        path = os.path.dirname(os.path.abspath(filename))
        stat = os.stat(filename)
        visibility = FileModel.guess_visibility(filename)

        # determine file content meta information
        file_type = FileModel.guess_type(filename)
        mime = file_type[0]
        extension = FileModel.guess_extension(filename, mime)
        mime_split = mime.split('/')
        checksum = FileModel.calculate_checksum(filename)

        model = FileModel({
            'name': name,
            'abspath': path,
            'extension': extension,
            'type': mime_split[0] if len(mime_split) > 0 else 'unknown',
            'subtype': mime_split[1] if len(mime_split) > 1 else 'unknown',
            'charset': file_type[1] if len(file_type) > 0 else 'unknown',
            'checksum': checksum,
            'size': stat.st_size,
            'created_at': int(stat.st_ctime),
            'is_hidden': 1 if visibility in (
                                VISIBILITY_HIDDEN, VISIBILITY_IN_HIDDEN_DIR
                            ) else 0
        })
        model._load_type_data(filename)

        return model

    @classmethod
    def _install(cls):
        """Install base table and attributes"""

        ExtendedModel.install()
        table = DBHelper.quote_identifier(cls._table)
        pk = DBHelper.quote_identifier(cls._pk)

        return (
            lambda: (
                DBHelper().query("""
                    CREATE TABLE %s (
                        %s           INTEGER PRIMARY KEY AUTOINCREMENT,
                        "name"       TEXT    NOT NULL DEFAULT '',
                        "abspath"    TEXT    NOT NULL DEFAULT '',
                        "extension"  TEXT,
                        "type"       TEXT    NOT NULL DEFAULT '',
                        "subtype"    TEXT    NOT NULL DEFAULT '',
                        "charset"    TEXT,
                        "checksum"   TEXT    NOT NULL DEFAULT '',
                        "size"       INTEGER,
                        "created_at" INTEGER,
                        "indexed_at" INTEGER,
                        "is_hidden"  INTEGER NOT NULL DEFAULT 0,
                        "rating"     INTEGER NOT NULL DEFAULT 0
                    )
                """ % (table, pk)),
                FileModel._create_attribute_tables()
            ),
        )

class FileModelTypeBase(object):
    """Base class for file types"""

    def __init__(self, file_model):
        """Initialize type instance"""
        self._file_model = file_model

    def get_file(self):
        """Return file model instance"""
        return self._file_model

    def harvest(self, filename=None):
        """Populate file model with type specific data"""

        model = self.get_file()
        if model is None:
            return self

        if filename is None or not os.path.isfile(filename):
            dirname = model.abspath()
            basename = model.name()
            if dirname is None or basename is None:
                return self
            filename = os.path.join(dirname, basename)
            if not os.path.isfile(filename):
                return self

        return self._harvest(filename)

    def _harvest(self, filename):
        """Implement in subclass"""
        return self

