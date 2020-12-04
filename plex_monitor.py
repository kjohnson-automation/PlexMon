#!/usr/bin/env python3
# plex server script

import os
import sys
import time
import datetime
import subprocess
import logging
import yaml

from handlers import sabnzbd_interface
from handlers import plex_handler
from handlers import nordvpn


def config_logger(logger_name, log_loc:str=None):
    """ Configures the file logger used for PlexMon - log saved here:
        E:\PlexServiceLogs
    """
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    file_date = datetime.datetime.now().strftime("%m_%d_%y_%H%M")
    if log_loc is not None and log_loc.endswith("\\"):
        logfile = f"{log_loc}PlexMon{file_date}.log"
    elif log_loc is not None:
        logfile = f"{log_loc}\\PlexMon{file_date}.log"
    else:
        # Default Log location -- FOR ME
        logfile = f"E:\\PlexServiceLogs\\PlexMon{file_date}.log"
    print(f"Log File: {logfile}")
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    return logger

class plexMon():
    """ This is the main PlexMon monitor - it will enable/disable vpn, pause/resume SABNZBD, and restart plex should it be found
        not running.  The config file dictates the Peak/Off Peak hours as well as all the ncessary keys for connecting to the
        different services
    """
    def __init__(self, config:str):
        self.__version__ = "0.1.1"
        print("     ____   _    ____  _     _      \n",
              "    |    | | |  |  __| \ \  / /     \n",
              "    |  D_| | |  |  -,   \ \/ /      \n",
              "    |  |   | |_ |  -'_  / /\ \      \n",
              "    |__|   |___||____| /_/  \_\     \n")
        self.parse_config(config)
        self.logger = config_logger(f"PlexMon Started - Version: {self.__version__}")
        # Creates Sabnzbd handler to trigger pause and resume

        try:
            print("Connecting to sabnzbd")
            self.sabnzbd = sabnzbd_interface.Sabnzbd(self.config["sab_host"], self.config["sab_port"], self.config["sab_api_key"])
        except ConnectionError:
            print("Failed initial connect to sabnzbd- entering except")
            self.logger.critical("Could not connect to Sabnzbd - trying to restart and connect")
            self.restart_sabnzbd()
            time.sleep(60)
            self.sabnzbd = sabnzbd_interface.Sabnzbd(self.config["sab_host"], self.config["sab_port"], self.config["sab_api_key"])

        # Create Plex handler to do plex operations - may expand role in the future
        try:
            print("connecting to plex")
            self.plex = plex_handler.Plex_interface(self.config["plex_host"], self.config["plex_port"], self.config["plex_token"])
        except ConnectionError:
            print("failed initial connect to plex")
            self.logger.critical("Could not connect to PMS - trying to restart and connect")
            self.restart_plex()
        self.is_running = self.check_plex()

        # Creates very basic VPN Handler
        self.nordvpn = nordvpn.NordVPN(self.config["vpn_path"])

        # This just sets a class var - if it is false, SABNZBD will always be active
        if self.config["use_vpn"]:
            self.use_vpn = True
        else:
            self.use_vpn = False
        # TODO: Document early_transition
        self.early_transition = False

    def parse_config(self, config):
        """ Parses the config.yaml file located in same directory """
        try:
            config_yaml = open(config, "r")
        except FileNotFoundError:
            self.logger.critical("Config file does not exist - service exiting")
            sys.exit(f"Invalid Config File: {config}")
        self.config = yaml.load(config_yaml, Loader=yaml.Loader)
        config_yaml.close()

    def restart_plex(self):
        """ starts plex service again after being found not running """
        self.logger.info("Restarting Plex")
        os.popen(f"\"{self.config['plex_path']}\"")

    def restart_sabnzbd(self):
        """ Starts Sabnzbd server if found not running """
        self.logger.info("Restarting SABNZBD")
        os.popen(f"\"{self.config['sab_path']}\"")

    def check_plex(self):
        """ Queries Plex to see if our target server is listed """
        return self.plex.is_alive(self.config["plex_server_name"])

    def get_plex_activity(self):
        """ Returns current active streams on PMS """
        return self.plex.get_current_sessions()

    def plex_to_vpn_transition(self):
        """ Handles the plex to VPN transition:
            Checks active streams to make sure its 0
            Activates VPN
            Resumes SABNZBD activity
        """
        self.logger.info("Transitioning to VPN/active Sabnzbd")
        # resets for next cycle
        self.eary_transition = False
        current_active_streams = self.plex.get_current_sessions()
        while current_active_streams != "0":
            # Checks every 5 minutes until streams == 0
            self.logger.info("Found active streams")
            time.sleep(300)
            current_active_streams = self.plex.get_current_sessions()
        sab_queue_len = self.sabnzbd.get_queue_length()
        self.logger.info(f"Currently {sab_queue_len} to download")
        sab_paused = self.sabnzbd.get_paused()
        if sab_queue_len > 0 and sab_paused:
            self.logger.info("Activating VPN Connection and SABNZBD Resume")
            # For some reason - group is not working correctly
            self.nordvpn.connect_group()
            print("Returned from VPN connect")
            # self.nordvpn.connect()
            # Waits 1 minute for VPN to connect and routing to be reestablished
            time.sleep(60)
            self.sabnzbd.resume_all()
            queue = self.sabnzbd.get_queue()
            self.logger.info("Getting Files:")
            for file in queue["queue"]["slots"]:
                self.logger.info(f"Filename: {file['filename']}")
            # True represents active downloading and VPN connection
            return True
        # False represents nothing to download so no VPN connection needed
        return False

    def vpn_to_plex_transition(self):
        """ Handles the VPN back to plex transition:
            Pauses SABNZBD
            Disconnects VPN
        """
        # Only Pauses downloads if use_vpn
        self.logger.info("Deactivating VPN and Pausing SABNZBD")
        # resets for next cycle
        self.eary_transition = False
        self.sabnzbd.pause_all()
        # Allow sometime for queue to pause
        time.sleep(20)
        self.nordvpn.disconnect()
        print("Disconnected VPN")
        # Waits for VPN to disconnect before returning
        time.sleep(60)
        # False signifies disconnected VPN
        return False

    def trigger_early_transition(self):
        """ Nothing left in Sabnzbd queue so triggering early VPN exit """
        self.sabnzbd.pause_all()
        self.nordvpn.disconnect()
        self.eary_transition = True

    def end_monitor(self):
        """ Called when disconnecting """
        self.sabnzbd.pause_all()
        self.nordvpn.disconnect()

    def check_time(self, begin_time, end_time):
        # If check time is not given, default to current UTC time
        current_time = datetime.datetime.now().time()
        if begin_time < end_time:
            return current_time >= begin_time and current_time <= end_time
        else: # crosses midnight
            return current_time >= begin_time or current_time <= end_time

    def loop(self):
        # initial check
        running = self.check_plex()
        self.logger.info(f"Initial Plex check - plex is running: {running}")
        # Because NORD doesn't have a way to check its connected from the cmdline
        vpn_on = False
        # just used to create datetime object:
        # start_time = datetime.datetime.now()
        # vpn_on_time = start_time.replace(hour=self.config["peak_stop"], minute=0, second=0, microsecond=0)
        # vpn_off_time = start_time.replace(hour=self.config["peak_start"], minute=0, second=0, microsecond=0)
        vpn_on_time = datetime.time(self.config["peak_stop"], 00)
        vpn_off_time = datetime.time(self.config["peak_start"], 00)
        while not running:
            self.restart_plex()
            time.sleep(60)
            running = self.plex.is_alive()
        while True:
            try:
                # current_time = datetime.datetime.now()
                # Currently only works with VPN_ON < VPN_OFF, does not handle date transitions - Will address later
                # if vpn_on_time.time() < current_time.time() < vpn_off_time.time():
                if self.check_time(vpn_on_time, vpn_off_time):
                    # if self.eary_transition:
                    #     pass
                    if not vpn_on and not self.eary_transition:
                        self.logger.info("Starting VPN")
                        vpn_on = self.plex_to_vpn_transition()
                    # Removing the specified timeout for off peak - Plex is not accessible anyway
                    time.sleep(60)
                    if self.sabnzbd.get_queue_length() == 0:
                        self.trigger_early_transition()
                else:
                    if vpn_on:
                        self.logger.info("Exiting VPN")
                        vpn_on = self.vpn_to_plex_transition()
                    plex_alive = self.check_plex()
                    if not plex_alive:
                        self.logger.warning("Plex found not running")
                        self.restart_plex()
                    time.sleep(int(self.config["peak_interval"]) * 60)

                # Daily update of VPN Times
                # start_time = datetime.datetime.now().time()
                # vpn_on_time = start_time.replace(hour=self.config["peak_stop"], minute=0, second=0, microsecond=0)
                vpn_on_time = datetime.time(self.config["peak_stop"], 00)
                # vpn_off_time = start_time.replace(hour=self.config["peak_start"], minute=0, second=0, microsecond=0)
                vpn_off_time = datetime.time(self.config["peak_start"], 00)
            except KeyboardInterrupt:
                print("triggering exit")
                self.logger.critical("Exiting PlexMon")
                self.end_monitor()
                sys.exit()

if __name__ == '__main__':
    # Handling the pre-config to make sure things go smoothly
    # Waits 2 minutes after starting before trigginger anything - allowing for system to completely boot since it starts on boot
    time.sleep(120)
    arg_len = len(sys.argv)
    if arg_len < 2:
        print("No config file defined - please select a config file and try again: python(3) plex_monitor.py <configfile.yaml>")
        sys.exit("Try again with config file")
    if arg_len >= 2:
        if arg_len > 2:
            print(f"All arguments after {sys.argv[1]} are being ignored: {sys.argv[2:]}")
        config = sys.argv[1]
        if ".yaml" not in config.lower():
            config_yaml = f"{config}.yaml"
            if os.path.isfile(config_yaml):
                config = config_yaml
            else:
                sys.exit(f"Could not find {config_yaml} - please check config file and try again")
        else:
            if not os.path.isfile(config):
                sys.exit(f"Could not find {config} - please check config file and try again")
    # Starting the monitor!
    plex_monitor = plexMon(config)
    plex_monitor.loop()
