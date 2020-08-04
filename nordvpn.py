# NordVPN handler
import subprocess


class NordVPN():
    """ Just a basic handler for starting/stoping the VPN service """
    def __init__(self, location):
        self.location = location

    def connect(self, connect_cmd:str="-c"):
        """ Connects - using quick connect to NordVPN service """
        subprocess.run([f"{self.location}", f"{connect_cmd}"])

    def disconnect(self, disconnect_cmd:str="-d"):
        """ Disconnects from NordVPN service """
        subprocess.run([f"{self.location}", f"{disconnect_cmd}"])
        
    def connect_name(self, server_name:str="United States #4914"):
        """ Connects to <server_name> """
        subprocess.run([f"{self.location}", f"-c -n {server_name}"])

    def connect_group(self, server_group:str="Obfuscated Servers"):
        """ Connects to the "best" server in <server_group> """
        subprocess.run([f"{self.location}", f"-c -g {server_group}"])