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

if ENV::has_key?('BOX_DIR') and File::directory?(ENV['BOX_DIR'])

  ##############################
  # Set up directory structure #
  ##############################

  # Create non-versioned directories
  dirs = %W{ #{ENV['BOX_DIR']}/log #{ENV['BOX_DIR']}/data }
  dirs.each do |dir|
    directory dir do
      owner 'root'
      group 'root'
      mode '0755'
      recursive true
      action :create
    end
  end

  ######################
  # Install udev rules #
  ######################

  # Define udev service
  service 'udev' do
    service_name 'udev'
    restart_command 'service udev restart && sleep 1'
    reload_command 'service udev reload && sleep 1'
    action :enable
  end

  # Copy rule template and restart udev service
  template '/etc/udev/rules.d/99-automount.rules' do
    source '99-automount.rules.erb'
    owner 'root'
    group 'root'
    mode 0644
    notifies :reload, resources(:service => 'udev'), :immediately
  end

  #####################
  # Confifure indexer #
  #####################

  # Define cron service
  service 'cron' do
    service_name 'cron'
    restart_command 'service cron restart && sleep 1'
    reload_command 'service cron reload && sleep 1'
    action :enable
  end

  # Copy cron template and restart cron service
  template '/etc/cron.d/box-cron' do
    source 'box-cron.erb'
    owner 'root'
    group 'root'
    mode 0644
    notifies :reload, resources(:service => 'cron'), :immediately
  end

end

