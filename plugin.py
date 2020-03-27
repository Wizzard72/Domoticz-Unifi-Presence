# Unifi-Presence plugin
#
# Author: Wizzard72
#
"""
<plugin key="UnifiPresence" name="Unifi Presence" author="Wizzard72" version="1.0.0" wikilink="https://github.com/Wizzard72/Domoticz-Unifi-Presence">
    <description>
        <h2>Unifi Presence Detection plugin</h2><br/>
        To be done
    </description>
    <params>
        <param field="Address" label="IP Address / DNS name of the Unifi Controller" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="30px" required="true" default="8443"/>
        <param field="Username" label="Username" width="200px" required="true" default="admin@unifi.com"/>
        <param field="Password" label="Password" width="600px" required="true" default="password" password="true"/>
        <param field="Mode1" label="Site Name" width="200px" required="true" default="default"/>
        <param field="Mode2" label="MAC Phone Addresses" width="600px" required="true" default="Phone1=1A:2B:3C:4D:5E:6F,Phone2=7A:8B:9C:AD:BE:CF"/>
        <param field="Mode3" label="Extra devices to monitor" width="600px" required="false" default="phone10,phone20"/>
        <param field="Mode4" label="Interval" width="200px" required="true" default="15"/>
        <param field="Mode5" label="Notifications" width="75px">
            <options>
                <option label="True" value="True"/>
                <option label="False" value="False"  default="true" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import socket
import json
import re
import requests
#import urllib.request
#from urllib.parse import quote
import urllib
#import urllib.parse
from datetime import datetime
import time

icons = {"UnifiHome": "uhome.zip",
         "UnifiOverride": "uoverride.zip",
         "UnifiUnit": "uunit.zip"}


class BasePlugin:
    unifiConn = None
    override_time = 0
    hostAuth = False
    UNIFI_WLAN_COUNTER_UNIT = 1
    UNIFI_LAN_COUNTER_UNIT = 2
    UNIFI_CPU_PERC_UNIT = 3
    UNIFI_MEM_PERC_UNIT = 4
    UNIFI_BOARD_CPU_UNIT = 5
    UNIFI_BOARD_PHY_UNIT = 6
    UNIFI_CPU_UNIT = 7
    UNIFI_PHY_UNIT = 8
    UNIFI_UPTIME_UNIT = 9
    UNIFI_ANYONE_HOME_UNIT = 50
    UNIFI_OVERRIDE_UNIT = 255
    cookie = None
    cookieAvailable = False
    #unifises = ""
    #csrftoken = ""
    phone_name = ""
    Matrix = ""
    count_ex_device = 0
    
    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        strName = "onStart: "
        Domoticz.Debug(strName+"called")
        if (Parameters["Mode6"] != "0"):
            Domoticz.Debugging(int(Parameters["Mode6"]))
        else:
            Domoticz.Debugging(0)
        
        # load custom images
        #if "UnifiAnyone" not in Images: 
        #    Domoticz.Log(strName+"Add UnifiAnyone icons to Domoticz")
        #    Domoticz.Image("uanyone.zip").Create()
        #    #Domoticz.Log(strName+"UnifiHome ID = "+str(Images["UnifiHome"].ID))
        #else:
        #    Domoticz.Log(strName+"Already added UnifiAnyone icons to Domoticz")
        
        if "UnifiOverride" not in Images: 
            Domoticz.Log(strName+"Add UnifiOverride icons to Domoticz")
            Domoticz.Image("uoverride.zip").Create()
        else:
            Domoticz.Log(strName+"Already added UnifiOverride icons to Domoticz")
        
        #if "UnifiApp" not in Images: 
        #    Domoticz.Log(strName+"Add UnifiApp icons to Domoticz")
        #    Domoticz.Image("uapp.zip").Create()
        #else:
        #    Domoticz.Log(strName+"Already added UnifiApp icons to Domoticz")
        
        #Domoticz.Log(strName+"TEST IMAGE = "+str(Images['UnifiApp'].ID))
        Domoticz.Log("Number of icons loaded = " + str(len(Images)))
        for item in Images:
            Domoticz.Log(strName+"Items = "+str(item))
            Domoticz.Log(strName+"Icon " + str(Images[item].ID) + " Name = " + Images[item].Name)
        
        if (self.UNIFI_WLAN_COUNTER_UNIT not in Devices):
            Domoticz.Device(Name="WLAN Counter",  Unit=self.UNIFI_WLAN_COUNTER_UNIT, Used=1, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_WLAN_COUNTER_UNIT, 0, "0")

        if (self.UNIFI_LAN_COUNTER_UNIT not in Devices):
            Domoticz.Device(Name="LAN Counter",  Unit=self.UNIFI_LAN_COUNTER_UNIT, Used=1, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_LAN_COUNTER_UNIT, 0, "0")
            
        if (self.UNIFI_ANYONE_HOME_UNIT not in Devices):
            Domoticz.Device(Name="AnyOne",  Unit=self.UNIFI_ANYONE_HOME_UNIT, Used=1, TypeName="Switch", Image=116).Create()
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 0, "Off")
            
        if (self.UNIFI_OVERRIDE_UNIT not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "Off|1 hour|2 hours|3 hours|On",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="OverRide", Unit=self.UNIFI_OVERRIDE_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options).Create()
        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 0, "0")
        
        if (self.UNIFI_CPU_PERC_UNIT not in Devices):
            Domoticz.Device(Name="Gateway CPU Percentage",  Unit=self.UNIFI_CPU_PERC_UNIT, Used=1, TypeName="Percentage").Create()
            UpdateDevice(self.UNIFI_CPU_PERC_UNIT, 0, "0")
        
        if (self.UNIFI_MEM_PERC_UNIT not in Devices):
            Domoticz.Device(Name="Gateway Mem Percentage",  Unit=self.UNIFI_MEM_PERC_UNIT, Used=1, TypeName="Percentage").Create()
            UpdateDevice(self.UNIFI_MEM_PERC_UNIT, 0, "0")
        
        if (self.UNIFI_BOARD_CPU_UNIT not in Devices):
            Domoticz.Device(Name="Gateway Board (CPU) Temperature",  Unit=self.UNIFI_BOARD_CPU_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_BOARD_CPU_UNIT, 0, "0")
        
        if (self.UNIFI_BOARD_PHY_UNIT not in Devices):
            Domoticz.Device(Name="Gateway Board (PHY) Temperature",  Unit=self.UNIFI_BOARD_PHY_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_BOARD_PHY_UNIT, 0, "0")
        
        if (self.UNIFI_CPU_UNIT not in Devices):
            Domoticz.Device(Name="Gateway CPU Temperature",  Unit=self.UNIFI_CPU_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_CPU_UNIT, 0, "0")
        
        if (self.UNIFI_PHY_UNIT not in Devices):
            Domoticz.Device(Name="Gateway PHY Temperature",  Unit=self.UNIFI_PHY_UNIT, Used=1, TypeName="Temperature").Create()
            UpdateDevice(self.UNIFI_PHY_UNIT, 0, "0")
            
        if (self.UNIFI_UPTIME_UNIT not in Devices):
            Domoticz.Device(Name="Uptime (hours)", Unit=self.UNIFI_UPTIME_UNIT, Used=1, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_UPTIME_UNIT, 0, "0.0")
        
        device_mac=Parameters["Mode2"].split(",")
        device_extra=Parameters["Mode3"].split(",")
        
        found_phone = False
        count_phone = 0
        for device in device_mac:
            device = device.strip()
            phone_name, mac_id = device.split("=")
            phone_name = phone_name.strip()
            mac_id = mac_id.strip().lower()
            try:
                for item in Devices:
                    if Devices[item].Name[8:] == phone_name:
                        Domoticz.Log(strName+"Found phone from configuration = "+device)
                        found_phone = True
                if found_phone == False:
                    new_unit = find_available_unit()
                    Domoticz.Device(Name=phone_name, Unit=new_unit, TypeName="Switch", Used=1, Image=Images['UnifiApp'].ID).Create()
            except:
                Domoticz.Error(strName+"Invalid phone settings. (" +device+")")
            count_phone = count_phone + 1
        
        # Extra devices for Geo Fence for example
        found_phone = False
        #count_ex_device = 0
        for ex_device in device_extra:
            ex_device = ex_device.strip()
            phone_name = ex_device
            try:
                for item in Devices:
                    if Devices[item].Name[8:] == phone_name:
                        Domoticz.Log(strName+"Found devices to monitor from configuration = "+device)
                        found_phone = True
                if found_phone == False:
                    new_unit = find_available_unit()
                    Domoticz.Device(Name=phone_name, Unit=new_unit, TypeName="Switch", Used=1).Create()
            except:
                Domoticz.Error(strName+"Invalid phone settings. (" +device+")")
            self.count_ex_device = self.count_ex_device + 1
        
        extra_devices = 1 # Override device
        self.total_devices_count = count_phone + self.count_ex_device + extra_devices
        Domoticz.Debug(strName+"total_devices = "+str(self.total_devices_count))
        # Create table
        device_mac=Parameters["Mode2"].split(",")
        device_extra=Parameters["Mode3"].split(",")
        w, h = 6, self.total_devices_count;
        self.Matrix = [[0 for x in range(w)] for y in range(h)] 
        # table:
        # Phone_Name | MAC_ID | Unit_Number | State | Changed | Refresh
        # Matrix[0][0] = 1
        count = 1
        found_user = None
        self.Matrix[0][0] = "OverRide"            # Used for the OverRide Selector Switch
        self.Matrix[0][1] = "00:00:00:00:00:00"   # Used for the OverRide Selector Switch
        self.Matrix[0][2] = 255                   # Used for the OverRide Selector Switch
        self.Matrix[0][3] = "Off"                 # Used for the OverRide Selector Switch
        self.Matrix[0][4] = "No"                  # Used for the OverRide Selector Switch
        self.Matrix[0][5] = "No"                  # Used for the OverRide Selector Switch
        for device in device_mac:
            device = device.strip()
            Device_Name, Device_Mac = device.split("=")
            self.Matrix[count][0] = Device_Name 
            self.Matrix[count][1] = Device_Mac
            Device_Unit = None
            self.Matrix[count][3] = "Off"
            self.Matrix[count][4] = "No"
            self.Matrix[count][5] = "Yes"
            found_user = Device_Name
            for dv in Devices:
                # Find the unit number
                search_phone = Devices[dv].Name[8:]
                if Devices[dv].Name[8:] == found_user:
                    self.Matrix[count][2] = Devices[dv].Unit
                    continue
            Domoticz.Log(strName+"Phone Naam = "+self.Matrix[count][0]+" | "+str(self.Matrix[count][1])+" | "+str(self.Matrix[count][2])+" | "+self.Matrix[count][3]+" | "+self.Matrix[count][4])
            count = count + 1
        
        # Extra devices for Geo Fence for example
        for ex_device in device_extra:
            Domoticz.Log(strName+"ex_device = "+str(ex_device))
            Domoticz.Log(strName+"count = "+str(count))
            self.Matrix[count][0] = ex_device.strip()
            self.Matrix[count][1] = "11:11:11:11:11:11"
            self.Matrix[count][3] = "Off"
            self.Matrix[count][4] = "No"
            self.Matrix[count][5] = "No"
            found_user = ex_device.strip()
            for dv in Devices:
                # Find the unit number
                search_phone = Devices[dv].Name[8:]
                if Devices[dv].Name[8:] == found_user:
                    self.Matrix[count][2] = Devices[dv].Unit
                    continue
            #Domoticz.Log(strName+"Phone Naam = "+self.Matrix[count][0]+" | "+str(self.Matrix[count][1])+" | "+str(self.Matrix[count][2])+" | "+self.Matrix[count][3]+" | "+self.Matrix[count][4])
            count = count + 1
            
        x = range(0, self.total_devices_count, 1)
        for n in x:
            Domoticz.Log(strName+"Phone Naam = "+self.Matrix[n][0]+" | "+str(self.Matrix[n][1])+" | "+str(self.Matrix[n][2])+" | "+self.Matrix[n][3]+" | "+self.Matrix[n][4]+" | "+self.Matrix[n][5])
            

        self.SetupConnection()
        Domoticz.Heartbeat(int(Parameters["Mode4"]))

    def onStop(self):
        strName = "onStop: "
        Domoticz.Debug(strName+"Pluggin is stopping.")
        sendData = {'Verb' : 'GET',
                    'URL'  : '/api/logout',
                    'Headers' : {
                                'Cookie': self.cookie, \
                                'Content-Type': 'application/json; charset=utf-8', \
                                'Host': "https://"+Parameters["Address"]+":"+Parameters["Port"]
                                }
                    }
        #Domoticz.Log("RequestDetails: sendData = "+str(sendData))
        #self.unifiConn.Send(sendData)

    def onConnect(self, Connection, Status, Description):
        strName = "onConnect: "
        Domoticz.Debug(strName+"called")
        Domoticz.Debug(strName+"Connection = "+str(Connection))
        Domoticz.Debug(strName+"Status = "+str(Status))
        Domoticz.Debug(strName+"Description = "+str(Description))
        if (self.hostAuth == False):
            Domoticz.Log(strName+"Start Authentication process")
            self.Authenticate()
        if (Status == 0):
            Domoticz.Log(strName+"Unifi Controller connected successfully.")
            self.Authenticate()
        else:
            Domoticz.Error(strName+"Failed to connect ("+str(Status)+") to: https://"+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        strName = "onMessage: "
        Domoticz.Debug(strName+"called")
        DumpHTTPResponseToLog(Data)
        Domoticz.Debug(strName+"Data = " +str(Data))
        strData = Data["Data"].decode("utf-8", "ignore")
        status = int(Data["Status"])

        if (self.unifiConn.Connecting() or self.unifiConn.Connected()):
            Domoticz.Debug(strName+"Unifi Controller connection is alive.")
            
        if (status == 200):
            unifiResponse = json.loads(strData)
            Domoticz.Debug(strName+"Retrieved following json: "+json.dumps(unifiResponse))
            
            self.ProcessCookie(Data)
            self.RequestDetails()
            if (('meta' in unifiResponse)):
                self.hostAuth = True
                Domoticz.Debug(strName+"hostAuth = True")
                self.countDown = self.ProcessDetails(unifiResponse['meta'])
                return
            else:
                Domoticz.Error(strName+"Error: HostAuth = False")
        elif status == 302:
            Domoticz.Error(strName+"Unifi Controller returned a Page Moved Error.")
        elif status == 400:
            Domoticz.Error(strName+"Unifi Controller returned a Bad Request Error.")
        elif (status == 500):
            Domoticz.Error(strName+"Unifi Controller returned a Server Error.")
        else:
            Domoticz.Error(strName+'Unifi Controller returned status='+Data['Status'])

    def onCommand(self, Unit, Command, Level, Hue):
        strName = "onCommand: "
        Domoticz.Log(strName+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if self.UNIFI_OVERRIDE_UNIT == Unit:
       
            if Level == 0: # Override Off
                self.override_time = 0 #seconds
                Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 1, str(Level))
                self.Matrix[0][3] = "Off"
                self.Matrix[0][4] = "Yes"
                self.Matrix[0][5] = "Change"
		
            
            elif Level == 10: # Override 1 hour
                self.override_time = 60 * 60 #seconds
                Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 1, str(Level))
                self.Matrix[0][3] = "On"
                self.Matrix[0][4] = "Yes"
                self.Matrix[0][5] = "Change"

            elif Level == 20: # Override 2 hours
                self.override_time = 2 * 60 * 60 #seconds
                Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 1, str(Level))
                self.Matrix[0][3] = "On"
                self.Matrix[0][4] = "Yes"
                self.Matrix[0][5] = "Change"

            elif Level == 30: # Override 3 hour
                self.override_time = 3 * 60 * 60 #seconds
                Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 1, str(Level))
                self.Matrix[0][3] = "On"
                self.Matrix[0][4] = "Yes"
                self.Matrix[0][5] = "Change"

            elif Level == 40: # Override On
                self.override_time = 99999999999 #seconds
                Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 1, str(Level))
                self.Matrix[0][3] = "On"
                self.Matrix[0][4] = "Yes"
                self.Matrix[0][5] = "Change"
            
                   
        t = self.total_devices_count - self.count_ex_device
        Domoticz.Log(strName+"Range = "+str(t)+" - "+str(self.total_devices_count-1))
        for r in range(t, self.total_devices_count):
            Domoticz.Log(strName+"r = "+str(r)+" / self.Matrix[r][2] = "+str(self.Matrix[r][2])+" / Unit = "+str(Unit))
            if self.Matrix[r][2] == Unit:
                if str(Command) == "On":
                    svalue = "On"
                    nvalue = 1
                    UpdateDevice(Unit, nvalue, svalue)
                    self.Matrix[r][3] = "On"
                    self.Matrix[r][4] = "Yes"
                    self.Matrix[r][5] = "Change"
                    #Unit 55: Parameter 'On', Level: 0
                else:
                    svalue = "Off"
                    nvalue = 0
                    UpdateDevice(Unit, nvalue, svalue)
                    self.Matrix[r][3] = "Off"
                    self.Matrix[r][4] = "Yes"
                    self.Matrix[r][5] = "Change"
        
        for x in range(self.total_devices_count):
            Domoticz.Log(strName+" "+str(x)+" Phone Naam = "+self.Matrix[x][0]+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+self.Matrix[x][3]+" | "+self.Matrix[x][4]+" | "+self.Matrix[x][5])
        
        self.ProcessDevices("change")
                
                
    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        strName = "onNotification: "
        Domoticz.Debug(strName+"called")
        Domoticz.Log(strName+"Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        strName = "onDisconnect: "
        Domoticz.Debug(strName+"called")

    def onHeartbeat(self):
        strName = "onHeartbeat: "
        Domoticz.Debug(strName+"called")
        #if (self.unifiConn != None) and (self.unifiConn.Connecting()):
        #    return
        
        if self.Matrix[0][3] == "On":
            try:
                timeDiff = datetime.now() - datetime.strptime(Devices[255].LastUpdate,'%Y-%m-%d %H:%M:%S')
            except TypeError:
                timeDiff = datetime.now() - datetime(*(time.strptime(Devices[255].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
            timeDiffSeconds = timeDiff.seconds
            Domoticz.Log(strName+"OverRide is on for: "+str(timeDiffSeconds)+" seconds")
            if timeDiffSeconds >= self.override_time:
                self.Matrix[0][3] = "Off"
                self.Matrix[0][4] = "Yes"
        
        if (self.unifiConn == None) or (not self.unifiConn.Connected()):
                Domoticz.Log(strName+'Attempting to reconnect Unifi Controller')
                self.SetupConnection()
        else:
            if self.hostAuth:
                Domoticz.Log(strName+'Requesting Unifi Controller details')
                self.RequestDetails()
            else:
                Domoticz.Log(strName+"Requesting Unifi Controller authorization.")
                Domoticz.Debug(strName+"hostAuth = "+str(self.hostAuth))
                self.Authenticate()

    def SetupConnection(self):
        strName = "SetupConnection: "
        Domoticz.Debug(strName+"called")
        self.unifiConn = Domoticz.Connection(Name='UnifiPresenceConn', Transport="TCP/IP", Protocol="HTTPS", Address=Parameters["Address"], Port=Parameters["Port"])
        self.unifiConn.Connect()
        
    def RequestDetails(self):
        strName = "RequestDetails: "
        Domoticz.Debug(strName+"called")
        host = "https://"+Parameters["Address"]+":"+Parameters["Port"]
        url_api_s_default_stat_health = "/api/s/"+Parameters["Mode1"]+"/stat/health"
        reqapi = urllib.request.Request(host+url_api_s_default_stat_health,headers={'Cookie':self.cookie})
        responseapi = urllib.request.urlopen(reqapi)
        test = responseapi.read().decode('utf-8', 'ignore')
        testjson = json.loads(test)
        url = "/api/s/"+str(Parameters["Mode1"])+"/stat/health"
        sendData = {'Verb' : 'GET',
                    'URL'  : '/api/s/default/stat/health',
                    'Headers' : {
                                'Cookie': self.cookie, \
                                'Connection': 'keep-alive', \
                                'Content-Encoding': 'gzip', \
                                'Content-Type': 'application/json; charset=utf-8', \
                                'Host': "https://"+Parameters["Address"]+":"+Parameters["Port"]
                                }
                    }
#        Domoticz.Log("RequestDetails: sendData = "+str(sendData))
#        self.unifiConn.Send(sendData)
        if ('meta' in testjson):
            meta = testjson['meta']
            if (meta['rc'] == "ok"):
                Domoticz.Debug(strName+"AUTHENTICATED: " +meta['rc'])
        if ('data' in testjson):
            data = testjson['data']
            for item in data:
                if item['subsystem'] == "wlan":
                    wlan = item
                    wlan_user_count = wlan['num_user']
                    UpdateDevice(self.UNIFI_WLAN_COUNTER_UNIT, int(wlan_user_count), str(wlan_user_count))
                if item['subsystem'] == "lan":
                    lan = item
                    lan_user_count = lan['num_user']
                    UpdateDevice(self.UNIFI_LAN_COUNTER_UNIT, int(lan_user_count), str(lan_user_count))
                if item['subsystem'] == "wan":
                    wan = item
                    cpu_pers = wan['gw_system-stats']['cpu']
                    UpdateDevice(self.UNIFI_CPU_PERC_UNIT, int(cpu_pers), str(cpu_pers))
                    mem_pers = wan['gw_system-stats']['mem']
                    UpdateDevice(self.UNIFI_MEM_PERC_UNIT, int(mem_pers), str(mem_pers))
                    board_cpu = wan['gw_system-stats']['temps']['Board (CPU)'][:-2]
                    UpdateDevice(self.UNIFI_BOARD_CPU_UNIT, int(board_cpu), str(board_cpu))
                    board_phy = wan['gw_system-stats']['temps']['Board (PHY)'][:-2]
                    UpdateDevice(self.UNIFI_BOARD_PHY_UNIT, int(board_phy), str(board_phy))
                    cpu = wan['gw_system-stats']['temps']['CPU'][:-2]
                    UpdateDevice(self.UNIFI_CPU_UNIT, int(cpu), str(cpu))
                    phy = wan['gw_system-stats']['temps']['PHY'][:-2]
                    UpdateDevice(self.UNIFI_PHY_UNIT, int(phy), str(phy))
                    uptime = int(wan['gw_system-stats']['uptime'])/3600
                    UpdateDevice(self.UNIFI_UPTIME_UNIT, int(uptime), str(uptime))
                    

        url = "/api/s/"+str(Parameters["Mode1"])+"/stat/sta"  
        url_api_s_default_stat_sta = "/api/s/"+Parameters["Mode1"]+"/stat/sta"
        reqapi = urllib.request.Request(host+url_api_s_default_stat_sta,headers={'Cookie':self.cookie})
        responseapi = urllib.request.urlopen(reqapi)
        test = responseapi.read().decode('utf-8', 'ignore')
        testjson = json.loads(test)
        
        if ('meta' in testjson):
            meta = testjson['meta']
            if (meta['rc'] == "ok"):
                Domoticz.Debug(strName+"AUTHENTICATED: " +meta['rc'])
                if ('data' in testjson):
                    data = testjson['data']
                    for item in data:
                        device_mac=Parameters["Mode2"].split(",")
                        found_mac = 0
                        found_mac_address = None
                        found_user = None
                        for device in device_mac:
                            device_unit = None
                            device = device.strip()
                            phone_name, mac_id = device.split("=")
                            phone_name = phone_name.strip()
                            mac_id = mac_id.strip().lower()
                            if str(item['mac']) == mac_id and not item['is_wired']:
                                # Found MAC address in API output
                                for x in range(self.total_devices_count):
                                    if self.Matrix[x][1] == mac_id:
                                        Domoticz.Log(strName+"Found phone ON "+self.Matrix[x][0])
                                        self.Matrix[x][3] = "On"
                                        self.Matrix[x][4] = "Yes"
        self.ProcessDevices("normal")
        
    def ProcessDevices(self, action):
        strName = "ProcessDevices: "
        for x in range(self.total_devices_count):
            Domoticz.Debug(strName+" "+str(x)+" Phone Naam = "+self.Matrix[x][0]+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+self.Matrix[x][3]+" | "+self.Matrix[x][4])
            if action == "normal" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "Yes":
                if self.Matrix[x][3] == "On":
                    svalue = "On"
                    nvalue = 1
                    if self.Matrix[x][0] == "OverRide":
                        self.Matrix[x][4] = "Yes"
                    else:
                        UpdateDevice(self.Matrix[x][2], nvalue, svalue)
                        self.Matrix[x][4] = "No"
                else:
                    svalue = "Off"
                    nvalue = 0
                    if self.Matrix[x][0] == "OverRide":
                        UpdateDevice(self.Matrix[x][2], nvalue, "0")
                    else:
                        UpdateDevice(self.Matrix[x][2], nvalue, svalue)
                        self.Matrix[x][3] = svalue
            elif action == "change" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "Change":
                if self.Matrix[x][3] == "On":
                    svalue = "On"
                    nvalue = 1
                    if self.Matrix[x][0] == "OverRide":
                        self.Matrix[x][4] = "Yes"
                        self.Matrix[x][5] = "No"
                        
                    else:
                        UpdateDevice(self.Matrix[x][2], nvalue, svalue)
                        self.Matrix[x][4] = "No"
                        self.Matrix[x][5] = "No"
                else:
                    svalue = "Off"
                    nvalue = 0
                    if self.Matrix[x][0] == "OverRide":
                        UpdateDevice(self.Matrix[x][2], nvalue, "0")
                    else:
                        UpdateDevice(self.Matrix[x][2], nvalue, svalue)
                        self.Matrix[x][3] = svalue
            elif action == "change" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "No":
                Domoticz.Log(strName+"Nothing to do")
            elif action == "change" and self.Matrix[x][4] == "No" and self.Matrix[x][5] == "No":
                Domoticz.Log(strName+"Nothing to do")
            else:
                if action == "normal" and self.Matrix[x][5] == "Yes":
                    svalue = "Off"
                    nvalue = 0
                    if self.Matrix[x][0] == "OverRide":
                        UpdateDevice(self.Matrix[x][2], nvalue, "0")
                    else:
                        UpdateDevice(self.Matrix[x][2], nvalue, svalue)
                        self.Matrix[x][3] = svalue
            
        
        count = 0
        for x in range(self.total_devices_count):
            Domoticz.Debug(strName+" "+str(x)+" Phone Naam = "+self.Matrix[x][0]+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+self.Matrix[x][3]+" | "+self.Matrix[x][4]+" | "+self.Matrix[x][5])
            if self.Matrix[x][3] == "On":
                count = count + 1
        Domoticz.Log(strName+"Total Phones connected = "+str(count))
        if count > 0:
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 1, "On")
        else:
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 0, "Off")


    def Authenticate(self):
        strName = "Authenticate: "
        Domoticz.Debug(strName+"called")
        payload = { "password" : Parameters["Password"],"username" : Parameters["Username"] }
        jsondata = json.dumps(payload)
        jsondataasbytes = jsondata.encode('utf-8')
        #url_api_login = "/api/login"
        #url = "https://"+Parameters["Address"]+":"+Parameters["Port"]+url_api_login
        #req = urllib.request.Request(url)
        #req.add_header('Content-Type', 'application/json; charset=utf-8')
        #req.add_header('Content-Length', len(jsondataasbytes))
        #response = urllib.request.urlopen(req, jsondataasbytes)
        #cookie = response.getheader('Set-Cookie')
        #Domoticz.Log("Cookie = " +cookie)	
        sendData = { 'Verb' : 'POST',
                     'URL'  : '/api/login',
                     'Headers' : { 
                         'Content-Type': 'application/json; charset=utf-8', \
                         'Host': Parameters["Address"]+":"+Parameters["Port"]
                         },
                     'Data' : json.dumps(payload)
                   }
        Domoticz.Debug(strName+"sendData = "+str(sendData))
        self.unifiConn.Send(sendData)
        
    
    def ProcessDetails(self, response):
        strName = "ProcessDetails: "
        Domoticz.Debug(strName+"called")
        if (('rc' in response) and (str(response['rc']) == "ok")):
            Domoticz.Log(strName+"Authenticated succesfull to Unifi Controller")
            hostAuth = True
        else:
            Domoticz.Log(strName+"Authenticated NOT succesfull to Unifi Controller")
            hostAuth = False


    def ProcessCookie(self, httpDict):
        strName = "ProcessCookie: "
        if isinstance(httpDict, dict):
            Domoticz.Debug(strName+"Analyzing Data ("+str(len(httpDict))+"):")
            for x in httpDict:
                if isinstance(httpDict[x], dict):
                    if (x == "Headers"):
                        Domoticz.Debug(strName+"---> Headers found")
                        for y in httpDict[x]:
                            Domoticz.Debug(strName+"------->'" + y + "':'" + str(httpDict[x][y]) + "'")
                            if (y == "Set-Cookie"):
                                Domoticz.Debug(strName+"---> Found Cookie")
                                self.cookie = str(httpDict[x][y])[:-2][2:]
                                self.cookieAvailable = True


				
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def LogMessage(Message):
    strName = "LogMessage: "
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Debug(strName+"File written")

def DumpHTTPResponseToLog(httpResp, level=0):
    strName = "DumpHTTPResponseToLog: "
    if (level==0): Domoticz.Debug(strName+"HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(strName+indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(strName+indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(strName+indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(strName+indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")

def UpdateDevice(Unit, nValue, sValue, Image=None):
    strName = "UpdateDevice: "
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or ((Image != None) and (Image != Devices[Unit].Image)):
            if (Image != None) and (Image != Devices[Unit].Image):
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue), Image=Image)
                Domoticz.Log(strName+"Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+") Image="+str(Image))
            else:
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Log(strName+"Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")

    # Generic helper functions
def DumpConfigToLog():
    strName = "DumpConfigToLog: "
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug(strName+"'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug(strName+"Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug(strName+"Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug(strName+"Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug(strName+"Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug(strName+"Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug(strName+"Device LastLevel: " + str(Devices[x].LastLevel))
    return

def find_available_unit():
    for num in range(51,200):
        if num not in Devices:
            return num
    return None
