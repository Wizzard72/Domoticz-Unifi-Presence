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
        <param field="Mode2" label="MAC Phone Addresses" width="600px" required="true" default="1A:2B:3C:4D:5E:6F,7A:8B:9C:AD:BE:CF"/>
        <param field="Mode3" label="Interval" width="200px" required="true" default="15"/>
        <param field="Mode4" label="Notifications" width="75px">
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
import urllib.request
from urllib.parse import quote
import urllib
import urllib.parse


class BasePlugin:
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
    #PHONE_ON_IMG = 'PhoneOn'
    #PHONE_OFF_IMG = 'PhoneOff'
    cookie = None
    cookieAvailable = False
    unifises = ""
    csrftoken = ""
    phone_name = ""
    
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
        
        #Create "Anyone home" device
        #if self.UNIFI_ANYONE_HOME_UNIT not in Devices:
        #    get_or_create_unit('Anyone', unit=self.UNIFI_ANYONE_HOME_UNIT, icon='idetect-home')
        
        #Create "Override" device
        #if self.UNIFI_OVERRIDE_UNIT not in Devices:
        #    get_or_create_unit('Override', unit=self.UNIFI_OVERRIDE_UNIT, icon='idetect-override')
        
        if (self.UNIFI_WLAN_COUNTER_UNIT not in Devices):
            Domoticz.Device(Name="WLAN Counter",  Unit=self.UNIFI_WLAN_COUNTER_UNIT, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_WLAN_COUNTER_UNIT, 0, "0")

        if (self.UNIFI_LAN_COUNTER_UNIT not in Devices):
            Domoticz.Device(Name="LAN Counter",  Unit=self.UNIFI_LAN_COUNTER_UNIT, Type=243, Subtype=31).Create()
            UpdateDevice(self.UNIFI_LAN_COUNTER_UNIT, 0, "0")

        if (self.UNIFI_ANYONE_HOME_UNIT not in Devices):
            Domoticz.Device(Name="AnyOne",  Unit=self.UNIFI_ANYONE_HOME_UNIT, Used=1, TypeName="Switch").Create()
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 0, "Off")
            
        if (self.UNIFI_OVERRIDE_UNIT not in Devices):
            Domoticz.Device(Name="OverRide",  Unit=self.UNIFI_OVERRIDE_UNIT, Used=1, TypeName="Switch").Create()
            UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 0, "Off")
        
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
            
        for item in Devices:
            Domoticz.Log(strName+"item in devices = " +Devices[item].Name)
            Domoticz.Log(strName+"item in devices = " +Devices[item].DeviceID)
            Domoticz.Log(strName+"item in devices = " +str(Devices[item].ID))
            Domoticz.Log(strName+"item in devices = " +str(Devices[item].Unit))
		
		
        device_mac=Parameters["Mode2"].split(",")
        found_phone = False
        for device in device_mac:
            device = device.strip()
            phone_name, mac_id = device.split("=")
            phone_name = phone_name.strip()
            mac_id = mac_id.strip().lower()
            try:
                for item in Devices:
                    #Domoticz.Log(strName+"Device.item = " +Devices[item].Name[8:])
                    if Devices[item].Name[8:] == phone_name:
                        Domoticz.Log(strName+"Found phone = "+device)
                        found_phone = True
                if found_phone == False:
                    new_unit = find_available_unit()
                    Domoticz.Device(Name=phone_name, Unit=new_unit, TypeName="Switch", Used=1).Create()
                    #Domoticz.Status(strName+"Created device for "+phone_name+" with unit id " + str(new_unit))
            except:
                Domoticz.Error(strName+"Invalid phone settings. (" +device+")")
            
        for dv in Devices:
            #Domoticz.Log(strName+"Devices Name = "+Devices[dv].Name[8:]+" = "+phone_name)
            if Devices[dv].Name[8:] == "Paul":
                device_unit = Devices[dv].Unit
                Domoticz.Log(strName+"Paul Phone Unit = "+str(device_unit))
            elif Devices[dv].Name[8:] == "Sarah":
                device_unit = Devices[dv].Unit
                Domoticz.Log(strName+"Paul Phone Unit = "+str(device_unit))
            elif Devices[dv].Name[8:] == "Peter":
                device_unit = Devices[dv].Unit
                Domoticz.Log(strName+"Paul Phone Unit = "+str(device_unit))
            elif Devices[dv].Name[8:] == "Leni":
                device_unit = Devices[dv].Unit
                Domoticz.Log(strName+"Paul Phone Unit = "+str(device_unit))
                

        self.SetupConnection()
        Domoticz.Heartbeat(int(Parameters["Mode3"]))

    def onStop(self):
        strName = "onStop: "
        Domoticz.Log(strName+"Pluggin is stopping.")
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
        Domoticz.Log(strName+"called")
        Domoticz.Log(strName+"Connection = "+str(Connection))
        Domoticz.Log(strName+"Status = "+str(Status))
        Domoticz.Log(strName+"Description = "+str(Description))
        if (self.hostAuth == False):
            Domoticz.Log(strName+"Start Authentication process")
            self.Authenticate()
        if (Status == 0):
            Domoticz.Log(strName+"Unifi Controller connected successfully.")
            self.Authenticate()
        else:
            Domoticz.Log(strName+"Failed to connect ("+str(Status)+") to: https://"+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        strName = "onMessage: "
        Domoticz.Log(strName+"called")
        DumpHTTPResponseToLog(Data)
        Domoticz.Log(strName+"Data = " +str(Data))
        strData = Data["Data"].decode("utf-8", "ignore")
        status = int(Data["Status"])

        if (self.unifiConn.Connecting() or self.unifiConn.Connected()):
            Domoticz.Debug(strName+"Unifi Controller connection is alive.")
            
        if (status == 200):
            unifiResponse = json.loads(strData)
            Domoticz.Log(strName+"Retrieved following json: "+json.dumps(unifiResponse))
            
            self.ProcessCookie(Data)
            self.RequestDetails()
            if (('meta' in unifiResponse)):
                self.hostAuth = True
                Domoticz.Log(strName+"hostAuth = True")
                self.countDown = self.ProcessDetails(unifiResponse['meta'])
                return
            else:
                Domoticz.Log(strName+"Error: HostAuth = False")
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

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        strName = "onNotification: "
        Domoticz.Log(strName+"called")
        Domoticz.Log(strName+"Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        strName = "onDisconnect: "
        Domoticz.Log(strName+"called")

    def onHeartbeat(self):
        strName = "onHeartbeat: "
        Domoticz.Log(strName+"called")
        #if (self.unifiConn != None) and (self.unifiConn.Connecting()):
        #    return
        
        if (self.unifiConn == None) or (not self.unifiConn.Connected()):
                Domoticz.Log(strName+'Attempting to reconnect Unifi Controller')
                self.SetupConnection()
        else:
            if self.hostAuth:
                Domoticz.Log(strName+'Requesting Unifi Controller details')
                self.RequestDetails()
            else:
                Domoticz.Log(strName+"Requesting Unifi Controller authorization.")
                Domoticz.Log(strName+"hostAuth = "+str(self.hostAuth))
                self.Authenticate()

    def SetupConnection(self):
        strName = "SetupConnection: "
        Domoticz.Log(strName+"called")
        self.unifiConn = Domoticz.Connection(Name='UnifiPresenceConn', Transport="TCP/IP", Protocol="HTTPS", Address=Parameters["Address"], Port=Parameters["Port"])
        self.unifiConn.Connect()
        
    def RequestDetails(self):
        strName = "RequestDetails: "
        Domoticz.Log(strName+"called")
        host = "https://"+Parameters["Address"]+":"+Parameters["Port"]
        url_api_s_default_stat_health = "/api/s/"+Parameters["Mode1"]+"/stat/health"
        reqapi = urllib.request.Request(host+url_api_s_default_stat_health,headers={'Cookie':self.cookie})
        responseapi = urllib.request.urlopen(reqapi)
        test = responseapi.read().decode('utf-8', 'ignore')
        testjson = json.loads(test)
        #Domoticz.Log(strName+"API Response (test) = " +test)
        #Domoticz.Log(strName+"URL = "+'/api/s/'+Parameters["Mode1"]+'/stat/sta')
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
                Domoticz.Log(strName+"AUTHENTICATED: " +meta['rc'])
        if ('data' in testjson):
            data = testjson['data']
            for item in data:
#                Domoticz.Log(strName+"items = " +str(item))
                if item['subsystem'] == "wlan":
                    wlan = item
                    wlan_user_count = wlan['num_user']
                    Domoticz.Log(strName+"WLAN User_Count = " +str(wlan_user_count))
                    UpdateDevice(self.UNIFI_WLAN_COUNTER_UNIT, int(wlan_user_count), str(wlan_user_count))
                if item['subsystem'] == "lan":
                    lan = item
                    lan_user_count = lan['num_user']
                    Domoticz.Log(strName+"LAN User_Count = " +str(lan_user_count))
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
                    uptime = wan['gw_system-stats']['uptime']

        url = "/api/s/"+str(Parameters["Mode1"])+"/stat/sta"  
        url_api_s_default_stat_sta = "/api/s/"+Parameters["Mode1"]+"/stat/sta"
        reqapi = urllib.request.Request(host+url_api_s_default_stat_sta,headers={'Cookie':self.cookie})
        responseapi = urllib.request.urlopen(reqapi)
        test = responseapi.read().decode('utf-8', 'ignore')
        testjson = json.loads(test)
        #Domoticz.Log(strName+"API Response (test) = " +test)
        #Domoticz.Log(strName+"URL = "+str(url_api_s_default_stat_sta))
        
        if ('meta' in testjson):
            meta = testjson['meta']
            if (meta['rc'] == "ok"):
                Domoticz.Log(strName+"AUTHENTICATED: " +meta['rc'])
        if ('data' in testjson):
            data = testjson['data']
            for item in data:
                device_mac=Parameters["Mode2"].split(",")
                #device_unit = None
                count = 0
                for device in device_mac:
                    device_unit = None
                    device = device.strip()
                    phone_name, mac_id = device.split("=")
                    phone_name = phone_name.strip()
                    mac_id = mac_id.strip().lower()
                    #Domoticz.Log(strName+"MAC = " +str(item['mac'])+" = "+mac_id)
                    #Domoticz.Log(strName+"is wired = "+str(item['is_wired']))
                    if str(item['mac']) == mac_id and item['is_wired']:
                        #Domoticz.Log(strName+"--------------------------")
                        #Domoticz.Log(strName+"Phone Name = "+phone_name)
                        #Domoticz.Log(strName+"Found a matching MAC pair! ("+str(item['mac'])+"="+mac_id+" = "+phone_name)
                        count = 1
                    #Domoticz.Log(strName+"<++++++++++++++++++++++++++>")
                    for dv in Devices:
                        #Domoticz.Log(strName+"Devices Name = "+Devices[dv].Name[8:]+" = "+phone_name)
                        if phone_name == Devices[dv].Name[8:]:
                            #Domoticz.Log(strName+"Found phone Unit = "+str(Devices[dv].Unit)+" / Name = "+Devices[dv].Name+" / Phone Name = "+phone_name)
                            device_unit = Devices[dv].Unit
                    #Domoticz.Log(strName+"<++++++++++++++++++++++++++>")
                if count == 1:
                    svalue = "On"
                    nvalue = 1
                    #UpdateDevice(device_unit, nvalue, svalue)
                    #Devices[device_unit].Update(nValue=nvalue, sValue=str(svalue))
                else:
                    svalue = "Off"
                    nvalue = 0
                if count == 1:
                    Domoticz.Log(strName+"Phone found with mac = "+str(item['mac'])+" / Unit = "+str(device_unit)+" / sValue = "+svalue)
                    UpdateDevice(device_unit, nvalue, svalue)
                    #Devices[device_unit].Update(nValue=nvalue, sValue=str(svalue))

   
    def Authenticate(self):
        strName = "Authenticate: "
        Domoticz.Log(strName+"called")
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
        Domoticz.Log(strName+"sendData = "+str(sendData))
        self.unifiConn.Send(sendData)
        
    
    def ProcessDetails(self, response):
        strName = "ProcessDetails: "
        Domoticz.Log(strName+"called")
        if (('rc' in response) and (str(response['rc']) == "ok")):
            Domoticz.Log(strName+"Authenticated succesfull to Unifi Controller")
            hostAuth = True
        else:
            Domoticz.Log(strName+"Authenticated NOT succesfull to Unifi Controller")
            hostAuth = False


    def ProcessCookie(self, httpDict):
        strName = "ProcessCookie: "
        if isinstance(httpDict, dict):
            Domoticz.Log(strName+"Analyzing Data ("+str(len(httpDict))+"):")
            for x in httpDict:
                if isinstance(httpDict[x], dict):
                    if (x == "Headers"):
                        Domoticz.Log(strName+"---> Headers found")
                        for y in httpDict[x]:
                            Domoticz.Log(strName+"------->'" + y + "':'" + str(httpDict[x][y]) + "'")
                            if (y == "Set-Cookie"):
                                Domoticz.Log(strName+"---> Found Cookie")
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
        Domoticz.Log(strName+"File written")

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
