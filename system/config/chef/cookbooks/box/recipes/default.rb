##########################################
# Check required configuration variables #
##########################################

required_system_dirs = %w{ root bin lib www }
required_system_dirs.each do |dir|
  if not File::directory?(node[:dirs][:system][dir.to_sym] || '')
    Chef::Application.fatal!("No \"#{dir}\" dir provided", 1)
  end
end

required_data_dirs = %w{ data device cache log }
required_data_dirs.each do |dir|
  if not node[:dirs][:data][dir.to_sym]
    Chef::Application.fatal!("No \"#{dir}\" dir provided", 1)
  end
end

#############################
# Install required packages #
#############################

# pmount - Used in automount script for block devices
# ifuse - Used in automount script for i-things
# libimobiledevice-utils - Used in automount script for i-things
# gphotofs - Used in automount for cameras and some Androids
# parted - Used in dispatcher.sh
# python - Language for indexer and web app
# python-werkzeug - Python utilities. Caching etc..
# python-imaging - Used for reading EXIF data and scaling images
# python-flask - Tiny python web application framework
# uwsgi - Install python web application container
# uwsgi-plugin-python
# nginx - Frontend proxy for uwsgi
# curl - Used by upgrade / ping scripts etc.
# mediainfo - Used to extract meta data from videos
# libav-tools - avconv is used to generate thumbnails from videos
# graphicsmagick - Extremely fast thumbnail generation tool
packages = %w{
  libfuse-dev libusb-1.0-0-dev python-dev pkg-config libxml2-dev pmount libtool automake autoconf autotools-dev tree gphotofs parted python python-werkzeug
  python-imaging python-flask uwsgi uwsgi-plugin-python nginx curl mediainfo libav-tools graphicsmagick python-pip python-dev libgraphicsmagick++1-dev libboost-python-dev sshpass
}
packages.each do |package_name|
  package package_name do
    package_name package_name
    action :upgrade
  end
end

####################################
# Install required Python Packages #
####################################
# python_pip "paramiko"
#
#packages = %w{
#  webassets, requests, pycrypto, pyOpenSSL, pwinty, paramiko, pgmagick
#}
# Master Zkilleman needs to help out here...

###################
# Define services #
###################

services = %w{ udev cron uwsgi nginx }
services.each do |service|
  service service do
    service_name service
    restart_command "service #{service} restart && sleep 1"
    reload_command "service #{service} reload && sleep 1"
    action :enable
  end
end

##############################
# Set up directory structure #
##############################

# Create non-versioned directories
node[:dirs][:data].each do |role,dirname|
  directory "#{dirname}" do
    owner 'root'
    group 'root'
    mode '0755'
    recursive true
    action :create
  end
end

# Publish image cache files
link "#{node[:dirs][:system][:www]}/static/images/thumbnails" do
  to "#{node[:dirs][:data][:cache]}/thumbnails"
end

######################
# Install udev rules #
######################

# Copy rule template and restart udev service
template '/etc/udev/rules.d/99-automount.rules' do
  source '99-automount.rules.erb'
  owner 'root'
  group 'root'
  mode 0644
  notifies :reload, resources(:service => 'udev'), :immediate
end

#####################
# Confifure indexer #
#####################

# Copy cron template and restart cron service
template '/etc/cron.d/box-cron' do
  source 'box-cron.erb'
  owner 'root'
  group 'root'
  mode 0644
  notifies :reload, resources(:service => 'cron'), :immediate
end

###################################
# Configure web application stack #
###################################

template '/etc/uwsgi/apps-available/box.ini' do
  source 'uwsgi.ini.erb'
  owner 'root'
  group 'root'
  mode 0644
  notifies :restart, resources(:service => 'uwsgi'), :immediate
end

template '/etc/nginx/sites-available/box-uwsgi' do
  source 'box-nginx.erb'
  owner 'root'
  group 'root'
  mode 0644
  notifies :restart, resources(:service => 'nginx'), :immediate
end

# Enable the uwsgi configuration and disable the default site
link '/etc/uwsgi/apps-enabled/box.ini' do
  to '/etc/uwsgi/apps-available/box.ini'
  notifies :restart, resources(:service => 'uwsgi'), :immediate
end
link '/etc/nginx/sites-enabled/box-uwsgi' do
  to '/etc/nginx/sites-available/box-uwsgi'
  notifies :restart, resources(:service => 'nginx'), :immediate
end
link '/etc/nginx/sites-enabled/default' do
  action :delete
  only_if 'test -L /etc/nginx/sites-enabled/default'
end

