#!/bin/bash

mv /backupbox /_backupbox
git clone https://github.com/lostkeys/backupbox /backupbox
chown -h www-data:www-data /backupbox/data
chown -h www-data:www-data /backupbox/system/data
chmod -h www-data:www-data /backupbox/system/www/static/.webassets-cache
chmod -h www-data:www-data /backupbox/system/www/static/gen
chmod -h www-data:www-data /backupbox/system/www/static/devices
chmod -h www-data:www-data /backupbox/system/www/static/cache
chmod -h www-data:www-data /backupbox/system/www/static/devices
/backupbox/system/bin/pip-install.sh
/backupbox/system/bin/update.sh
