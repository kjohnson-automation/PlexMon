# NordVPN handler
import subprocess
import os


class NordVPN():
    """ Just a basic handler for starting/stoping the VPN service """
    def __init__(self, location):
        self.sub_location = f"{location}"
        self.sys_location = f"\"{location}\""
        self.open_vpn()
        print(f"VPN Path: {self.sub_location}")

    def open_vpn(self):
        """ Starts VPN application """
        os.system(f"\"{self.sys_location}\"")

    def connect(self, connect_cmd:str="-c"):
        """ Connects - using quick connect to NordVPN service """
        os.system(f"\"{self.sys_location}\" -c")

    def disconnect(self, disconnect_cmd:str="-d"):
        """ Disconnects from NordVPN service """
        os.system(f"{self.sys_location} {disconnect_cmd}")
        
    def connect_name(self, server_name:str="United States #4914"):
        """ Connects to <server_name> """
        cmd_list = [self.sub_location, "-c", "-n", f"{server_name}"]
        subprocess.run(cmd_list)

    def connect_group(self, server_group:str="Obfuscated Servers"):
        """ Connects to the "best" server in <server_group> """
        cmd_list = [self.sub_location, "-c", "-g", f"{server_group}"]
        subprocess.run(cmd_list)
