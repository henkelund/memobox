#!/bin/bash

mv /backupbox /_backupbox
git clone https://github.com/lostkeys/backupbox /backupbox
chown -h www-data:www-data /backupbox/data
chown -h www-data:www-data /backupbox/system/data
chown -h www-data:www-data /backupbox/system/www/static/.webassets-cache
chown -h www-data:www-data /backupbox/system/www/static/gen
chown -h www-data:www-data /backupbox/system/www/static/devices
chown -h www-data:www-data /backupbox/system/www/static/cache
chown -h www-data:www-data /backupbox/system/www/static/devices
/backupbox/system/bin/pip-install.sh
/backupbox/system/bin/update.sh
