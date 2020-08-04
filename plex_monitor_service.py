# plex server restart

import os
import sys
import time
import datetime
import subprocess
import re
import logging
import yaml

from pyservice import PyService
import sabnzbd_interface
import plex_handler
import nordvpn


def config_logger(logger_name):
    """ Configures the file logger used for PlexMon - log saved here:
        E:\PlexServiceLogs\
    """
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    file_date = datetime.datetime.now().strftime("%m_%d_%y_%H%M")
    file_handler = logging.FileHandler(f"E:\\PlexServiceLogs\\PlexMon{file_date}.log")
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    return logger

class plexMon(PyService):
    """ Service that monitors plex related services """

    _svc_name_ = "PlexMon"
    _svc_display_name_ = "PlexMon"
    _svc_description_ = "Service that handles Plex/Sabnzbd/VPN"

    def __init__(self, config:dict, args):
        """ Calls super init """
        super().__init__(args)
        self.parse_config()
        self.logger = config_logger("PlexMon Started")
        
        # Creates Sabnzbd handler to trigger pause and resume
        try:
            self.sabnzbd = sabnzbd(config["sab_host"], config["sab_port"], config["sab_api_key"])
        except:
            self.logger.critical("Could not connect to Sabnzbd - trying to restart and connect")
            self.restart_sabnzbd()
            time.sleep(60)
            self.sabnzbd = sabnzbd_interface.Sabnzbd(config["sab_host"], config["sab_port"], config["sab_api_key"])
        
        # Create Plex handler to do plex operations - may expand role in the future
        try:
            self.plex = plex_handler.Plex_interface(config["plex_host"], config["plex_port"], config["plex_token"])
        except:
            self.logger.critical("Could not connect to PMS - trying to restart and connect")
            self.restart_plex()

        # Creates very basic VPN Handler
        self.nordvpn = nordvpn.NordVPN(self.config["vpn_path"])
        
        # This just sets a class var - if it is false, SABNZBD will always be active
        if self.config["use_vpn"]:
            self.use_vpn = True
        else:
            self.use_vpn = False

    def parse_config(self):
        """ Parses the config.yaml file located in same directory """
        try:
            config_yaml = open("local_config.yaml", "r")
        except FileNotFoundError:
            self.logger.critical("Config file does not exist - service exiting")
            self.SvcStop()
        self.config = yaml.load(config_yaml, Loader=yaml.Loader)
        config_yaml.close()

    def restart_plex(self):
        """ starts plex service again after being found not running """
        self.logger.info("Restarting Plex")
        os.popen(f"{self.config['plex_path']}")

    def restart_sabnzbd(self):
        """ Starts Sabnzbd server if found not running """
        self.logger.info("Restarting SABNZBD")
        os.popen(f"{self.config['sab_path']}")

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
        current_active_streams = self.plex.get_current_sessions()
        while current_active_streams != 0:
            # Checks every 5 minutes until streams == 0
            time.sleep(300)
            current_active_streams = self.plex.get_current_sessions()
        sab_queue_len = self.sabnzbd.get_queue_length()
        sab_paused = self.sabnzbd.get_paused()
        if sab_queue_len > 0 and sab_paused:
            self.logger.info("Activating VPN Connection and SABNZBD Resume")
            self.nordvpn.connect_group()
            # Waits 1 minute for VPN to connect and routing to be reestablished
            time.sleep(60)
            self.sabnzbd.resume_all()
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
        self.sabnzbd.pause_all()
        # Allow sometime for queue to pause
        time.sleep(20)
        self.nordvpn.disconnect()
        # Waits for VPN to disconnect before returning
        time.sleep(60)
        # False signifies disconnected VPN
        return False

    def main(self):
        # initial check
        running = self.plex.is_alive()
        vpn_on = False
        # just used to create datetime object:
        start_time = datetime.datetime.now()
        vpn_on_time = start_time.replace(hour=self.config["peak_stop"])
        vpn_off_time = start_time.replace(hour=self.config["peak_start"])
        while not running and self.is_running:
            self.restart_plex()
            time.sleep(60)
            running = self.plex.is_alive()
        while True:
            current_time = datetime.datetime.now()
            # Currently only works with VPN_Start < VPN_Stop, does not handle date transitions - Will address later
            if vpn_on_time.time() < current_time.time() < vpn_off_time.time():
                if not vpn_on:
                    vpn_on = self.plex_to_vpn_transition()
                time.sleep(self.config["offpeak_interval"] * 60)
            else:
                if vpn_on:
                    vpn_on = self.vpn_to_plex_transition()
                plex_alive = self.check_plex()
                if not plex_alive:
                    self.logger.warning("Plex found not running")
                    self.restart_plex()
                time.sleep((self.config["peak_interval"]))                
            except KeyboardInterrupt:
                # Shouldn't be possible to get here but just in case
                self.logger.critical("Exiting PlexMon")
                self.SvcStop()


if __name__ == '__main__':
    plexmon.parse_command_line()