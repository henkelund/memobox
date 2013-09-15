from model.device import DeviceModel
from model.extended import ExtendedModel
from helper.db import DBHelper
import sys, os, subprocess, re, mimetypes, hashlib, math, time
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

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
                cls._create_attribute_tables(),
                cls._create_attribute(
                    'width', 'Width', 'integer', 'Image'),
                cls._create_attribute(
                    'height', 'Height', 'integer', 'Image'),
                cls._create_attribute(
                    'latitude', 'Latitude', 'real', 'Image'),
                cls._create_attribute(
                    'longitude', 'Longitude', 'real', 'Image'),
                cls._create_attribute(
                    'timestamp', 'Timestamp', 'integer', 'Image'),
                cls._create_attribute(
                    'orientation', 'Orientation', 'integer', 'Image')
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

class FileModelTypeImage(FileModelTypeBase):
    """Image file type specialist

    EXIF to LatLng conversion courtesy of erans
    https://gist.github.com/erans/983821
    """

    def _get_exif_data(self, image):
        """Get exif data from 'filename'"""

        data = {}
        exif = image._getexif()
        if not exif:
            return data

        for tag, value in exif.items():
            decoded = TAGS.get(tag, tag)
            if decoded == 'GPSInfo':
                gps_info = {}
                for t in value:
                    gps_decoded = GPSTAGS.get(t, t)
                    gps_info[gps_decoded] = value[t]

                data[decoded] = gps_info
            else:
                data[decoded] = value

        return data

    def _latlng_to_degree(self, value):
        """Convert EXIF coordinate value to float degree"""

        d0 = value[0][0]
        d1 = value[0][1]
        d = float(d0) / float(d1)

        m0 = value[1][0]
        m1 = value[1][1]
        m = float(m0) / float(m1)

        s0 = value[2][0]
        s1 = value[2][1]
        s = float(s0) / float(s1)

        return d + (m / 60.) + (s / 3600.)

    def _gpsinfo_to_latlng(self, info):
        """Convert EXIF GPSInfo to latlng degree values"""

        lat_val = None
        lng_val = None

        latref = info['GPSLatitudeRef'] if 'GPSLatitudeRef' in info else None
        lngref = info['GPSLongitudeRef'] if 'GPSLongitudeRef' in info else None
        lat = info['GPSLatitude'] if 'GPSLatitude' in info else None
        lng = info['GPSLongitude'] if 'GPSLongitude' in info else None

        if not latref or not lngref or not lat or not lng:
            return (lat_val, lng_val)

        lat_val = self._latlng_to_degree(lat)
        if latref != 'N':
            lat_val = -lat_val

        lng_val = self._latlng_to_degree(lng)
        if lngref != 'E':
            lng_val = -lng_val

        return (lat_val, lng_val)

    def _clean_exif_string(self, string):
        """Clean strings from trailing null char"""
        return re.sub(r'\0.*$', r'', string)

    def _harvest(self, filename):
        """Gather image specific data from 'filename'"""

        model = self.get_file()
        image = Image.open(filename)
        if not image:
            return self

        size = image.size
        if size and len(size) >= 2:
            model.width(size[0])
            model.height(size[1])

        exif = self._get_exif_data(image)

        if 'GPSInfo' in exif:
            latlng = self._gpsinfo_to_latlng(exif['GPSInfo'])
            if latlng[0] and latlng[1]:
                model.latitude(latlng[0])
                model.longitude(latlng[1])

        if 'DateTime' in exif:
            date_str = self._clean_exif_string(exif['DateTime'])
            try:
                time_struct = time.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                timestamp = int(time.mktime(time_struct))
                if timestamp > 0:
                    model.timestamp(timestamp)
            except ValueError:
                pass

        if 'Orientation' in exif:
            model.orientation(exif['Orientation'])

        return self

