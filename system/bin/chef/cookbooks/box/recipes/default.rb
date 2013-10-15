#############################
# Install required packages #
#############################

# Used in automount script for block devices
package 'pmount' do
  package_name node[:pmount][:package]
  action :install
end

# Used in automount script for i-things
package 'ifuse' do
  package_name node[:ifuse][:package]
  action :install
end

# Used in automount script for i-things
package 'idevicepair' do
  package_name node[:idevicepair][:package]
  action :install
end

# Used in automount for cameras and some Androids
package 'gphotofs' do
  package_name node[:gphotofs][:package]
  action :install
end

# Used in dispatcher.sh
package 'parted' do
  package_name node[:parted][:package]
  action :install
end

# Language for indexer and web app
package 'python' do
  package_name node[:python][:package]
  action :install
end

# Python utilities. Caching etc..
package 'werkzeug' do
  package_name node[:werkzeug][:package]
  action :install
end

# Used for reading EXIF data and scaling images
package 'pil' do
  package_name node[:pil][:package]
  action :install
end

# Tiny python web application framework
package 'flask' do
  package_name node[:flask][:package]
  action :install
end

# Install python web application container
package 'uwsgi' do
  package_name node[:uwsgi][:package]
  action :install
end
package 'uwsgi_python' do
  package_name node[:uwsgi_python][:package]
  action :install
end

# Frontend proxy for uwsgi
package 'nginx' do
  package_name node[:nginx][:package]
  action :install
end

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

if ENV::has_key?('BOX_DIR') and File::directory?(ENV['BOX_DIR'])

  ##############################
  # Set up directory structure #
  ##############################

  # Create non-versioned directories
  dirs = %w{ log data data/cache }
  dirs.each do |dir|
    directory "#{ENV['BOX_DIR']}/#{dir}" do
      owner 'root'
      group 'root'
      mode '0755'
      recursive true
      action :create
    end
  end

  # Publish image cache files
  link "#{ENV['BOX_DIR']}/www/static/images/thumbnails" do
    to "#{ENV['BOX_DIR']}/data/cache/thumbnails"
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

end

