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
        <param field="Mode1" label="MAC Phone Addresses" width="600px" required="true" default="1A:2B:3C:4D:5E:6F,7A:8B:9C:AD:BE:CF">
        <param field="Mode3" label="Notifications" width="75px">
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
                
        self.SetupConnection()
        Domoticz.Heartbeat(10)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")
        Domoticz.Log("onConnect Connection = "+str(Connection))
        Domoticz.Log("onConnect Status = "+str(Status))
        Domoticz.Log("onConnect Description = "+str(Description))
        if (Status == 0):
            Domoticz.Log("Unifi Controller connected successfully.")
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: https://"+Parameters["Address"]+":"+Parameter["Port"]+" with error: "+Description)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")
        Domoticz.Debug("onMessage Data = "+str(Data))
        if (self.unifiConn.Connecting() or self.unifiConn.Connected()):
            Domoticz.Debug("Unifi Controller connection is alive.")
            
        if (Status == 200):            
            strData = Data["Data"].decode("utf-8", "ignore")
            Domoticz.Debug('Unifi Controller response: '+strData)
            unifiResponse = json.loads(strData)
        else:
            Domoticz.Error('Unifi Controller returned status='+Data['Status'])

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("onNotification called")
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        if (self.unifiConn != None) and (self.unifiConn.Connecting()):
            return

    def SetupConnection(self):
        Domoticz.Debug("SetupConnection called")
        self.unifiConn = Domoticz.Connection(Name='UnifiPresenceConn', Transport="TCP/IP", Protocol="HTTPS", Address=Parameters["Address"], Port=Parameters["Port"])
        self.unifiConn.Connect()
        self.Authenticate()
        
        
    def RequestDetails(self):
        Domoticz.Log("RequestDetails called")
        sendData = { 'Verb' : 'GET',
                     'URL'  : '/api/s/default/stat/sta',
                     'Headers' : { 'User-Agent': "Mozilla/5.0",
                                   'Content-Type': 'application/json; UTF-8', \
                                   'Connection': 'keep-alive', \
                                   'Accept': '*/*', \
                                   'Accept-Charset': 'UTF-8', \
                                   'Host': Parameters["Address"]+":"+Parameters["Port"] }
                   }
        self.unifiConn.Send(sendData)
        
    def Authenticate(self):
        Domoticz.Log("Authenticate called")
        payload = { "password" : +Parameters["Password"]+' , "username" : '+Parameters["Username"]}
        sendData = { 'Verb' : 'POST',
                     'Headers' : { 'User-Agent': "Mozilla/5.0",
                                   'Content-Type': 'application/json; UTF-8', \
                                   'Host': 'https://'+Parameters["Address"]+":"+Parameters["Port"]+'/api/login' },
                     'Data' : json.dumps(payload)
                   }
        Domoticz.Log("sendData = "+str(sendData))
        self.unifiConn.Send(sendData)
        
      
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
