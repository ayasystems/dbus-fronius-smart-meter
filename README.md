# dbus-fronius-smart-meter
Integrate Fronis Meter smart meter into [Victron Energies Venus OS](https://github.com/victronenergy/venus)

![image](https://user-images.githubusercontent.com/7864168/179211755-434ad49f-0f82-4b31-8ab3-e293f7d33c3c.png)

![image](https://user-images.githubusercontent.com/7864168/179207965-218cf519-f7f6-41af-8c24-e4446c434010.png)


## Purpose
With the scripts in this repo it should be easy possible to install, uninstall, restart a service that connects the Fronis Meter to the VenusOS and GX devices from Victron.
Idea is pasend on @RalfZim project linked below.



## Inspiration
This project is my first on GitHub and with the Victron Venus OS, so I took some ideas and approaches from the following projects - many thanks for sharing the knowledge:
- https://github.com/fabian-lauer/dbus-shelly-3em-smartmeter (thanks a lot)
- https://github.com/RalfZim/venus.dbus-fronius-smartmeter
- https://github.com/victronenergy/dbus-smappee
- https://github.com/Louisvdw/dbus-serialbattery
- https://community.victronenergy.com/questions/85564/eastron-sdm630-modbus-energy-meter-community-editi.html



## How it works
### My setup
- Fronius Primo 5 with Smart Meter TS 100A-1
  - 1-Phase installation (normal for Spain)
  - Wired connected
  
- Raspberry Pi 4 with Venus OS - Firmware v2.90-17
  - No other devices from Victron connected  
  - Wired connected
 

### Details / Process
As mentioned above the script is inspired by @RalfZim fronius smartmeter implementation.
So what is the script doing:
- Running as a service
- connecting to DBus of the Venus OS `com.victronenergy.grid.http_40`
- After successful DBus connection Fronis Meter is accessed via REST-API 
  A sample JSON file from Fronis Meter can be found [here](docs/GetMeterRealtimeData.json)
- Serial is taken from the response as device serial
- Paths are added to the DBus with default value 0 - including some settings like name, etc
- After that a "loop" is started which pulls Fronis Meter data every 750ms from the REST-API and updates the values in the DBus

Thats it 😄






## Install & Configuration
### Get the code
Just grap a copy of the main branche and copy them to `/data/dbus-fronius-smart-meter`.
After that call the install.sh script.

The following script should do everything for you:
```
wget https://github.com/ayasystems/dbus-fronius-smart-meter/archive/refs/heads/main.zip
unzip main.zip "dbus-fronius-smart-meter-main/*" -d /data
mv /data/dbus-fronius-smart-meter-main /data/dbus-fronius-smart-meter
chmod a+x /data/dbus-fronius-smart-meter/install.sh
/data/dbus-fronius-smart-meter/install.sh
rm main.zip
```
⚠️ Check configuration after that - because service is already installed an running and with wrong connection data (host, username, pwd) you will spam the log-file
### Stop service
```
svc -d /service/dbus-fronius-smart-meter
```
### Start service
```
svc -u /service/dbus-fronius-smart-meter
```
### Reload data
```
/data/dbus-fronius-smart-meter/restart.sh
```
### View log file
```
cat /data/dbus-fronius-smart-meter/current.log
```
### Change config.ini
Within the project there is a file `/data/dbus-fronius-smart-meter/config.ini` - just change the values - most important is the host, username and password in section "ONPREMISE". More details below:

Afther change the config file execute restart.sh to reload new settings [how to](https://github.com/ayasystems/dbus-fronius-smart-meter/blob/main/README.md#reload-data)

| Section  | Config vlaue | Explanation |
| ------------- | ------------- | ------------- |
| DEFAULT  | AccessType | Fixed value 'OnPremise' |
| DEFAULT  | SignOfLifeLog  | Time in minutes how often a status is added to the log-file `current.log` with log-level INFO |
| ONPREMISE  | Host | IP or hostname of on-premise Fronis Meter web-interface |
| ONPREMISE  | MeterID  | Your meter ID
| ONPREMISE  | intervalMs  | Interval time in ms to get data from Fronius

![image](https://user-images.githubusercontent.com/7864168/179208083-80d7b07e-3985-4922-b5b8-bd56d65ba31c.png)


## Used documentation
- https://github.com/victronenergy/venus/wiki/dbus#grid   DBus paths for Victron namespace
- https://github.com/victronenergy/venus/wiki/dbus-api   DBus API from Victron
- https://www.victronenergy.com/live/ccgx:root_access   How to get root access on GX device/Venus OS

 
