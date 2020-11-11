# <center> README for PlexMon Service </center>

The goal of this program is to create a service that will monitor Plex, SABNZBD, and control a vpn for automated downloading only over VPN connections. The goal of this being a service will be complete running in the background with a **LIGHT** log file created with information for debug if anything should happend.

I will be using NORD VPN but it should be transferable to any VPN that supports command line launching and connection.

Version 1 Support will include:
* Scheduled SABNZBD Resume/Pause
* Scheduled NORD VPN start/stop
* Plex service monitoring and relaunch
    * The plex monitor will monitor plex availability during different intervals depending on time of day as to not overload with queries unnecessarily - can be modified
* Config.yaml file support - one stop for all config values used in the service. This will include
    * API Keys
    * Paths for programs
    * Interval timing
    * Log file location
    * etc...


## How to Use ##

* First make sure python is installed and within your path, it shouldn't matter exactly which version of python, but something over 3.5 is required.
* Make sure you have the following libraries installed by doing: ```pip install <library>```
    * pyyaml
    * requests
    * xmltodict

* Populate the config.yaml file that has an empty template included
    * The plex token is the hardest to get, follow [this guide.](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
* Once the config file is complete - navigate to the directory it is saved in and run:
    * ```python plex_monitor.py config.yaml```

### PlexMon should now be running as a script and automatically toggle the VPN and Sabnzbd during the specified intervals.

## BUGS ##
* Still working on fixing a couple toggle vpn and resume/pause sabnzbd - note it will not start sabnzbd without vpn, however, theres a date check issue
* Going to start integrating some nordvpn apis into the monitor.


 - Updated 11/10/20