# Unifi-Presence plugin
#
# Author: Wizzard72
# Versions:
#   1.0.0: First release
#   2.0.0: Second release
#   3.0.0: Third release: complete rewrite of requesting details and creating devices. Delete alle devices and delete the 'devicetable.txt file within de plugin folder.
#   3.0.2: Bug resolved
#   3.0.4: Bug when using Domoticz container
"""
<plugin key="UnifiPresence" name="Unifi Presence" author="Wizzard72" version="3.0.4" wikilink="https://github.com/Wizzard72/Domoticz-Unifi-Presence">
    <description>
        <h2>Unifi Presence Detection plugin</h2><br/>
        This plugin reads the Unifi Controller information such as the sensors on the Unifi Gateway.
        Beside this it checks the presence of phone(s) and it is possible to add extra devices for example Geo Fencing.
    </description>
    <params>
        <param field="Address" label="IP Address / DNS name of the Unifi Controller" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="30px" required="true" default="8443"/>
        <param field="Username" label="Username" width="200px" required="true" default="admin@unifi.com"/>
        <param field="Password" label="Password" width="600px" required="true" default="password" password="true"/>
        <param field="Mode1" label="Site Name" width="200px" required="true" default="default"/>
        <param field="Mode2" label="MAC Phone Addresses" width="600px" required="true" default="Phone1=1A:2B:3C:4D:5E:6F,Phone2=7A:8B:9C:AD:BE:CF"/>
        <param field="Mode3" label="Enable Geofencing devices" width="75px">
            <options>
                <option label="Yes" value="Yes"/>
                <option label="No" value="No"  default="true" />
            </options>
        </param>
        <param field="Mode4" label="Select Unifi Controller" width="150px">
            <options>
                <option label="Unifi Controller" value="unificontroller" default="true" />
                <option label="Dream Machine Pro/CloudKey-Gen2" value="dreammachinepro"/>
            </options>
        </param>
        <param field="Mode5" label="Posibility to block devices from the network?" width="75px">
            <options>
                <option label="Yes" value="Yes"/>
                <option label="No" value="No"  default="true" />
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
import urllib
import time
import os
from requests import Session
from typing import Pattern, Dict, Union
from datetime import datetime
# https://ubntwiki.com/products/software/unifi-controller/api


class BasePlugin:
    _Off_Delay = 60
    _plugin_name = False
    _device_table = False
    _unifiConn = False
    override_time = 0
    hostAuth = False
    UNIFI_ANYONE_HOME_UNIT = 1
    UNIFI_OFF_DELAY = 2
    UNIFI_OVERRIDE_UNIT = 255
    _Cookies = None
    _csrftoken = None
    cookie = None
    cookieAvailable = False
    phone_name = ""
    Matrix = ""
    count_g_device = 0
    _devices_found = {}
    _login_data = {}
    _current_status_code = None
    versionCheck = None
    _block_data = {}
    _block_data['cmd'] = None
    _block_data['mac'] = None
    _login_data['username'] = None
    _login_data['password'] = None
    _site = None
    _verify_ssl = False
    _baseurl = None
    _session = requests.Session()
    _uapDevices = []
    _total_phones_active_before = 0
    _lastloginfailed = False
    u_name_total_found = ""
    u_name_total = ""
    devUnit_found = 0
    UnifiDevicesNames = {
        #Device Code, Device Type, Device Name
        "BZ2":       ("uap",       "UniFi AP"),
        "BZ2LR":     ("uap",       "UniFi AP-LR"),
        "U2HSR":     ("uap",       "UniFi AP-Outdoor+"),
        "U2IW":      ("uap",       "UniFi AP-In Wall"),
        "U2L48":     ("uap",       "UniFi AP-LR"),
        "U2Lv2":     ("uap",       "UniFi AP-LR v2"),
        "U2M":       ("uap",       "UniFi AP-Mini"),
        "U2O":       ("uap",       "UniFi AP-Outdoor"),
        "U2S48":     ("uap",       "UniFi AP"),
        "U2Sv2":     ("uap",       "UniFi AP v2"),
        "U5O":       ("uap",       "UniFi AP-Outdoor 5G"),
        "U7E":       ("uap",       "UniFi AP-AC"),
        "U7EDU":     ("uap",       "UniFi AP-AC-EDU"),
        "U7Ev2":     ("uap",       "UniFi AP-AC v2"),
        "U7HD":      ("uap",       "UniFi AP-HD"),
        "U7SHD":     ("uap",       "UniFi AP-SHD"),
        "U7NHD":     ("uap",       "UniFi AP-nanoHD"),
        "UAL6":      ("uap",       "UniFi AP-U6-Lite"),
        "UAP6MP":    ("uap",       "UniFi WiFi 6 Pro"),
        "UFLHD":     ("uap",       "UniFi AP-Flex-HD"),
        "UHDIW":     ("uap",       "UniFi AP-HD-In Wall"),
        "UCXG":      ("uap",       "UniFi AP-XG"),
        "UXSDM":     ("uap",       "UniFi AP-BaseStationXG"),
        "UCMSH":     ("uap",       "UniFi AP-MeshXG"),
        "U7IW":      ("uap",       "UniFi AP-AC-In Wall"),
        "U7IWP":     ("uap",       "UniFi AP-AC-In Wall Pro"),
        "U7MP":      ("uap",       "UniFi AP-AC-Mesh-Pro"),
        "U7LR":      ("uap",       "UniFi AP-AC-LR"),
        "U7LT":      ("uap",       "UniFi AP-AC-Lite"),
        "U7O":       ("uap",       "UniFi AP-AC Outdoor"),
        "U7P":       ("uap",       "UniFi AP-Pro"),
        "U7MSH":     ("uap",       "UniFi AP-AC-Mesh"),
        "U7PG2":     ("uap",       "UniFi AP-AC-Pro"),
        "p2N":       ("uap",       "PicoStation M2"),
        "US48PRO":   ("usw",       "UniFi Switch Pro 48"),
        "US8":       ("usw",       "UniFi Switch 8"),
        "US8P60":    ("usw",       "UniFi Switch 8 POE-60W"),
        "US8P150":   ("usw",       "UniFi Switch 8 POE-150W"),
        "S28150":    ("usw",       "UniFi Switch 8 AT-150W"),
        "USC8":      ("usw",       "UniFi Switch 8"),
        "USL8LP":    ("usw",       "Unifi Switch Lite 8 PoE"),
        "US16P150":  ("usw",       "UniFi Switch 16 POE-150W"),
        "USL16P":    ("usw",       "UniFi Switch 16 150W"),
        "S216150":   ("usw",       "UniFi Switch 16 AT-150W"),
        "US24":      ("usw",       "UniFi Switch 24"),
        "US24P250":  ("usw",       "UniFi Switch 24 POE-250W"),
        "US24PL2":   ("usw",       "UniFi Switch 24 L2 POE"),
        "US24P500":  ("usw",       "UniFi Switch 24 POE-500W"),
        "S224250":   ("usw",       "UniFi Switch 24 AT-250W"),
        "S224500":   ("usw",       "UniFi Switch 24 AT-500W"),
        "USL24P":    ("usw",       "UniFi Switch 24 PoE"),
        "US48":      ("usw",       "UniFi Switch 48"),
        "US48P500":  ("usw",       "UniFi Switch 48 POE-500W"),
        "US48PL2":   ("usw",       "UniFi Switch 48 L2 POE"),
        "US48P750":  ("usw",       "UniFi Switch 48 POE-750W"),
        "S248500":   ("usw",       "UniFi Switch 48 AT-500W"),
        "S248750":   ("usw",       "UniFi Switch 48 AT-750W"),
        "US6XG150":  ("usw",       "UniFi Switch 6XG POE-150W"),
        "USXG":      ("usw",       "UniFi Switch 16XG"),
        "USMINI":    ("usw",       "Unifi Switch Flex Mini"),
        "UGW3":      ("ugw",       "UniFi Security Gateway 3P"),
        "UGW4":      ("ugw",       "UniFi Security Gateway 4P"),
        "UGWHD4":    ("ugw",       "UniFi Security Gateway HD"),
        "UGWXG":     ("ugw",       "UniFi Security Gateway XG-8"),
        "UP4":       ("uph",       "UniFi Phone-X"),
        "UP5":       ("uph",       "UniFi Phone"),
        "UP5t":      ("uph",       "UniFi Phone-Pro"),
        "UP7":       ("uph",       "UniFi Phone-Executive"),
        "UP5c":      ("uph",       "UniFi Phone"),
        "UP5tc":     ("uph",       "UniFi Phone-Pro"),
        "UP7c":      ("uph",       "UniFi Phone-Executive"),
        "UDMPRO":    ("udm",       "Unifi Dream Machine Pro"),
        "UDM":       ("udm",       "Unifi Dream Machine")
        }
    uap = []
    usw = []
    ugw = []
    uph = []
    udm = []

    def __init__(self):
        return

    def onStart(self):
        strName = "onStart: "
        Domoticz.Debug(strName+"called")

        #self._login_data['username'] = Parameters["Username"]
        #self._login_data['password'] = Parameters["Password"]
        #self._login_data['remember'] = True
        #self._site = Parameters["Mode1"]
        #self._verify_ssl = False
        #self._baseurl = 'https://'+Parameters["Address"]+':'+Parameters["Port"]
        #self._session = Session()

        if (Parameters["Mode6"] != "0"):
            Domoticz.Debugging(int(Parameters["Mode6"]))
        else:
            Domoticz.Debugging(0)

        # check if version of domoticz is 2020.2 or higher
        try:
            if int(Parameters["DomoticzVersion"].split('.')[0]) < 2020:  # check domoticz major version
                Domoticz.Error(
                    "Domoticz version required by this plugin is 2020.2 (you are running version {}).".format(
                        Parameters["DomoticzVersion"]))
                Domoticz.Error("Plugin is therefore disabled")
                self.setVersionCheck(False, "onStart")
            else:
                self.setVersionCheck(True, "onStart")
        except Exception as err:
            Domoticz.Error("Domoticz version check returned an error: {}. Plugin is therefore disabled".format(err))
            self.setVersionCheck(False, "onStart")
        if not self.versionCheck:
            return

        # Create file
        try:
           f = open(Parameters["HomeFolder"] + "devicetable.txt")
           Domoticz.Log(strName+"Found devicestable.txt file")
        except:
           Domoticz.Log(strName+"Didn't found devicestable.txt file, creating file")
           f = open(Parameters["HomeFolder"] + "devicetable.txt", "w+")

        # load custom images
        if "UnifiPresenceAnyone" not in Images:
            Domoticz.Log(strName+"Add UnifiPresenceAnyone icons to Domoticz")
            Domoticz.Image("uanyone.zip").Create()

        if "UnifiPresenceOverride" not in Images:
            Domoticz.Log(strName+"Add UnifiPresenceOverride icons to Domoticz")
            Domoticz.Image("uoverride.zip").Create()

        if "UnifiPresenceDevice" not in Images:
            Domoticz.Log(strName+"Add UnifiPresenceDevice icons to Domoticz")
            Domoticz.Image("udevice.zip").Create()

        Domoticz.Log("Number of icons loaded = " + str(len(Images)))
        for item in Images:
            Domoticz.Log(strName+"Items = "+str(item))
            Domoticz.Log(strName+"Icon " + str(Images[item].ID) + " Name = " + Images[item].Name)

        # create devices
        self.login()
        if self._current_status_code == 200:
            self.detectUnifiDevices()
            self.create_devices()

            # Create table
            #               0           1         2           3        4              5            6       7
            #           Phone_Name | MAC_ID | Unit_Number | State | Last Online | Check Online | Status | Time
            #             Test      1:1:1:1     50           Off      No             No          Online
            #             Test                  50           Off      No             Yes         Way
            #             Test                  50           On       Yes            Yes         Offline
            #             Test                  50           On       Yes            No          None
            #             Test                  50           Off      No             No
            # Step 1      User A    1:1:1:1     110          Off      No             No          Offline
            # Step 2      User A    1:1:1:1     110          Off      No             No          Offline

            # Step 1      User A    1:1:1:1     110          Off      No             Yes         Offline
            # Step 2      User A    1:1:1:1     110          On       Yes            No          Online

            # Step 1      User A    1:1:1:1     110          Off      Yes            Yes         Offline
            # Step 2      User A    1:1:1:1     110          On       Yes            No          Online

            # Step 1      User A    1:1:1:1     110          On       Yes            No          Online
            # Step 2      User A    1:1:1:1     110          Off      No             No          Wait     11:30
            # Step 3      User A    1:1:1:1     110          Off      No             No          Offline

            # Step 1      User A    1:1:1:1     110          On       Yes            Yes         Online
            # Step 2      User A    1:1:1:1     110          On       Yes            No          Online
            device_mac=Parameters["Mode2"].split(",")
            w, h = 8, self.total_devices_count;
            self.Matrix = [[0 for x in range(w)] for y in range(h)]

            count = 1
            found_user = None
            self.Matrix[0][0] = "OverRide"            # Used for the OverRide Selector Switch
            self.Matrix[0][1] = "00:00:00:00:00:00"   # Used for the OverRide Selector Switch
            self.Matrix[0][2] = 255                   # Used for the OverRide Selector Switch
            self.Matrix[0][3] = "Off"                 # Used for the OverRide Selector Switch
            self.Matrix[0][4] = "No"                  # Used for the OverRide Selector Switch
            self.Matrix[0][5] = "No"                  # Used for the OverRide Selector Switch
            self.Matrix[0][6] = "None"                  # Used for the OverRide Selector Switch
            for device in device_mac:
                device = device.strip()
                Device_Name, Device_Mac = device.split("=")
                self.Matrix[count][0] = Device_Name
                self.Matrix[count][1] = Device_Mac.lower()
                Device_Unit = None
                self.Matrix[count][3] = "Off"
                self.Matrix[count][4] = "No"
                self.Matrix[count][5] = "No"
                self.Matrix[count][6] = "None"
                found_user = Device_Name
                for dv in Devices:
                    # Find the unit number
                    search_phone = Devices[dv].Name
                    position = len(self._plugin_name)+3
                    if Devices[dv].Name[position:] == found_user:
                        self.Matrix[count][2] = Devices[dv].Unit
                        count = count + 1
                        #continue
                if Parameters["Mode3"] == "Yes":
                    self.Matrix[count][0] = "Geo "+Device_Name
                    self.Matrix[count][1] = "11:11:11:11:11:11"
                    Device_Unit = None
                    self.Matrix[count][3] = "Off"
                    self.Matrix[count][4] = "No"
                    self.Matrix[count][5] = "GEO"
                    self.Matrix[count][6] = "None"
                    found_user = "Geo "+Device_Name
                    for dv in Devices:
                        # Find the unit number
                        devName = Devices[dv].Name
                        position = len(self._plugin_name)+3
                        if Devices[dv].Name[position:] == found_user:
                            self.Matrix[count][2] = Devices[dv].Unit
                            self.Matrix[count][3] = Devices[dv].sValue
                            self.Matrix[count][5] = "GEO"
                            Domoticz.Log(strName+"Geo Phone with name '"+found_user+"' is detected from config.")
                            count = count + 1
                            #continue

            # report the phone and geofencing devices
            x = range(0, self.total_devices_count, 1)
            for n in x:
                Domoticz.Log(strName+"Phone Naam = "+str(self.Matrix[n][0])+" | "+str(self.Matrix[n][1])+" | "+str(self.Matrix[n][2])+" | "+str(self.Matrix[n][3])+" | "+str(self.Matrix[n][4])+" | "+str(self.Matrix[n][5]))

            #self.devicesPerAP()

        if Devices[self.UNIFI_OFF_DELAY].nValue == 0:
            self._Off_Delay = 0
        else:
            self._Off_Delay = Devices[self.UNIFI_OFF_DELAY].nValue + 20
        Domoticz.Heartbeat(5)

    def onStop(self):
        strName = "onStop: "
        Domoticz.Debug(strName+"Pluggin is stopping.")
        self.logout()

    def onConnect(self, Connection, Status, Description):
        strName = "onConnect: "
        Domoticz.Debug(strName+"called")
        Domoticz.Debug(strName+"Connection = "+str(Connection))
        Domoticz.Debug(strName+"Status = "+str(Status))
        Domoticz.Debug(strName+"Description = "+str(Description))

    def onMessage(self, Connection, Data):
        strName = "onMessage: "
        Domoticz.Debug(strName+"called")
        DumpHTTPResponseToLog(Data)
        Domoticz.Debug(strName+"Data = " +str(Data))
        strData = Data["Data"].decode("utf-8", "ignore")
        status = int(Data["Status"])

        if (self._current_status_code == 200 or self._current_status_code == 404):
            unifiResponse = json.loads(strData)
            Domoticz.Debug(strName+"Retrieved following json: "+json.dumps(unifiResponse))
            self.onHeartbeat()

    def onCommand(self, Unit, Command, Level, Hue):
        strName = "onCommand: "
        Domoticz.Log(strName+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if self.versionCheck is True:
            if self._current_status_code == 200 or self._current_status_code == 404:
                if self.UNIFI_OVERRIDE_UNIT == Unit:
                    if Level == 0: # Override Off
                        self.override_time = 0 #seconds
                        Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, int(Level), str(Level))
                        self.Matrix[0][3] = "Off"
                        self.Matrix[0][5] = "No"
                    elif Level == 10: # Override 1 hour
                        self.override_time = 60 * 60 #seconds
                        Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, int(Level), str(Level))
                        self.Matrix[0][3] = "On"
                        self.Matrix[0][5] = "OverRide"
                    elif Level == 20: # Override 2 hours
                        self.override_time = 2 * 60 * 60 #seconds
                        Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, int(Level), str(Level))
                        self.Matrix[0][3] = "On"
                        self.Matrix[0][5] = "OverRide"
                    elif Level == 30: # Override 3 hour
                        self.override_time = 3 * 60 * 60 #seconds
                        Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, int(Level), str(Level))
                        self.Matrix[0][3] = "On"
                        self.Matrix[0][5] = "OverRide"
                    elif Level == 40: # Override On
                        self.override_time = 99999999999 #seconds
                        Domoticz.Log(strName+"Override Time = "+str(self.override_time))
                        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, int(Level), str(Level))
                        self.Matrix[0][3] = "On"
                        self.Matrix[0][5] = "OverRide"
                if self.UNIFI_OFF_DELAY == Unit:
                    self._Off_Delay = Level + 20 #seconds
                    Domoticz.Debug(strName+"Off Delay = "+str(self._Off_Delay))
                    UpdateDevice(self.UNIFI_OFF_DELAY, Level, str(Level))


                t = self.total_devices_count - self.count_g_device
                for r in range(self.total_devices_count):
                    Domoticz.Debug(strName+"r = "+str(r)+" / self.Matrix[r][2] = "+str(self.Matrix[r][2])+" / Unit = "+str(Unit))
                    if self.Matrix[0][2] != Unit:
                        if self.Matrix[r][2] == Unit:
                            Domoticz.Debug(strName+"Unit = "+str(Unit))
                            if self.Matrix[r][5] == "Yes" or self.Matrix[r][5] == "No":
                                if Parameters["Mode5"] == "Yes":
                                    if Level == 10: # 10 = BLOCK
                                        svalue = str(Level)
                                        nvalue = int(Level)
                                        UpdateDevice(self.Matrix[r][2], nvalue, svalue)
                                        self.Matrix[r][3] = "Off"
                                        self.Matrix[r][4] = "No"
                                        self.Matrix[r][5] = "No"
                                        self.block_phone(self.Matrix[r][0], self.Matrix[r][1])
                                    elif Level == 20: # 20 = UNBLOCK
                                        svalue = str(Level)
                                        nvalue = int(Level)
                                        UpdateDevice(Unit, nvalue, svalue)
                                        self.Matrix[r][3] = "Off"
                                        self.Matrix[r][4] = "Yes"
                                        self.Matrix[r][5] = "No"
                                        self.unblock_phone(self.Matrix[r][0], self.Matrix[r][1], Unit)
                            if self.Matrix[r][5] == "GEO":
                                if str(Command) == "On":
                                    UpdateDevice(Unit, 1, str(Command))
                                    self.Matrix[r][3] = str(Command)
                                elif str(Command) == "Off":
                                    UpdateDevice(Unit, 0, str(Command))
                                    self.Matrix[r][3] = str(Command)


                for x in range(self.total_devices_count):
                    Domoticz.Debug(strName+" "+str(x)+" Phone Naam = "+self.Matrix[x][0]+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+self.Matrix[x][3]+" | "+self.Matrix[x][4]+" | "+self.Matrix[x][5])

            self.onHeartbeat()


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
        if self.versionCheck is True:
            if Devices[self.UNIFI_OFF_DELAY].nValue == 0:
                self._Off_Delay = 0
            else:
                self._Off_Delay = Devices[self.UNIFI_OFF_DELAY].nValue + 20
            if (self._current_status_code == None) or (self._current_status_code == 401) or (self._current_status_code == 404) or (self._current_status_code != 200):
                Domoticz.Log(strName+'Attempting to reconnect Unifi Controller')
                self.login()

            if self._current_status_code == 200 or self._current_status_code == 404:
                if self.Matrix[0][3] == "On":
                    try:
                        timeDiff = datetime.now() - datetime.strptime(Devices[255].LastUpdate,'%Y-%m-%d %H:%M:%S')
                    except TypeError:
                        timeDiff = datetime.now() - datetime(*(time.strptime(Devices[255].LastUpdate,'%Y-%m-%d %H:%M:%S')[0:6]))
                    timeDiffSeconds = timeDiff.seconds
                    Domoticz.Log(strName+"OverRide is on for: "+str(timeDiffSeconds)+"/"+str(self.override_time)+" seconds")
                    if timeDiffSeconds >= self.override_time:
                        self.Matrix[0][3] = "Off"
                        self.Matrix[0][4] = "Yes"

            if self._current_status_code == 200:
                Domoticz.Debug(strName+'Requesting Unifi Controller details')
                self.request_details()
                if self._current_status_code == 200:
                    self.request_online_phones()


    def getCookies(cookie_jar, domain):
        cookie_dict = cookie_jar.get_dict(domain=domain)
        found = ['%s=%s' % (name, value) for (name, value) in cookie_dict.items()]
        return ';'.join(found)

    def login(self):
        strName = "login: "
        Domoticz.Debug(strName+"called")
        """
        Log the user in
        :return: None
        api url for dreammachine pro: /api/auth/login
        api url for other: /api/login
        """
        self._login_data['username'] = Parameters["Username"]
        self._login_data['password'] = Parameters["Password"]
        self._login_data['remember'] = True
        self._site = Parameters["Mode1"]
        self._verify_ssl = False
        self._baseurl = "https://"+Parameters["Address"]+":"+Parameters["Port"]
        self._session = Session()
        try:
            if Parameters["Mode4"] == "unificontroller":
                self._session.headers.update({'Content-Type' : 'application/json'})
                self._session.headers.update({'Connection' : 'keep-alive'})
                r = self._session.post("{}/api/login".format(self._baseurl), data=json.dumps(self._login_data), verify=self._verify_ssl, timeout=4000)
                controller = "Unifi Controller"
            elif Parameters["Mode4"] == "dreammachinepro":
                self._session.headers.update({'Content-Type' : 'application/json'})
                self._session.headers.update({'Connection' : 'keep-alive'})
                r = self._session.post("{}/api/auth/login".format(self._baseurl), data=json.dumps(self._login_data), verify=self._verify_ssl, timeout=4000)
                if 'X-CSRF-Token' in r.headers:
                    self._session.headers.update({'X-CSRF-Token': r.headers['X-CSRF-Token']})
                    Domoticz.Log(strName+"X-SCRF-Token found and added to header")
                controller = "Dream Machine Pro"
            else:
                Domoticz.Error(strName+"Check configuration!!")

            self._current_status_code = r.status_code
            if self._current_status_code == 200:
                Domoticz.Log(strName+"Login successful into "+controller)
                self._Cookies = r.cookies
                self._lastloginfailed = False
            elif self._current_status_code == 400:
                Domoticz.Error(strName+"Failed to log in to api ("+controller+") with provided credentials ("+str(self._current_status_code)+")")
            #elif self._current_status_code == 404:
            #    Domoticz.Error(strName+" "+controller+" Not Found ("+str(self._current_status_code)+")")
            #    self.logout()
            else:
                if self._lastloginfailed:
                    Domoticz.Error(strName+"Failed to login to the "+controller+" with errorcode "+str(self._current_status_code))
                    self._current_status_code = 999
                else:
                    Domoticz.Log(strName+"First attempt failed to login to the "+controller+"(URL="+self._baseurl+") with errorcode "+str(self._current_status_code))
                    self._lastloginfailed = True
                    self._current_status_code = 999
        except:
            Domoticz.Error("Login failed")

    def logout(self):
        strName = "logout: "
        """
        Log the user out
        :return: None
        """
        try:
            if self._current_status_code == 200:
                if Parameters["Mode4"] == "unificontroller":
                    self._session.post("{}/logout".format(self._baseurl, verify=self._verify_ssl))
                elif Parameters["Mode4"] == "dreammachinepro":
                    #self._session.post("{}/proxy/network/logout".format(self._baseurl, verify=self._verify_ssl))
                    self._session.post("{}/api/auth".format(self._baseurl, verify=self._verify_ssl))
                else:
                    Domoticz.Error("Check configuration!!")
                Domoticz.Log(strName+"Logout of the Unifi API")
                self._session.close()
                self._current_status_code = 999
                self._timeout_timer = None
        except:
            Domoticz.Error("Logout failure")



    def get_attribute(data, attribute, default_value):
        return data.get(attribute) or default_value

    def request_details(self):
        strName = "request_details: "
        oke = 0
        try:
            if Parameters["Mode4"] == "unificontroller":
                try:
                    r = self._session.get("{}/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), cookies=self._Cookies)
                except:
                    Domoticz.Error("Problem retrieving data. Trying to login...")
                    self._lastloginfailed = True
                    oke = 1
            elif Parameters["Mode4"] == "dreammachinepro":
                r = self._session.get("{}/proxy/network/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), cookies=self._Cookies)
            else:
                Domoticz.Error("Check configuration!!")
        
            if oke == 0:
                self._current_status_code = r.status_code
            else:
                self._current_status_code = 9999


            #Name      type,  jsonfield,     jsonfield
            jsonFields = {
            "01 CPU":           ("usw","Percentage","Custom","system-stats","cpu"),
            "02 Memory":        ("usw","Percentage","Custom","system-stats","mem"),
            "03 CPU Usage":     ("ugw","Percentage","Custom","system-stats","cpu"),
            "04 Memory":        ("ugw","Percentage","Custom","system-stats","mem"),
            "05 Board (CPU)":   ("ugw","Temperature","Custom","system-stats","temps","Board (CPU)"),
            "06 Board (PHY)":   ("ugw","Temperature","Custom","system-stats","temps","Board (PHY)"),
            "07 CPU Temp":      ("ugw","Temperature","Custom","system-stats","temps","CPU"),
            "08 PHY":           ("ugw","Temperature","Custom","system-stats","temps","PHY"),
            "09 Latency":       ("ugw","31","1;ms","speedtest-status","latency"),
            "10 XPut Download": ("ugw","31","1;Mbps","speedtest-status","xput_download"),
            "11 XPut Upload":   ("ugw","31","1;Mbps","speedtest-status","xput_upload"),
            "12 CPU":           ("uap","Percentage","Custom","system-stats","cpu"),
            "13 Memory":        ("uap","Percentage","Custom","system-stats","mem"),
            "14 CPU":           ("udm","Temperature","Custom","temperatures","0","value"),
            "15 Local":         ("udm","Temperature","Custom","temperatures","1","value"),
            "16 PHY":           ("udm","Temperature","Custom","temperatures","2","value"),
            "17 CPU Usage":     ("udm","Percentage","Custom","system-stats","cpu"),
            "18 Memory":        ("udm","Percentage","Custom","system-stats","mem"),
            "19 Latency":       ("udm","31","{1;ms}","speedtest-status","latency"),
            "20 XPut Download": ("udm","31","{1;Mbps}","speedtest-status","xput_download"),
            "21 XPut Upload":   ("udm","31","{1;Mbps}","speedtest-status","xput_upload")
            }


            if self._current_status_code == 200 and oke == 0:
                data = r.json()['data']
                for j_name, j_json  in jsonFields.items():
                    for item in data:
                        if item['type'] == j_json[0]:
                            device_found = 0
                            u_name_total_found = ""
                            self.u_name_total = ""
                            if 'name' not in item:
                                u_name = item['model']
                            elif 'name' in item:
                                u_name = item['name']
                            self.u_name_total = u_name + " " + j_name[3:]
                            if self.is_non_zero_file(Parameters["HomeFolder"] + "devicetable.txt"):
                                for devicetable in self._device_table:
                                    devUnit, devName = devicetable.split(",")
                                    devName = devName.strip()
                                    devUnit = int(devUnit)
                                    device_found = 0
                                    found_devUnit = 0
                                    if devName == self.u_name_total:
                                        #Found device
                                        device_found = 1
                                        found_u_name_total = self.u_name_total
                                        found_devUnit = devUnit
                                        break
                            else:
                                devName = ""
                                devUnit = 0
                            try:
                                if len(j_json) == 4:
                                    #future use
                                    value = item["" +j_json[3]+ ""]
                                elif len(j_json) == 5:
                                    value = item["" +j_json[3]+ ""]["" +j_json[4]+ ""]
                                    if isinstance(value, float):
                                        value = round(value, 2)
                                    if device_found == 1:
                                        UpdateDevice(devUnit, int(float(value)), str(value))
                                    elif value != "" and device_found == 0:
                                        #create device
                                        self.create_device(j_json[0], self.u_name_total, j_json[1], j_json[2])
                                        UpdateDevice(self.devUnit_found, int(float(value)), str(value))
                                elif len(j_json) == 6:
                                    value = item["" +j_json[3]+ ""]
                                    if j_json[0] == "udm":
                                        for p in value:
                                            if p['name'].lower() == j_name[3:].lower():
                                                value = p['value']
                                                if isinstance(value, float):
                                                    value = round(value, 2)
                                                if device_found == 1:
                                                    UpdateDevice(devUnit, int(float(value)), str(value))
                                                elif device_found == 0:
                                                    #create device
                                                    self.create_device(j_json[0], self.u_name_total, j_json[1], j_json[2])
                                                    UpdateDevice(self.devUnit_found, int(float(value)), str(value))
                                    elif j_json == "ugw":
                                        Domoticz.Error("Send the API output: '/api/s/default/stat/device' (Unifi Controller) or '/proxy/network/api/s/{}/stat/device' (Dreammachine)")
                            except:
                                pass
        except requests.ReadTimeout:
            Domoticz.Error("Request to " +Parameters["Mode4"]+" timed out.")


    def is_non_zero_file(self, fpath):  
        return os.path.isfile(fpath) and os.path.getsize(fpath) > 0


    def create_device(self, un_type, un_name, un_typename, un_custom="None"):
        strName = "create_device: "

        new_unit = 0
        if un_type == "uap":
            new_unit = find_available_unit_uap()
        elif un_type == "usw":
            new_unit = find_available_unit_usw()
        elif un_type == "ugw":
            new_unit = find_available_unit_ugw()
        elif un_type == "udm":
            new_unit = find_available_unit_udm()

        if un_typename != "31":
            Domoticz.Log("Create device: " +un_name+" (type="+un_typename+")")
            Domoticz.Device(Name=un_name, Unit=new_unit, Used=1, TypeName=un_typename).Create()
        else:
            Domoticz.Log("Create device: " +un_name+" (type="+un_typename+" | Options="+un_custom+")")
            Domoticz.Device(Name=un_name, Unit=new_unit, Used=1, Type=243, Subtype=int(un_typename), Options=un_custom).Create()
        UpdateDevice(new_unit, 0, "0")
        self.create_devicetable(new_unit, un_name)
        #reload the devicetable.txt file
        f = open(Parameters["HomeFolder"] + "devicetable.txt")
        self._device_table = f.readlines()

    def request_online_phones(self):
        strName = "request_online_phones: "
        try:
            if Parameters["Mode4"] == "unificontroller":
                r = self._session.get("{}/api/s/{}/stat/sta".format(self._baseurl, self._site, verify=self._verify_ssl), cookies=self._Cookies)
            elif Parameters["Mode4"] == "dreammachinepro":
                r = self._session.get("{}/proxy/network/api/s/{}/stat/sta".format(self._baseurl, self._site, verify=self._verify_ssl), cookies=self._Cookies)
            else:
                Domoticz.Error("Check configuration!!")
            self._current_status_code = r.status_code
            if self._current_status_code == 200:
                data = r.json()['data']
                for item in data:
                    Domoticz.Debug(strName+"Json Data (device) = " + str(item))
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
                                    self.Matrix[x][5] = "Yes"
                self.ProcessDevices()
            elif self._current_status_code == 401:
                Domoticz.Log(strName+"Invalid login, or login has expired")
                self.login()
            elif self._current_status_code == 404:
                Domoticz.Log(strName+"Invalid login, or login has expired")
                self.login()
        except requests.ReadTimeout:
            Domoticz.Error("Request to " +Parameters["Mode4"]+" timed out.")


    def block_phone(self, phone_name, mac):
        strName = "block_phone: "
        self._block_data['cmd'] ='block-sta'
        self._block_data['mac'] = mac
        if Parameters["Mode4"] == "unificontroller":
            r = self._session.post("{}/api/s/{}/cmd/stamgr".format(self._baseurl, self._site, verify=self._verify_ssl), data=json.dumps(self._block_data), verify=self._verify_ssl).status_code
        elif Parameters["Mode4"] == "dreammachinepro":
            r = self._session.post("{}/proxy/network/api/s/{}/cmd/stamgr".format(self._baseurl, self._site, verify=self._verify_ssl), data=json.dumps(self._block_data), verify=self._verify_ssl).status_code
        else:
            Domoticz.Error("Check configuration!!")

        if r == 200:
            Domoticz.Log(strName+"Blocked '" + phone_name + "' with mac address " + mac)
        elif r == 401:
            Domoticz.Log(strName+"Invalid login, or login has expired")
            self.login()
        elif r == 404:
            Domoticz.Log(strName+"Invalid login, or login has expired")
            self.login()


    def unblock_phone(self, phone_name, mac, unit):
        strName = "unblock_phone: "
        self._block_data['cmd'] ='unblock-sta'
        self._block_data['mac'] = mac
        if Parameters["Mode4"] == "unificontroller":
            r = self._session.post("{}/api/s/{}/cmd/stamgr".format(self._baseurl, self._site, verify=self._verify_ssl), data=json.dumps(self._block_data), verify=self._verify_ssl).status_code
        elif Parameters["Mode4"] == "dreammachinepro":
            r = self._session.post("{}/proxy/network/api/s/{}/cmd/stamgr".format(self._baseurl, self._site, verify=self._verify_ssl), data=json.dumps(self._block_data), verify=self._verify_ssl).status_code
        else:
            Domoticz.Error("Check configuration!!")

        if  r == 200:
            UpdateDevice(unit, 0, "Off")
            Domoticz.Log(strName+"Unblocked '" + phone_name + "' with mac address " + mac)
        elif r == 401:
            Domoticz.Log(strName+"Invalid login, or login has expired")
            self.login()
        elif r == 404:
            Domoticz.Log(strName+"Invalid login, or login has expired")
            self.login()


    def ProcessDevices(self):
        strName = "ProcessDevices: "
        if Parameters["Mode5"] == "No":
            svalueOn = "On"
            nvalueOn = 1
            svalueOff = "Off"
            nvalueOff = 0
        else:
            svalueOn = "30" # 30 = ON
            nvalueOn = 30
            svalueOff = "0"
            nvalueOff = 0  # 0 = OFF
        for x in range(self.total_devices_count):
            #Domoticz.Log(self.Matrix[x][0] + " - " + str(self.Matrix[x][1]) + " - " + str(self.Matrix[x][2]) + " - " + self.Matrix[x][3] + " - " + self.Matrix[x][4] + " - " + self.Matrix[x][5] + " - " + self.Matrix[x][6] + " - " +str(self.Matrix[x][7]))
            if self.Matrix[x][3] == "Off" and self.Matrix[x][4] == "No" and self.Matrix[x][5] == "No":
                self.Matrix[x][3] = "Off"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
                self.Matrix[x][6] = "Offline"
                self.Matrix[x][7] = ""
                if Devices[self.Matrix[x][2]].nValue != 0:
                    UpdateDevice(self.Matrix[x][2], nvalueOff, svalueOff)
            elif self.Matrix[x][3] == "Off" and self.Matrix[x][4] == "No" and self.Matrix[x][5] == "Yes":
                Domoticz.Log(strName+"Phone '"+self.Matrix[x][0]+"' connected to the Unifi Controller")
                self.Matrix[x][3] = "On"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
                self.Matrix[x][6] = "Online"
                self.Matrix[x][7] = ""
                UpdateDevice(self.Matrix[x][2], nvalueOn, svalueOn)
            elif self.Matrix[x][3] == "Off" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "Yes":
                Domoticz.Log(strName+"Phone '"+self.Matrix[x][0]+"' connected to the Unifi Controller")
                self.Matrix[x][3] = "On"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
                self.Matrix[x][6] = "Online"
                self.Matrix[x][7] = ""
                UpdateDevice(self.Matrix[x][2], nvalueOn, svalueOn)
            elif self.Matrix[x][3] == "On" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "No":
                if self.Matrix[x][6] == "Online" or self.Matrix[x][6] == "None":
                    Domoticz.Log(strName+"Seems we lost phone '"+self.Matrix[x][0]+"'")
                    self.Matrix[x][6] = "Wait"
                    self.Matrix[x][7] = datetime.now()
                elif self.Matrix[x][6] == "Wait":
                    timeDiffSeconds = round((datetime.now() - self.Matrix[x][7]).total_seconds())
                    Domoticz.Log(strName+"Waiting for phone '"+self.Matrix[x][0]+"' to return ("+str(timeDiffSeconds)+"/"+str(self._Off_Delay)+" seconds)")
                    if timeDiffSeconds >= self._Off_Delay:
                        Domoticz.Log(strName+"Phone '"+self.Matrix[x][0]+"' disconnected from the Unifi Controller")
                        self.Matrix[x][3] = "Off"
                        self.Matrix[x][4] = self.Matrix[x][5]
                        self.Matrix[x][5] = "No"
                        self.Matrix[x][6] = "Offline"
                        self.Matrix[x][7] = ""
                        UpdateDevice(self.Matrix[x][2], nvalueOff, svalueOff)
            elif self.Matrix[x][3] == "On" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "Yes":
                Domoticz.Debug(strName+"Phone '"+self.Matrix[x][0]+"' still connected to the Unifi Controller")
                self.Matrix[x][3] = "On"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
                self.Matrix[x][6] = "Online"
                self.Matrix[x][7] = ""
                UpdateDevice(self.Matrix[x][2], nvalueOn, svalueOn)

        count = 0
        Domoticz.Debug(strName+"NU self.total_devices_count - "+str(self.total_devices_count))
        for x in range(self.total_devices_count):
            Domoticz.Debug(strName+" "+str(x)+" Phone Naam = "+str(self.Matrix[x][0])+" | "+str(self.Matrix[x][1])+" | "+str(self.Matrix[x][2])+" | "+str(self.Matrix[x][3])+" | "+str(self.Matrix[x][4])+" | "+str(self.Matrix[x][5]))
            if self.Matrix[x][3] == "On":
                count = count + 1
        if self._total_phones_active_before != count:
            Domoticz.Log(strName+"Total Phones connected = "+str(count))
        self._total_phones_active_before = count

        if count > 0:
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 1, "On")
        else:
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 0, "Off")


    def setVersionCheck(self, value, note):
        strName = "setVersionCheck - "
        if value is True:
            if self.versionCheck is not False:
                self.versionCheck = True
                Domoticz.Log(strName+"Plugin allowed to start (triggered by: "+note+")")
        elif value is False:
            self.versionCheck = False
            Domoticz.Error(strName+"Plugin NOT allowed to start (triggered by: "+note+")")

    def detectUnifiDevices(self):
        strName = "detect Unifi Devices: "
        try:
            if Parameters["Mode4"] == "unificontroller":
                r = self._session.get("{}/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), cookies=self._Cookies)
            elif Parameters["Mode4"] == "dreammachinepro":
                r = self._session.get("{}/proxy/network/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), cookies=self._Cookies)
            else:
                Domoticz.Error("Check configuration!!")
            self._current_status_code = r.status_code

            if self._current_status_code == 200:
                data = r.json()['data']
                totalUnifiDevices = 0
                for item in data:
                    Domoticz.Debug(strName+"Json Data (device) = " + str(item))
                    deviceCode = item['model']
                    try:
                        deviceName = self.UnifiDevicesNames[deviceCode][1]
                        if self.UnifiDevicesNames[deviceCode][0] == "uap":
                            if 'name' not in item:
                                self.uap.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                            elif 'name' in item:
                                self.uap.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model']+","+item['name'])
                        elif self.UnifiDevicesNames[deviceCode][0] == "usw":
                            if 'name' not in item:
                                self.usw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                            elif 'name' in item:
                                self.usw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model']+","+item['name'])
                        elif self.UnifiDevicesNames[deviceCode][0] == "ugw":
                            if 'name' not in item:
                                self.ugw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                            elif 'name' in item:
                                self.ugw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model']+","+item['name'])
                        elif self.UnifiDevicesNames[deviceCode][0] == "uph":
                            if 'name' not in item:
                                self.uph.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                            elif 'name' in item:
                                self.uph.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model']+","+item['name'])
                        elif self.UnifiDevicesNames[deviceCode][0] == "udm":
                            if 'name' not in item:
                                self.udm.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                            elif 'name' in item:
                                self.udm.append(self.UnifiDevicesNames[deviceCode][1]+","+item['name'])
                        Domoticz.Log(strName+"Found Unifi Device: "+deviceName+" ("+deviceCode+")")
                    except KeyError:
                        Domoticz.Error(strName+"Unifi device ("+deviceCode+") is not present in the table.")
                        self.setVersionCheck(False, "detectUnifiDevices")
            elif self._current_status_code == 401:
                Domoticz.Log(strName+"Invalid login, or login has expired")
        except requests.ReadTimeout:
            Domoticz.Error("Request to " +Parameters["Mode4"]+" timed out.")

    def devicesPerAP(self):
        strName = "devicesPerAP - "
        totalUAPs = len(self.uap)
        Domoticz.Log("Total UAP = " + str(totalUAPs))
        devUAPs = {}
        for x in range(totalUAPs):
            devUAPs[x] = set()


    def create_devicetable(self, unitnumber, devicename):
        f = open(Parameters["HomeFolder"] + "devicetable.txt", "a")
        f.write(str(unitnumber) + "," + str(devicename) + "\r\n")
        f.close()

    def create_devices(self):
        strName = "create_devices: "
        # create devices

        if (self.UNIFI_ANYONE_HOME_UNIT not in Devices):
            Domoticz.Device(Name="AnyOne",  Unit=self.UNIFI_ANYONE_HOME_UNIT, Used=1, TypeName="Switch", Image=Images['UnifiPresenceAnyone'].ID).Create()
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 0, "Off")
        self._plugin_name = Devices[self.UNIFI_ANYONE_HOME_UNIT].Name[:-9]
        Domoticz.Log(strName+"Plugin Name = "+self._plugin_name)
        if (self.UNIFI_OVERRIDE_UNIT not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "Off|1 hour|2 hours|3 hours|On",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="OverRide", Unit=self.UNIFI_OVERRIDE_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=Images['UnifiPresenceOverride'].ID).Create()
        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 0, "0")

        if (self.UNIFI_OFF_DELAY not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "0 second|30 seconds|40 seconds|50 seconds|60 seconds|70 seconds|80 seconds|90 seconds",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "1"}
            Description = "If phone often connect and reconnect with the Unifi Controller or Dreammachine an Off Delay can be configured."
            Domoticz.Device(Name="Off Delay", Unit=self.UNIFI_OFF_DELAY, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Description=Description, Image=9).Create()
            UpdateDevice(self.UNIFI_OFF_DELAY, 0, "0")

        # create phone devices
        device_mac=Parameters["Mode2"].split(",")

        found_phone = False
        count_phone = 0
        for device in device_mac:
            device = device.strip()
            phone_name, mac_id = device.split("=")
            phone_name = phone_name.strip()
            mac_id = mac_id.strip().lower()
            try:
                for item in Devices:
                    position = len(self._plugin_name)+3
                    if Devices[item].Name[position:] == phone_name:
                        Domoticz.Log(strName+"Found phone to monitor from configuration = "+device)
                        UpdateDevice(Devices[item].Unit, 1, "On")
                        UpdateDevice(Devices[item].Unit, 0, "Off")
                        found_phone = True
                        if Parameters["Mode3"] == "Yes":
                            count_phone = count_phone + 2
                        elif Parameters["Mode3"] == "No":
                            count_phone = count_phone + 1
                if found_phone == False:
                    new_unit_phone = find_available_unit_phone()
                    if Parameters["Mode5"] == "Yes":
                        Options = {"LevelActions": "||||",
                        "LevelNames": "Off|Block|Unblock|On",
                        "LevelOffHidden": "false",
                        "SelectorStyle": "0"}
                        Domoticz.Device(Name=phone_name, Unit=new_unit_phone, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=Images['UnifiPresenceOverride'].ID).Create()
                        UpdateDevice(new_unit_phone, 30, "On")
                        UpdateDevice(new_unit_phone, 0, "Off")
                        count_phone = count_phone + 1
                    else:
                        Domoticz.Device(Name=phone_name, Unit=new_unit_phone, TypeName="Switch", Used=1, Image=Images['UnifiPresenceOverride'].ID).Create()
                        UpdateDevice(new_unit_phone, 1, "On")
                        UpdateDevice(new_unit_phone, 0, "Off")
                        count_phone = count_phone + 1
                    if Parameters["Mode3"] == "Yes":
                        new_unit_geo = find_available_unit_geo()
                        phone_name = "Geo " + phone_name
                        Domoticz.Device(Name=phone_name, Unit=new_unit_geo, TypeName="Switch", Used=1, Image=Images['UnifiPresenceOverride'].ID).Create()
                        count_phone = count_phone + 1
            except:
                Domoticz.Error(strName+"Invalid phone settings. (" +device+")")

            # calculate total devices
            extra_devices = 1 # Override device
            self.total_devices_count = count_phone + extra_devices

        f = open(Parameters["HomeFolder"] + "devicetable.txt")
        self._device_table = f.readlines()

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

def is_whole(n):
    return n % 1 == 0

def UpdateDevice(Unit, nValue, sValue, Image=None):
    strName = "UpdateDevice: "
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or ((Image != None) and (Image != Devices[Unit].Image)):
            if (Image != None) and (Image != Devices[Unit].Image):
                Domoticz.Log(strName+"Update (sValue): "+str(Devices[Unit].sValue)+" --> "+str(sValue)+" ("+Devices[Unit].Name+") Image="+str(Image))
                Devices[Unit].Update(nValue=int(nValue), sValue=str(sValue), Image=Image)
                #Domoticz.Log(strName+"Update "+str(nValue)+":'"+str(nValue)+"' ("+Devices[Unit].Name+") Image="+str(Image))
                #Domoticz.Log(strName+"Update "+str(sValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+") Image="+str(Image))
            else:
                #Domoticz.Log(strName+"Update  - Old nValue = "+str(Devices[Unit].nValue)+" To New nValue = "+str(nValue)+" ("+Devices[Unit].Name+")")
                Domoticz.Log(strName+"Update (sValue): "+str(Devices[Unit].sValue)+" --> "+str(sValue)+" ("+Devices[Unit].Name+")")
                Devices[Unit].Update(nValue=int(nValue), sValue=str(sValue))

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

def find_available_unit_phone():
    for num in range(50,70):
        if num not in Devices:
            return num
    return None

def find_available_unit_geo():
    for num in range(80,100):
        if num not in Devices:
            return num
    return None

def find_available_unit_uap():
    for num in range(110,140):
        if num not in Devices:
            return num
    return None

def find_available_unit_usw():
    for num in range(150,180):
        if num not in Devices:
            return num
    return None

def find_available_unit_ugw():
    for num in range(140,250):
        if num not in Devices:
            return num
    return None

def find_available_unit_udm():
    for num in range(140,250):
        if num not in Devices:
            return num
    return None
