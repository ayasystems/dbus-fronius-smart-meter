#!/bin/bash


kill $(pgrep -f 'supervise dbus-fronius-smart-meter')
chmod a-x /data/dbus-fronius-smart-meter/service/run
svc -d /service/dbus-fronius-smart-meter
./restart.sh
