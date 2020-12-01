# Domoticz-Unifi-Presence
Normal use without the option to block a configured user:

![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/AnyOne.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/OverRide.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/User%20A.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/User%20B.png)
With the option to block a configured user:
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/User%20A%20Block.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/User%20B%20Block.png)
With the option for Geofencing devices:
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Geo%20User%20A%20Block.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Geo%20User%20B%20Block.png)
Hardware information:
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/LAN%20Counter.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Uptime.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Gateway%20Mem.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Gateway%20CPU.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/WLAN%20Counter.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Gateway%20PHY.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Gateway%20CPU%20Temperature.png)
![ble_tag](https://raw.githubusercontent.com/Wizzard72/Domoticz-Unifi-Presence/master/image/Gateway%20Board%20CPU%20Temperature.png)



## Versions

    1.0.0: First release
    2.0.0: New connection code, new function to block and unblock user devices

## Introduction
There is a good Dzvents script, but I wanted to create a plugin for this. 
This plugin works with this setup:
 - Unifi Gateway
 - Unifi Switch
 - Unifi Access Points

## Installation

The plugin is tested to works on a Raspberry Pi 3b.

### Prerequisite:
  - A working Unifi Controller setup

### Install plugin on Domoticz (only Linux is supported)
To install the plugin login to the Raspberry Pi (SSH / Putty).
  
        cd /home/<username>/domoticz/plugin
  
        git clone https://github.com/Wizzard72/Domoticz-Unifi-Presence
      
        sudo systemctl restart domoticz.service

Go to the hardware tab in Domoticz and select by field Type: Unifi Presence.
Fill in all fields:
| Field | Information|
| ----- | ---------- |
| IP Address / DNS name of the Unifi Controller: | The IP Address or the DNS name of the Unifi Controller portal. |
| Port: | The port number of the Unifi Controller Portal. |
| Username: | An Unifi administrator account. |
| Password: | The password of the Unifi Administrator. |
| Site Name:  | The Unifi Site name. |
| MAC Phone Addresses: | The MAC addresses of the phones to be detected. Syntax: User A=00:00:00:00:00:00,User B=11:11:11:11:11:11 |
| Enable Geofencing devices: | This creates Geofencing devices the the configured phones |
| Interval in seconds: | The  interval to query the Unifi Controller. |
| Posibility to block devices from the network?: | The ability to block and unblock devices from the Unifi Controller. |
| Debug: | Debug information. |


## Update
Update plugin to latest version:

        cd /home/<username>/domoticz/plugin
  
        git pull
      
        In Domoticz Hardware page: Disable the Alarm System for Domoticz plugin
        
        In Domoticz Hardware page: Enable the Alarm System for Domoticz plugin

