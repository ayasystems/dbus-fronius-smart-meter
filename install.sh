#!/bin/bash

# set permissions for script files
chmod a+x /data/dbus-fronius-smart-meter/restart.sh
chmod 744 /data/dbus-fronius-smart-meter/restart.sh

chmod a+x /data/dbus-fronius-smart-meter/uninstall.sh
chmod 744 /data/dbus-fronius-smart-meter/uninstall.sh

chmod a+x /data/dbus-fronius-smart-meter/service/run
chmod 755 /data/dbus-fronius-smart-meter/service/run



# create sym-link to run script in deamon
ln -s /data/dbus-fronius-smart-meter/service /service/dbus-fronius-smart-meter



# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]
then
    touch $filename
    chmod 755 $filename
    echo "#!/bin/bash" >> $filename
    echo >> $filename
fi

grep -qxF '/data/dbus-fronius-smart-meter/install.sh' $filename || echo '/data/dbus-fronius-smart-meter/install.sh' >> $filename
