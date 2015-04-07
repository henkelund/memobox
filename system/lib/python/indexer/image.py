# -*- coding: utf-8 -*-
import sys, os
import subprocess
from PIL import Image
from helper.db import DBHelper, DBSelect
from helper.image import ImageHelper
from model.file import FileModel
from helper.log import LogHelper as logger
from model.device import DeviceModel

# Get Duration
# avconv -i IMG_0106.mov 2>&1 | grep Duration | awk '{print $2}' | tr -d ,

# Get screen size
# avconv -i IMG_0106.mp4 2>&1 | grep Stream | awk '{print $7}' | tr -d , | head -1

# Get orientation
# mediainfo IMG_2464.MOV  | grep Rotation  | awk '{print $3}'

# Get creation date
# avconv -i IMG_0106.mp4 2>&1 | grep creation_time | awk '{print $3}' | tr -d , | head -1 

# Get Creation time
# avconv -i IMG_0106.mp4 2>&1 | grep creation_time | awk '{print $4}' | tr -d , | head -1 

# avconv -i IMG_2464.MOV -codec:v libx264 -profile:v high -preset slow -b:v 500k -maxrate 500k -bufsize 1000k -vf scale=-1:480 -threads 0 -codec:a aac -b:a 128k output_file.mp4

class ImageIndexer(object):
    """Class responsible for generating thumbnails"""

    @classmethod
    def index_file_thumbnails(cls, device, database, basedir, width, height):
        """Generate thumbnails for image files"""

        ImageHelper.install()
        insert = {}
        _models = []
        busy = False

        models = FileModel.all().add_filter('extension', {'in': (
            'bmp', 'gif', 'im', 'jpg', 'jpe', 'jpeg', 'msp',
            'pcx', 'png', 'ppm', 'tiff', 'xpm', 'mov', 'mp4', 'wmv'
        )})

        ImageHelper.join_file_thumbnails(
            models, 'm.%s' % FileModel._pk, width, height, ())
        models.where("m.device = " + str(device.id())).where('tt.thumbnail IS NULL').limit(70).order('created_at', 'DESC')

        for model in models:
            _models.append(model)

        for model in _models:
            if not busy:
                busy = True
                device.set_state(DeviceModel.THUMBNAIL_INDEX_STARTED)

            filename = os.path.join(model.abspath(), model.name())
            extension = os.path.splitext(filename)[1][1:]

            thumbname = os.path.join(
				'thumbnails',
				'%sx%s' % (width if width else '', height if height else ''),
				model.name()[0] if len(model.name()) > 0 else '_',
				model.name()[1] if len(model.name()) > 1 else '_',
				model.name()
            )
            
            thumbname = thumbname.replace(" ", "_").replace("(", "_").replace(")", "_")+"_"+str(model.id())+".jpg"
            thumbfile = os.path.join(basedir, thumbname);

            if (extension.lower() in ["mov", "mp4", "wmv"]) and (height > 0) :
            	print "Thumbfile/Video: "+thumbfile
            	directory = os.path.dirname(thumbfile)
            	if not os.path.isdir(directory):
        			os.makedirs(directory)
            	
            	# Command for converting video to thumbnail Todo: adjust for format
            	cmdline = [
            	'avconv',
            	'-itsoffset',
            	'-4',
            	'-i',
            	filename,
            	'-vcodec',
            	'mjpeg',
            	'-vframes',
            	'1',
            	'-an',
            	'-f',
            	'rawvideo',
            	'-y',
            	thumbfile+"_",
            	]   		
        		
        		# Command for detectin video orientation. Using mediainfo | grep | awk
            	mediainfo = subprocess.Popen(['mediainfo', filename],stdout=subprocess.PIPE)
            	grep = subprocess.Popen(['grep', 'Rotation'],stdin = mediainfo.stdout, stdout=subprocess.PIPE)
            	awk = subprocess.Popen(['awk', '{print $3}'],stdin = grep.stdout, stdout=subprocess.PIPE)
            	line = awk.stdout.readline()
            	
            	# If Orientation is 90 degress. Rotate the movie
            	if(line.startswith("90")):
					cmdline.insert(7, "transpose=1")
					cmdline.insert(7, "-vf")

            	subprocess.call(cmdline)
            	
            	cmdline = [
            	'gm',
            	'convert',
            	'-size',
            	str(width)+"x"+str(height),
            	thumbfile+"_",
            	'-thumbnail',
            	str(width)+"x"+str(height)+"^",
            	'-gravity',
            	'center',
            	'-extent',
            	str(width)+"x"+str(height),
            	'+profile',
            	'"*"',
            	'-auto-orient',
            	thumbfile
            	]                 	
            	
            	subprocess.call(cmdline)
            	
            	insert[model.id()] = thumbname
            else:
            	print "Thumbfile/Image: "+thumbfile
            	directory = os.path.dirname(thumbfile)
            	if not os.path.isdir(directory):
            		os.makedirs(directory)
        		
            	if (height > 0) :
		            cmdline = [
		            'gm',
		            'convert',
		            '-size',
		            str(width)+"x"+str(height),
		            filename,
		            '-thumbnail',
		            str(width)+"x"+str(height)+"^",
		            '-gravity',
		            'center',
		            '-extent',
		            str(width)+"x"+str(height),
		            '+profile',
		            '"*"',
		            '-auto-orient',
		            thumbfile
		            ]
            	else:
		            cmdline = [
		            'gm',
		            'convert',
		            '-size',
		            str(width)+"x"+str(width)+"^",
		            filename,
		            '-thumbnail',
		            str(width)+"x"+str(width)+"^",
		            '+profile',
		            '"*"',
		            '-auto-orient',
		            thumbfile
					]

            	subprocess.call(cmdline)
            	insert[model.id()] = thumbname

        if len(insert) > 0:
            print "Add generated thumbnails to database"            
            for file_id in insert.keys():
                ImageHelper.add_file_thumbnail(
                    file_id, width, height, insert[file_id])
            
        elif width == 520:
            DBHelper().close_connection()
            device.set_state(DeviceModel.READY);
                
        print "Image " + str(width) + " index done"

if (__name__ == '__main__'):
    """$ python image.py path/to/database path/to/basedir"""

    if len(sys.argv) < 3:
        exit(1)

    database = sys.argv[1]
    basedir = sys.argv[2]
    _devices = []

    if not os.path.isdir(basedir):
        exit(2)

    basedir = os.path.join(basedir, 'cache')
    DBHelper(database)
    devices = DeviceModel.all()

    for device in devices: 
        _devices.append(device)

    for device in _devices:
        if device.serial() is not None:
            ImageIndexer.index_file_thumbnails(device, database, basedir, 260, 260) #TODO: read from configuration
            ImageIndexer.index_file_thumbnails(device, database, basedir, 520, -1) # retina