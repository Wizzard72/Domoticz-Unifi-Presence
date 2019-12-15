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
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="True" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import socket
import json

class BasePlugin:
    hostAuth = False
    ANYONE_UNIT = 1
    OVERRIDE_UNIT = 2
    #PHONE_ON_IMG = 'PhoneOn'
    #PHONE_OFF_IMG = 'PhoneOff'
    setCookie = None
    
    #if (self.PHONE_ON_IMG not in Images):
    #    Domoticz.Log('Loading Phone ON images')
    #    Domoticz.Image('Smartphone48_On.zip').Create()
            
    #if (self.PHONE_OFF_IMG not in Images):
    #    Domoticz.Log('Loading Phone OFF images')
    #    Domoticz.Image('Smartphone48_Off.zip').Create()
    
    #for image in Images:
    #    Domoticz.Debug("Icon " + str(Images[image].ID) + " " + Images[image].Name)
    
    #if (self.ANYONE_UNIT not in Devices):
    #        Domoticz.Device(Name=" - Anyone",  Unit=self.ANYONE_UNIT, Type=242, Subtype=1, Image=Images[self.FLAME_OFF_IMG].ID).Create()
    #        UpdateDevice(self.TARGET_TEMP_UNIT, 0, "0.0")
    
    #if (self.ANYONE_UNIT not in Devices):
        #Domoticz.Device(Name="AnyOne", Unit=self.ANYONE_UNIT, TypeName='Selector Switch').Create()
        #UpdateDevice(self.ANYONE_UNIT, 0, "")
    
    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        Domoticz.Debug("onStart called")
        if Parameters["Mode2"] == 'Debug':
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)
        
        Domoticz.Debugging(16 | 64)
        
        self.SetupConnection()
        #Domoticz.Heartbeat(int(Parameters["Mode3"]))
        Domoticz.Heartbeat(10)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")
        Domoticz.Log("onConnect Connection = "+str(Connection))
        Domoticz.Log("onConnect Status = "+str(Status))
        Domoticz.Log("onConnect Description = "+str(Description))
        if (self.hostAuth == False):
            self.Authenticate()
        if (Status == 0):
            Domoticz.Log("onConnect Unifi Controller connected successfully.")
        else:
            Domoticz.Log("onConnect Failed to connect ("+str(Status)+") to: https://"+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")
        Domoticz.Log("onMessage Data = "+str(Data))
        status = int(Data["Status"])
        strHeaders = str(Data['Headers'])
        Domoticz.Log("onMessage strHeaders = "+strHeaders)
        #for strHeader in strHeaders:
            #Domoticz.Log("strHeader = "+strHeader)
            
        #unifiResponseHeaders = strHeaders
        #Domoticz.Log("onMessage unifiResponseHeaders = "+str(unifiResponseHeaders))
        if ('Set-Cookie' in strHeaders):
            #self.setCookie = str(Data['Headers']).split("'")[19]
            #self.setCookie = setCookie.split(";")[0]
            self.setCookie = str(Data['Headers']).split("[")[1]
            self.setCookie = "["+self.setCookie.split("]")[0]+"]"
            Domoticz.Log("onMessage Found Cookie ("+str(self.setCookie)+")")
        
        if (self.unifiConn.Connecting() or self.unifiConn.Connected()):
            Domoticz.Debug("onMessage Unifi Controller connection is alive.")
            
        if (status == 200):            
            strData = Data["Data"].decode("utf-8", "ignore")
            Domoticz.Log('onMessage Unifi Controller response: '+strData)
            unifiResponse = json.loads(strData)
            Domoticz.Log("onMessage unifiResponse = "+str(unifiResponse))
            if (('meta' in unifiResponse)):
                self.hostAuth = True
                Domoticz.Log("onMessage hostAuth = True")
                self.countDown = self.ProcessDetails(unifiResponse['meta'])
                return
            else:
                Domoticz.Log("onMessage Error: HostAuth = False")
        elif status == 302:
            Domoticz.Error("Unifi Controller returned a Page Moved Error.")
        elif status == 400:
            Domoticz.Error("Unifi Controller returned a Bad Request Error.")
        elif (status == 500):
            Domoticz.Error("Unifi Controller returned a Server Error.")
        else:
            Domoticz.Error('Unifi Controller returned status='+Data['Status'])

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("onNotification called")
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        if (self.unifiConn != None) and (self.unifiConn.Connecting()):
            return
        
        if (self.unifiConn == None) or (not self.unifiConn.Connected()):
                Domoticz.Log('onHeartbeat Attempting to reconnect Unifi Controller')
                self.SetupConnection()
        else:
            if self.hostAuth:
                Domoticz.Log('onHeartbeat Requesting Unifi Controller details')
                self.RequestDetails()
            else:
                Domoticz.Log("onHeartbeat Requesting Unifi Controller authorization.")
                Domoticz.Log("onHeartbeat hostAuth = "+str(self.hostAuth))
                #self.Authenticate()

    def SetupConnection(self):
        Domoticz.Log("SetupConnection called")
        self.unifiConn = Domoticz.Connection(Name='UnifiPresenceConn', Transport="TCP/IP", Protocol="HTTPS", Address=Parameters["Address"], Port=Parameters["Port"])
        self.unifiConn.Connect()
        #self.Authenticate()
        
        
    def RequestDetails(self):
        Domoticz.Log("RequestDetails called")
        Domoticz.Log("URL = "+'/api/s/'+Parameters["Mode1"]+'/stat/sta')
        payload = {  }
        sendData = {'Verb' : 'POST',
                    'URL'  : '/api/s/default/stat/sta',
                    'Headers' : { 
                        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", \
                        'Accept-Encoding': 'gzip, deflate, br', \
                        'Accept-Language': 'en-US,en;q=0.5', \
                        'Connection': 'keep-alive', \
                        'Content-Length': '62', \
                        'Content-Type': 'text/plain;charset=UTF-8', \
                        'Upgrade-Insecure-Requests': '1', \
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0', \
                        #'User-Agent': 'Mozilla/5.0', \
                        #'Cookie': self.setCookie, \
                        #'Connection': 'keep-alive', \
                        'Host': Parameters["Address"]+":"+Parameters["Port"]
                    }
                    #'Data' : 'json={}'
                   }
        Domoticz.Log("RequestDetails sendData = "+str(sendData))
        self.unifiConn.Send(sendData)
        
        

        
        
        
        
    def Authenticate(self):
        Domoticz.Log("Authenticate called")
        payload = { "password" : Parameters["Password"] , 
                   "username" : Parameters["Username"]}
        sendData = { 'Verb' : 'POST',
                     'URL'  : '/api/login',
                     'Headers' : { 
                         'User-Agent': 'Mozilla/5.0', \
                         'Connection': 'keep-alive', \
                         'Host': Parameters["Address"]+":"+Parameters["Port"]
                         },
                     'Data' : json.dumps(payload)
                   }
        Domoticz.Log("sendData = "+str(sendData))
        self.unifiConn.Send(sendData)
        
    
    def ProcessDetails(self, response):
        Domoticz.Log("ProcessDetails called")
        if (('rc' in response) and (str(response['rc']) == "ok")):
            Domoticz.Log("Authenticated succesfull to Unifi Controller")
            hostAuth = True
        else:
            Domoticz.Log("Authenticated NOT succesfull to Unifi Controller")
            hostAuth = False
        
      
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

def UpdateDevice(Unit, nValue, sValue, Image=None):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or ((Image != None) and (Image != Devices[Unit].Image)):
            if (Image != None) and (Image != Devices[Unit].Image):
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue), Image=Image)
                Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+") Image="+str(Image))
            else:
                Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
                Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
