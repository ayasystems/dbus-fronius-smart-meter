#!/bin/bash
svc -u /service/dbus-fronius-smart-meter
kill $(pgrep -f 'python /data/dbus-fronius-smart-meter/dbus-fronius-smart-meter.py')
