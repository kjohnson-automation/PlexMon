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

You guys know me, let me know if there is anything in paritcular you want to see.
