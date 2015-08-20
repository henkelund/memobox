#!/bin/bash

mv /backupbox /_backupbox
git clone https://pm.nordkvist:cd7f07da2057266e397f0194a9a0c853f6b1cff6@github.com/lostkeys/backupbox /backupbox
chown -h www-data:www-data /backupbox/data
chown -h www-data:www-data /backupbox/system/data
chown -h www-data:www-data /backupbox/system/www/static/.webassets-cache
chown -h www-data:www-data /backupbox/system/www/static/gen
chown -h www-data:www-data /backupbox/system/www/static/devices
chown -h www-data:www-data /backupbox/system/www/static/cache
chown -h www-data:www-data /backupbox/system/www/static/devices
/backupbox/system/bin/pip-install.sh
/backupbox/system/bin/update.sh
