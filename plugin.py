# Unifi-Presence plugin
#
# Author: Wizzard72
#
"""
<plugin key="UnifiPresence" name="Unifi Presence" author="Wizzard72" version="2.6.0" wikilink="https://github.com/Wizzard72/Domoticz-Unifi-Presence">
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
                <option label="Dream Machine Pro" value="dreammachinepro"/>
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
from requests import Session
from typing import Pattern, Dict, Union
from datetime import datetime
# https://ubntwiki.com/products/software/unifi-controller/api


class BasePlugin:
    _unifiConn = False
    override_time = 0
    hostAuth = False
    UNIFI_ANYONE_HOME_UNIT = 1
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
    _session = Session()
    _uapDevices = []
    _total_phones_active_before = 0
    _timeout_timer = None
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
        "US16P150":  ("usw",       "UniFi Switch 16 POE-150W"),
        "S216150":   ("usw",       "UniFi Switch 16 AT-150W"),
        "US24":      ("usw",       "UniFi Switch 24"),
        "US24P250":  ("usw",       "UniFi Switch 24 POE-250W"),
        "US24PL2":   ("usw",       "UniFi Switch 24 L2 POE"),
        "US24P500":  ("usw",       "UniFi Switch 24 POE-500W"),
        "S224250":   ("usw",       "UniFi Switch 24 AT-250W"),
        "S224500":   ("usw",       "UniFi Switch 24 AT-500W"),
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
        "UDMPRO":    ("udm",       "Unifi Dream Machine Pro")
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

        self._login_data['username'] = Parameters["Username"]
        self._login_data['password'] = Parameters["Password"]
        self._login_data['remember'] = True
        self._site = Parameters["Mode1"]
        self._verify_ssl = False
        self._baseurl = 'https://'+Parameters["Address"]+':'+Parameters["Port"]
        self._session = Session()

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
            #     0           1         2           3        4              5
            # Phone_Name | MAC_ID | Unit_Number | State | Last Online | Check Online
            #   Test      1:1:1:1     50           Off      No             No
            #   Test                  50           Off      No             Yes
            #   Test                  50           On       Yes            Yes
            #   Test                  50           On       Yes            No
            #   Test                  50           Off      No             No
            device_mac=Parameters["Mode2"].split(",")
            w, h = 6, self.total_devices_count;
            self.Matrix = [[0 for x in range(w)] for y in range(h)]

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
                self.Matrix[count][1] = Device_Mac.lower()
                Device_Unit = None
                self.Matrix[count][3] = "Off"
                self.Matrix[count][4] = "No"
                self.Matrix[count][5] = "No"
                found_user = Device_Name
                for dv in Devices:
                    # Find the unit number
                    search_phone = Devices[dv].Name
                    position = search_phone.find("-")+2
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
                    found_user = "Geo "+Device_Name
                    for dv in Devices:
                        # Find the unit number
                        search_phone = Devices[dv].Name[8:]
                        if Devices[dv].Name[8:] == found_user:
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

        if (self._current_status_code == 200):
            unifiResponse = json.loads(strData)
            Domoticz.Debug(strName+"Retrieved following json: "+json.dumps(unifiResponse))
            self.onHeartbeat()

    def onCommand(self, Unit, Command, Level, Hue):
        strName = "onCommand: "
        Domoticz.Log(strName+"called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if self._current_status_code == 200:
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

        if (self._current_status_code == None) or (self._current_status_code == 401) or (self._current_status_code == 404) or (self._current_status_code != 200):
            Domoticz.Log(strName+'Attempting to reconnect Unifi Controller')
            self.login()

#        if (self._timeout_timer == False):
#            Domoticz.Log(strName+'Attempting to reconnect Unifi Controller')
#            self.login()

        if self._current_status_code == 200:
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
            self.request_online_phones()

        #timeDiff = datetime.now() - self._timeout_timer
        #timeDiff = timeDiff.seconds
        #if Parameters["Mode4"] == "dreammachinepro":
        #    if timeDiff >= 1800: #30 minutes
        #        Domoticz.Log(strName+"Log out before the API timeout")
        #        self.logout()

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
        if Parameters["Mode4"] == "unificontroller":
            self._session.headers.update({'Content-Type' : 'application/json'})
            self._session.headers.update({'Connection' : 'keep-alive'})
            r = self._session.post("{}/api/login".format(self._baseurl), data=json.dumps(self._login_data), verify=self._verify_ssl, timeout=4000)
            controller = "Unifi Controller"
            self._timeout_timer = datetime.now()
        elif Parameters["Mode4"] == "dreammachinepro":
            self._session.headers.update({'Content-Type' : 'application/json'})
            self._session.headers.update({'Connection' : 'keep-alive'})
            r = self._session.post("{}/api/auth/login".format(self._baseurl), data=json.dumps(self._login_data), verify=self._verify_ssl, timeout=4000)
            controller = "Dream Machine Pro"
            self._timeout_timer = datetime.now()
        else:
            Domoticz.Error("Check configuration!!")

        #r = self._session.post("{}{}".format(self._baseurl,url_api_login), data=json.dumps(self._login_data), verify=self._verify_ssl)

        self._current_status_code = r.status_code
        if self._current_status_code == 200:
            Domoticz.Log(strName+"Login successful into "+controller)
            self._Cookies = r.cookies
            for value in r.cookies:
                Domoticz.Log(strName+"Value = "+str(value))
            if 'X-CSRF-Token' in r.headers:
                self._session.headers.update({'X-CSRF-Token': r.headers['X-CSRF-Token']})
                Domoticz.Log(strName+"X-SCRF-Token found and added to header")
        elif self._current_status_code == 400:
            Domoticz.Error(strName+"Failed to log in to api ("+controller+") with provided credentials ("+str(self._current_status_code)+")")
        else:
            Domoticz.Error(strName+"Failed to login to the "+controller+" with errorcode "+str(self._current_status_code))
            self._current_status_code = 999

    def logout(self):
        strName = "logout: "
        """
        Log the user out
        :return: None
        """
        if self._current_status_code == 200:
            if Parameters["Mode4"] == "unificontroller":
                self._session.post("{}/logout".format(self._baseurl, verify=self._verify_ssl))
            elif Parameters["Mode4"] == "dreammachinepro":
                self._session.post("{}/proxy/network/logout".format(self._baseurl, verify=self._verify_ssl))
            else:
                Domoticz.Error("Check configuration!!")
            Domoticz.Log(strName+"Logout of the Unifi API")
            self._session.close()
            self._current_status_code = 999
            self._timeout_timer = None


    def request_details(self):
        strName = "request_details: "
        if Parameters["Mode4"] == "unificontroller":
            r = self._session.get("{}/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), data="json={}", cookies=self._Cookies)
        elif Parameters["Mode4"] == "dreammachinepro":
            r = self._session.get("{}/proxy/network/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), data="json={}", cookies=self._Cookies)
        else:
            Domoticz.Error("Check configuration!!")
        self._current_status_code = r.status_code

        if self._current_status_code == 200:
            data = r.json()['data']
            for item in data:
                Domoticz.Debug(strName+"Json Data (request details) = " + str(item))
                if item['type'] == "usw":
                    for devUnit in Devices:
                        devName = Devices[devUnit].Name
                        json_field = "CPU"
                        if 'name' not in item:
                            uapName = item['model']+" "+json_field
                        elif 'name' in item:
                            uapName = item['name']+" "+json_field
                        if devName.find(uapName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'cpu' in test_json:
                                    usw_cpu = item['system-stats']['cpu']
                                    UpdateDevice(devUnit, int(float(usw_cpu)), str(usw_cpu))
                        json_field = "Memory"
                        if 'name' not in item:
                            uapName = item['model']+" "+json_field
                        elif 'name' in item:
                            uapName = item['name']+" "+json_field
                        if devName.find(uapName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'mem' in test_json:
                                    usw_mem = item['system-stats']['mem'] 
                                    UpdateDevice(devUnit, int(float(usw_mem)), str(usw_mem))
                        json_field = "General Temperature"
                        if 'name' not in item:
                            uapName = item['model']+" "+json_field
                        elif 'name' in item:
                            uapName = item['name']+" "+json_field
                        if devName.find(uapName) > 0:
                            if 'general_temperature' in item:
                                general_temperature = item['general_temperature'] 
                                UpdateDevice(devUnit, int(float(general_temperature)), str(general_temperature))
                if item['type'] == "ugw":
                    for devUnit in Devices:
                        devName = Devices[devUnit].Name
                        json_field = "CPU Usage"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'cpu' in test_json:
                                    ugw_cpu = item['system-stats']['cpu'] 
                                    UpdateDevice(devUnit, int(float(ugw_cpu)), str(ugw_cpu))
                        json_field = "Memory"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'mem' in test_json:
                                    ugw_mem = item['system-stats']['mem'] 
                                    UpdateDevice(devUnit, int(float(ugw_mem)), str(ugw_mem))
                        json_field = "Board (CPU) Temperature"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'Board (CPU)' in test_json:
                                        ugw_board_cpu_temp = item['system-stats']['temps']['Board (CPU)'][:-2]
                                        UpdateDevice(devUnit, int(float(ugw_board_cpu_temp)), str(ugw_board_cpu_temp))
                        json_field = "Board (PHY) Temperature"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'Board (PHY)' in test_json:
                                        ugw_board_phy_temp = item['system-stats']['temps']['Board (PHY)'][:-2]
                                        UpdateDevice(devUnit, int(float(ugw_board_phy_temp)), str(ugw_board_phy_temp))
                        json_field = "CPU Temperature"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'CPU' in test_json:
                                        ugw_cpu_temp = item['system-stats']['temps']['CPU'][:-2]
                                        UpdateDevice(devUnit, int(float(ugw_cpu_temp)), str(ugw_cpu_temp))
                        json_field = "PHY Temperature"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'PHY' in test_json:
                                        ugw_phy_temp = item['system-stats']['temps']['PHY'][:-2]
                                        UpdateDevice(devUnit, int(float(ugw_phy_temp)), str(ugw_phy_temp))
                        json_field = "Latency"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'speedtest-status' in item:
                                test_json = item['speedtest-status']
                                if 'latency' in test_json:
                                    ugw_latency = item['speedtest-status']['latency']
                                    UpdateDevice(devUnit, int(float(ugw_latency)), str(ugw_latency))
                        json_field = "XPut Download"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'speedtest-status' in item:
                                test_json = item['speedtest-status']
                                if 'xput_download' in test_json:
                                    ugw_xput_download = item['speedtest-status']['xput_download'] 
                                    UpdateDevice(devUnit, int(float(ugw_xput_download)), str(ugw_xput_download))
                        json_field = "XPut Upload"
                        if 'name' not in item:
                            ugwName = item['model']+" "+json_field
                        elif 'name' in item:
                            ugwName = item['name']+" "+json_field
                        if devName.find(ugwName) > 0:
                            if 'speedtest-status' in item:
                                test_json = item['speedtest-status']
                                if 'xput_upload' in test_json:
                                    ugw_xput_upload = item['speedtest-status']['xput_upload'] 
                                    UpdateDevice(devUnit, int(float(ugw_xput_upload)), str(ugw_xput_upload))
                if item['type'] == "uap":
                    for devUnit in Devices:
                        devName = Devices[devUnit].Name
                        json_field = "CPU"
                        if 'name' not in item:
                            uapName = item['model']+" "+json_field
                        elif 'name' in item:
                            uapName = item['name']+" "+json_field
                        if devName.find(uapName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'cpu' in test_json:
                                    uap_cpu = item['system-stats']['cpu'] 
                                    UpdateDevice(devUnit, int(float(uap_cpu)), str(uap_cpu))
                        json_field = "Memory"
                        if 'name' not in item:
                            uapName = item['model']+" "+json_field
                        elif 'name' in item:
                            uapName = item['name']+" "+json_field
                        if devName.find(uapName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'mem' in test_json:
                                    uap_mem = item['system-stats']['mem'] 
                                    UpdateDevice(devUnit, int(float(uap_mem)), str(uap_mem))
                if item['type'] == "udm":
                    for devUnit in Devices:
                        devName = Devices[devUnit].Name
                        json_field = "CPU Usage"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'cpu' in test_json:
                                    udm_cpu = item['system-stats']['cpu'] 
                                    UpdateDevice(devUnit, int(float(udm_cpu)), str(udm_cpu))
                        json_field = "Memory"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'mem' in test_json:
                                    udm_mem = item['system-stats']['mem'] 
                                    UpdateDevice(devUnit, int(float(udm_mem)), str(udm_mem))
                        json_field = "Board (CPU) Temperature"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'Board (CPU)' in test_json:
                                        udm_board_cpu_temp = item['system-stats']['temps']['Board (CPU)'][:-2]
                                        UpdateDevice(devUnit, int(float(udm_board_cpu_temp)), str(udm_board_cpu_temp))
                        json_field = "Board (PHY) Temperature"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'Board (PHY)' in test_json:
                                        udm_board_phy_temp = item['system-stats']['temps']['Board (PHY)'][:-2]
                                        UpdateDevice(devUnit, int(float(udm_board_phy_temp)), str(udm_board_phy_temp))
                        json_field = "CPU Temperature"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'CPU' in test_json:
                                        udm_cpu_temp = item['system-stats']['temps']['CPU'][:-2]
                                        UpdateDevice(devUnit, int(float(udm_cpu_temp)), str(udm_cpu_temp))
                        json_field = "PHY Temperature"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'system-stats' in item:
                                test_json = item['system-stats']
                                if 'temps' in test_json:
                                    test_json = item['system-stats']['temps']
                                    if 'PHY' in test_json:
                                        udm_phy_temp = item['system-stats']['temps']['PHY'][:-2]
                                        UpdateDevice(devUnit, int(float(udm_phy_temp)), str(udm_phy_temp))
                        json_field = "Latency"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'speedtest-status' in item:
                                test_json = item['speedtest-status']
                                if 'latency' in test_json:
                                    udm_latency = item['speedtest-status']['latency']
                                    UpdateDevice(devUnit, int(float(udm_latency)), str(udm_latency))
                        json_field = "XPut Download"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'speedtest-status' in item:
                                test_json = item['speedtest-status']
                                if 'xput_download' in test_json:
                                    udm_xput_download = item['speedtest-status']['xput_download'] 
                                    UpdateDevice(devUnit, int(float(udm_xput_download)), str(udm_xput_download))
                        json_field = "XPut Upload"
                        if 'name' not in item:
                            udmName = item['model']+" "+json_field
                        elif 'name' in item:
                            udmName = item['name']+" "+json_field
                        if devName.find(udmName) > 0:
                            if 'speedtest-status' in item:
                                test_json = item['speedtest-status']
                                if 'xput_upload' in test_json:
                                    udm_xput_upload = item['speedtest-status']['xput_upload'] 
                                    UpdateDevice(devUnit, int(float(udm_xput_upload)), str(udm_xput_upload))
        elif self._current_status_code == 401:
            Domoticz.Log(strName+"Invalid login, or login has expired")
            self.login()
        elif self._current_status_code == 404:
            Domoticz.Log(strName+"Invalid login, or login has expired")
            self.login()




    def request_online_phones(self):
        strName = "request_online_phones: "
        if Parameters["Mode4"] == "unificontroller":
            r = self._session.get("{}/api/s/{}/stat/sta".format(self._baseurl, self._site, verify=self._verify_ssl), data="json={}", cookies=self._Cookies)
        elif Parameters["Mode4"] == "dreammachinepro":
            r = self._session.get("{}/proxy/network/api/s/{}/stat/sta".format(self._baseurl, self._site, verify=self._verify_ssl), data="json={}", cookies=self._Cookies)
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
            if self.Matrix[x][3] == "Off" and self.Matrix[x][4] == "No" and self.Matrix[x][5] == "No":
                self.Matrix[x][4] = self.Matrix[x][5]
                if Devices[self.Matrix[x][2]].nValue != 0:
                    UpdateDevice(self.Matrix[x][2], nvalueOff, svalueOff)
            elif self.Matrix[x][3] == "Off" and self.Matrix[x][4] == "No" and self.Matrix[x][5] == "Yes":
                Domoticz.Log(strName+"Phone '"+self.Matrix[x][0]+"' connected to the Unifi Controller")
                self.Matrix[x][3] = "On"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
                UpdateDevice(self.Matrix[x][2], nvalueOn, svalueOn)
            elif self.Matrix[x][3] == "Off" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "Yes":
                Domoticz.Log(strName+"Phone '"+self.Matrix[x][0]+"' connected to the Unifi Controller")
                self.Matrix[x][3] = "On"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
                UpdateDevice(self.Matrix[x][2], nvalueOn, svalueOn)
            elif self.Matrix[x][3] == "On" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "No":
                Domoticz.Log(strName+"Phone '"+self.Matrix[x][0]+"' disconnected from the Unifi Controller")
                self.Matrix[x][3] = "Off"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
                UpdateDevice(self.Matrix[x][2], nvalueOff, svalueOff)
            elif self.Matrix[x][3] == "On" and self.Matrix[x][4] == "Yes" and self.Matrix[x][5] == "Yes":
                Domoticz.Debug(strName+"Phone '"+self.Matrix[x][0]+"' still connected to the Unifi Controller")
                self.Matrix[x][3] = "On"
                self.Matrix[x][4] = self.Matrix[x][5]
                self.Matrix[x][5] = "No"
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
        if Parameters["Mode4"] == "unificontroller":
            r = self._session.get("{}/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), data="json={}", cookies=self._Cookies)
        elif Parameters["Mode4"] == "dreammachinepro":
            r = self._session.get("{}/proxy/network/api/s/{}/stat/device".format(self._baseurl, self._site, verify=self._verify_ssl), data="json={}", cookies=self._Cookies)
        else:
            Domoticz.Error("Check configuration!!")

        self._current_status_code = r.status_code

        if self._current_status_code == 200:
            data = r.json()['data']
            totalUnifiDevices = 0
            for item in data:
                Domoticz.Debug(strName+"Json Data (device) = " + str(item))
                deviceCode = item['model']
                deviceName = self.UnifiDevicesNames[deviceCode][1]
                if self.UnifiDevicesNames[deviceCode][0] == "uap":
                    if 'name' not in item:
                         self.uap.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                    elif 'name' in item:
                        self.uap.append(self.UnifiDevicesNames[deviceCode][1]+","+item['name'])
                elif self.UnifiDevicesNames[deviceCode][0] == "usw":
                    if 'name' not in item:
                        self.usw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                    elif 'name' in item:
                        self.usw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['name'])
                elif self.UnifiDevicesNames[deviceCode][0] == "ugw":
                    if 'name' not in item:
                        self.ugw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                    elif 'name' in item:
                        self.ugw.append(self.UnifiDevicesNames[deviceCode][1]+","+item['name'])
                elif self.UnifiDevicesNames[deviceCode][0] == "uph":
                    if 'name' not in item:
                        self.uph.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                    elif 'name' in item:
                        self.uph.append(self.UnifiDevicesNames[deviceCode][1]+","+item['name'])
                elif self.UnifiDevicesNames[deviceCode][0] == "udm":
                    if 'name' not in item:
                        self.udm.append(self.UnifiDevicesNames[deviceCode][1]+","+item['model'])
                    elif 'name' in item:
                        self.udm.append(self.UnifiDevicesNames[deviceCode][1]+","+item['name'])
                Domoticz.Log(strName+"Found Unifi Device: "+deviceName+" ("+deviceCode+")")
        elif self._current_status_code == 401:
            Domoticz.Log(strName+"Invalid login, or login has expired")


    def devicesPerAP(self):
        strName = "devicesPerAP - "
        totalUAPs = len(self.uap)
        Domoticz.Log("Total UAP = " + str(totalUAPs))
        devUAPs = {}
        for x in range(totalUAPs):
            devUAPs[x] = set()


    def create_devices(self):
        strName = "create_devices: "
        # create devices
        foundDevice = False
        for device in self.uap:
            device = device.strip()
            deviceType, deviceName = device.split(",")
            for item in Devices:
                devName = Devices[item].Name
                uapName = deviceName
                if devName.find(uapName) > 0:
                    foundDevice = True
            if foundDevice == False:
                    new_unit = find_available_unit_uap()
                    Domoticz.Device(Name=deviceName+" CPU",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                    UpdateDevice(new_unit, 0, "0")
                    new_unit = find_available_unit_uap()
                    Domoticz.Device(Name=deviceName+" Memory",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                    UpdateDevice(new_unit, 0, "0")

        foundDevice = False
        for device in self.usw:
            device = device.strip()
            deviceType, deviceName = device.split(",")
            for item in Devices:
                devName = Devices[item].Name
                uswName = deviceName
                if devName.find(uswName) > 0:
                    foundDevice = True
            if foundDevice == False:
                new_unit = find_available_unit_usw()
                Domoticz.Device(Name=deviceName+" CPU",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_usw()
                Domoticz.Device(Name=deviceName+" Memory",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_usw()
                Domoticz.Device(Name=deviceName+" General Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")


        foundDevice = False
        for device in self.ugw:
            device = device.strip()
            deviceType, deviceName = device.split(",")
            for item in Devices:
                devName = Devices[item].Name
                ugwName = deviceName
                if devName.find(ugwName) > 0:
                    foundDevice = True
            if foundDevice == False:
                new_unit = find_available_unit_ugw()
                Domoticz.Device(Name=deviceName+" CPU Usage",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Domoticz.Device(Name=deviceName+" Memory",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Domoticz.Device(Name=deviceName+" Board (CPU) Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Domoticz.Device(Name=deviceName+" Board (PHY) Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Domoticz.Device(Name=deviceName+" CPU Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Domoticz.Device(Name=deviceName+" PHY Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Options = {'Custom': '1;milliseconds'}
                Domoticz.Device(Name=deviceName+" Latency",  Unit=new_unit, Used=1, Type=243, Subtype=31, Options=Options).Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Options = {'Custom': '1;MBit/s'}
                Domoticz.Device(Name=deviceName+" XPut Download",  Unit=new_unit, Used=1, Type=243, Subtype=31, Options=Options).Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_ugw()
                Options = {'Custom': '1;MBit/s'}
                Domoticz.Device(Name=deviceName+" XPut Upload",  Unit=new_unit, Used=1, Type=243, Subtype=31, Options=Options).Create()
                UpdateDevice(new_unit, 0, "0")


        foundDevice = False
        for device in self.udm:
            device = device.strip()
            deviceType, deviceName = device.split(",")
            for item in Devices:
                devName = Devices[item].Name
                udmName = deviceName
                if devName.find(udmName) > 0:
                    foundDevice = True
            if foundDevice == False:
                new_unit = find_available_unit_udm()
                Domoticz.Device(Name=deviceName+" CPU Usage",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Domoticz.Device(Name=deviceName+" Memory",  Unit=new_unit, Used=1, TypeName="Percentage").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Domoticz.Device(Name=deviceName+" Board (CPU) Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Domoticz.Device(Name=deviceName+" Board (PHY) Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Domoticz.Device(Name=deviceName+" CPU Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Domoticz.Device(Name=deviceName+" PHY Temperature",  Unit=new_unit, Used=1, TypeName="Temperature").Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Options = {'Custom': '1;milliseconds'}
                Domoticz.Device(Name=deviceName+" Latency",  Unit=new_unit, Used=1, Type=243, Subtype=31, Options=Options).Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Options = {'Custom': '1;MBit/s'}
                Domoticz.Device(Name=deviceName+" XPut Download",  Unit=new_unit, Used=1, Type=243, Subtype=31, Options=Options).Create()
                UpdateDevice(new_unit, 0, "0")
                new_unit = find_available_unit_udm()
                Options = {'Custom': '1;MBit/s'}
                Domoticz.Device(Name=deviceName+" XPut Upload",  Unit=new_unit, Used=1, Type=243, Subtype=31, Options=Options).Create()
                UpdateDevice(new_unit, 0, "0")






        if (self.UNIFI_ANYONE_HOME_UNIT not in Devices):
            Domoticz.Device(Name="AnyOne",  Unit=self.UNIFI_ANYONE_HOME_UNIT, Used=1, TypeName="Switch", Image=Images['UnifiPresenceAnyone'].ID).Create()
            UpdateDevice(self.UNIFI_ANYONE_HOME_UNIT, 0, "Off")
        if (self.UNIFI_OVERRIDE_UNIT not in Devices):
            Options = {"LevelActions": "||||",
                       "LevelNames": "Off|1 hour|2 hours|3 hours|On",
                       "LevelOffHidden": "false",
                       "SelectorStyle": "0"}
            Domoticz.Device(Name="OverRide", Unit=self.UNIFI_OVERRIDE_UNIT, TypeName="Selector Switch", Switchtype=18, Used=1, Options=Options, Image=Images['UnifiPresenceOverride'].ID).Create()
        UpdateDevice(self.UNIFI_OVERRIDE_UNIT, 0, "0")

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
                    devName = Devices[item].Name
                    position = devName.find("-")+2
                    if Devices[item].Name[position:] == phone_name:
                        Domoticz.Log(strName+"Found phone to monitor from configuration = "+device)
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
                        count_phone = count_phone + 1
                    else:
                        Domoticz.Device(Name=phone_name, Unit=new_unit_phone, TypeName="Switch", Used=1, Image=Images['UnifiPresenceOverride'].ID).Create()
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
