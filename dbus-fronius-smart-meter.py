#!/usr/bin/env python
 
# import normal packages
import platform 
import logging
import sys
import os
import sys
if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject
import sys
import time
import requests # for http GET
import configparser # for config/ini file
 
# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService


class DbusFroniusMeterService:
  def __init__(self, servicename, deviceinstance, paths, productname='Fronius Smart Meter VIR', connection='Fronius meter JSON API'):
    config = configparser.ConfigParser()
    config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))
    self._dbusservice = VeDbusService("{}.http_{:02d}".format(servicename, deviceinstance))
    self._paths = paths
 
    logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))
 
    # Create the management objects, as specified in the ccgx dbus-api document
    self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
    self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
    self._dbusservice.add_path('/Mgmt/Connection', connection)
 
    # Create the mandatory objects
    self._dbusservice.add_path('/DeviceInstance', deviceinstance)
    self._dbusservice.add_path('/ProductId', 16) # value used in ac_sensor_bridge.cpp of dbus-cgwacs
    #self._dbusservice.add_path('/ProductId', 0xFFFF) # id assigned by Victron Support from SDM630v2.py
    #self._dbusservice.add_path('/ProductId', 45069) # found on https://www.sascha-curth.de/projekte/005_Color_Control_GX.html#experiment - should be an ET340 Engerie Meter
    #self._dbusservice.add_path('/DeviceType', 345) # found on https://www.sascha-curth.de/projekte/005_Color_Control_GX.html#experiment - should be an ET340 Engerie Meter
    self._dbusservice.add_path('/ProductName', productname)
    self._dbusservice.add_path('/CustomName', config['ONPREMISE']['CustomName'])    
    self._dbusservice.add_path('/Latency', None)    
    self._dbusservice.add_path('/FirmwareVersion', 0.1)
    self._dbusservice.add_path('/HardwareVersion', 0)
    self._dbusservice.add_path('/Connected', 1)
    self._dbusservice.add_path('/Role', config['ONPREMISE']['Role'])
    self._dbusservice.add_path('/Position', 1) # normaly only needed for pvinverter
    self._dbusservice.add_path('/Serial', self._getFronisSerial())
    self._dbusservice.add_path('/UpdateIndex', 0)
 
    # add path values to dbus
    for path, settings in self._paths.items():
      self._dbusservice.add_path(
        path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)
 
    # last update
    self._lastUpdate = 0
 
    # add _update function 'timer'
    gobject.timeout_add(int(config['ONPREMISE']['intervalMs']), self._update) # pause 250ms before the next request
    
    # add _signOfLife 'timer' to get feedback in log every 5minutes
    gobject.timeout_add(self._getSignOfLifeInterval()*60*1000, self._signOfLife)
  def _getFronisSerial(self):
    meter_data = self._getFroniusData()  
    
    if not meter_data['Body']['Data']['Details']['Serial']:
        raise ValueError("Response does not contain 'mac' attribute")
    
    serial = meter_data['Body']['Data']['Details']['Serial']
    return serial
  def _getConfig(self):
    config = configparser.ConfigParser()
    config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))
    return config;
  def _getSignOfLifeInterval(self):
    config = self._getConfig()
    value = config['DEFAULT']['SignOfLifeLog']
    
    if not value: 
        value = 0
    
    return int(value)
  
  
  def _getFroniusDataUrl(self):
    config = self._getConfig()
    accessType = config['DEFAULT']['AccessType']
    
    if accessType == 'OnPremise': 
        #URL = "http://%s:%s@%s/status" % (config['ONPREMISE']['Username'], config['ONPREMISE']['Password'], config['ONPREMISE']['Host'])
        URL = "http://%s/solar_api/v1/GetMeterRealtimeData.cgi?Scope=Device&DeviceId=%s&DataCollection=MeterRealtimeData" % (config['ONPREMISE']['Host'], config['ONPREMISE']['MeterID'])
        #URL = URL.replace(":@", "")
    else:
        raise ValueError("AccessType %s is not supported" % (config['DEFAULT']['AccessType']))
    
    return URL
    
 
  def _getFroniusData(self):
    URL = self._getFroniusDataUrl()
    meter_r = requests.get(url = URL)
    
    # check for response
    if not meter_r:
        raise ConnectionError("No response from Fronius - %s" % (URL))
    
    meter_data = meter_r.json()     
    
    # check for Json
    if not meter_data:
        raise ValueError("Converting response to JSON failed")
    
    
    return meter_data
 
 
  def _signOfLife(self):
    logging.info("--- Start: sign of life ---")
    logging.info("Last _update() call: %s" % (self._lastUpdate))
    logging.info("Last '/Ac/Power': %s" % (self._dbusservice['/Ac/Power']))
    logging.info("--- End: sign of life ---")
    return True
 
  def _update(self):   
    try:
       #get data from Fronius
       meter_data = self._getFroniusData()
       """       
       #send data to DBus
       self._dbusservice['/Ac/Power'] = meter_data['total_power'] # positive: consumption, negative: feed into grid
       self._dbusservice['/Ac/L1/Voltage'] = meter_data['emeters'][0]['voltage']
       self._dbusservice['/Ac/L2/Voltage'] = meter_data['emeters'][1]['voltage']
       self._dbusservice['/Ac/L3/Voltage'] = meter_data['emeters'][2]['voltage']
       self._dbusservice['/Ac/L1/Current'] = meter_data['emeters'][0]['current']
       self._dbusservice['/Ac/L2/Current'] = meter_data['emeters'][1]['current']
       self._dbusservice['/Ac/L3/Current'] = meter_data['emeters'][2]['current']
       self._dbusservice['/Ac/L1/Power'] = meter_data['emeters'][0]['power']
       self._dbusservice['/Ac/L2/Power'] = meter_data['emeters'][1]['power']
       self._dbusservice['/Ac/L3/Power'] = meter_data['emeters'][2]['power']
       self._dbusservice['/Ac/L1/Energy/Forward'] = (meter_data['emeters'][0]['total']/1000)
       self._dbusservice['/Ac/L2/Energy/Forward'] = (meter_data['emeters'][1]['total']/1000)
       self._dbusservice['/Ac/L3/Energy/Forward'] = (meter_data['emeters'][2]['total']/1000)
       self._dbusservice['/Ac/L1/Energy/Reverse'] = (meter_data['emeters'][0]['total_returned']/1000) 
       self._dbusservice['/Ac/L2/Energy/Reverse'] = (meter_data['emeters'][1]['total_returned']/1000) 
       self._dbusservice['/Ac/L3/Energy/Reverse'] = (meter_data['emeters'][2]['total_returned']/1000) 
       self._dbusservice['/Ac/Energy/Forward'] = self._dbusservice['/Ac/L1/Energy/Forward'] + self._dbusservice['/Ac/L2/Energy/Forward'] + self._dbusservice['/Ac/L3/Energy/Forward']
       self._dbusservice['/Ac/Energy/Reverse'] = self._dbusservice['/Ac/L1/Energy/Reverse'] + self._dbusservice['/Ac/L2/Energy/Reverse'] + self._dbusservice['/Ac/L3/Energy/Reverse'] 
       """       
       meter_consumption = meter_data['Body']['Data']['PowerReal_P_Sum']
       meter_voltage = meter_data['Body']['Data']['Voltage_AC_Phase_1']
       meter_model = meter_data['Body']['Data']['Details']['Model']
       if meter_model == 'Smart Meter TS 100A-1' or meter_model == 'Smart Meter 63A-1'  :  # set values for single phase meter
        meter_data['Body']['Data']['Voltage_AC_Phase_2'] = 0
        meter_data['Body']['Data']['Voltage_AC_Phase_3'] = 0
        meter_data['Body']['Data']['Current_AC_Phase_2'] = 0
        meter_data['Body']['Data']['Current_AC_Phase_3'] = 0
        meter_data['Body']['Data']['PowerReal_P_Phase_2'] = 0
        meter_data['Body']['Data']['PowerReal_P_Phase_3'] = 0
       self._dbusservice['/Ac/Power'] = meter_consumption  # positive: consumption, negative: feed into grid 
       self._dbusservice['/Ac/Voltage'] = meter_voltage
       self._dbusservice['/Ac/Current'] = meter_data['Body']['Data']['Current_AC_Phase_1']
       self._dbusservice['/Ac/L1/Voltage'] = meter_voltage
       self._dbusservice['/Ac/L2/Voltage'] = meter_data['Body']['Data']['Voltage_AC_Phase_2']
       self._dbusservice['/Ac/L3/Voltage'] = meter_data['Body']['Data']['Voltage_AC_Phase_3']
       self._dbusservice['/Ac/L1/Current'] = meter_data['Body']['Data']['Current_AC_Phase_1']
       self._dbusservice['/Ac/L2/Current'] = meter_data['Body']['Data']['Current_AC_Phase_2']
       self._dbusservice['/Ac/L3/Current'] = meter_data['Body']['Data']['Current_AC_Phase_3']
       self._dbusservice['/Ac/L1/Power'] = meter_data['Body']['Data']['PowerReal_P_Phase_1']
       self._dbusservice['/Ac/L2/Power'] = meter_data['Body']['Data']['PowerReal_P_Phase_2']
       self._dbusservice['/Ac/L3/Power'] = meter_data['Body']['Data']['PowerReal_P_Phase_3']
       self._dbusservice['/Ac/L1/Energy/Forward'] = float(meter_data['Body']['Data']['EnergyReal_WAC_Sum_Consumed'])/1000 
       self._dbusservice['/Ac/L1/Energy/Reverse'] = float(meter_data['Body']['Data']['EnergyReal_WAC_Sum_Produced'])/1000  
       self._dbusservice['/Ac/L2/Energy/Forward'] = 0
       self._dbusservice['/Ac/L2/Energy/Reverse'] = 0
       self._dbusservice['/Ac/L3/Energy/Forward'] = 0
       self._dbusservice['/Ac/L3/Energy/Reverse'] = 0
       self._dbusservice['/Ac/Energy/Forward'] = float(meter_data['Body']['Data']['EnergyReal_WAC_Sum_Consumed'])/1000
       self._dbusservice['/Ac/Energy/Reverse'] = float(meter_data['Body']['Data']['EnergyReal_WAC_Sum_Produced'])/1000
       logging.info("Grid power: {:.0f} w Voltage: {:.0f} v".format(meter_consumption,meter_voltage))
       
       
       #logging
       logging.debug("House Consumption (/Ac/Power): %s" % (self._dbusservice['/Ac/Power']))
       logging.debug("House Forward (/Ac/Energy/Forward): %s" % (self._dbusservice['/Ac/Energy/Forward']))
       logging.debug("House Reverse (/Ac/Energy/Revers): %s" % (self._dbusservice['/Ac/Energy/Reverse']))
       logging.debug("---");
       
       # increment UpdateIndex - to show that new data is available
       index = self._dbusservice['/UpdateIndex'] + 1  # increment index
       if index > 255:   # maximum value of the index
         index = 0       # overflow from 255 to 0
       self._dbusservice['/UpdateIndex'] = index

       #update lastupdate vars
       self._lastUpdate = time.time()              
    except Exception as e:
       logging.critical('Error at %s', '_update', exc_info=e)
       
    # return true, otherwise add_timeout will be removed from GObject - see docs http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--timeout-add
    return True
 
  def _handlechangedvalue(self, path, value):
    logging.debug("someone else updated %s to %s" % (path, value))
    return True # accept the change
 


def main():
  #configure logging
  logging.basicConfig(      format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.ERROR,
                            handlers=[
                                logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                                logging.StreamHandler()
                            ])
 
  try:
      logging.info("Start");
  
      from dbus.mainloop.glib import DBusGMainLoop
      # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
      DBusGMainLoop(set_as_default=True)
     
      #formatting 
      _kwh = lambda p, v: (str(round(v, 2)) + ' KWh')
      _a = lambda p, v: (str(round(v, 1)) + ' A')
      _w = lambda p, v: (str(round(v, 1)) + ' W')
      _v = lambda p, v: (str(round(v, 1)) + ' V')   
     
      #start our main-service
      pvac_output = DbusFroniusMeterService(
        servicename='com.victronenergy.grid',
        deviceinstance=40,
        paths={
          '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh}, # energy bought from the grid
          '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh}, # energy sold to the grid
          '/Ac/Power': {'initial': 0, 'textformat': _w},
          
          '/Ac/Current': {'initial': 0, 'textformat': _a},
          '/Ac/Voltage': {'initial': 0, 'textformat': _v},
          
          '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
          '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
          '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
          '/Ac/L1/Energy/Forward': {'initial': 0, 'textformat': _kwh},
          '/Ac/L2/Energy/Forward': {'initial': 0, 'textformat': _kwh},
          '/Ac/L3/Energy/Forward': {'initial': 0, 'textformat': _kwh},
          '/Ac/L1/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
          '/Ac/L2/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
          '/Ac/L3/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
        })
     
      logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
      mainloop = gobject.MainLoop()
      mainloop.run()            
  except Exception as e:
    logging.critical('Error at %s', 'main', exc_info=e)
if __name__ == "__main__":
  main()
