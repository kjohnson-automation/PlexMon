#plex interface

import requests
import xmltodict


class Plex_interface():
    """ Plex interface for checking plex status """
    def __init__(self, host:str="127.0.0.1", port:int=32400, token:str="4QczhHhzCkgDN4xB9E-3"):
        self.base_addr = f"https://{host}:{port}/"
        self.key_str = f"?X-Plex-Token={token}"

    def gen_get_str(self, cmd:str=""):
        """ Generates a API get str """
        return f"{self.base_addr}{cmd}{self.key_str}"

    def parse_xml(self, xml_str):
        """ Returns dict of xml str """
        return xmltodict.parse(xml_str)

    def get_current_sessions(self):
        """ Checks to see if any active sessions are being played """
        # /status/sessions
        cmd_str = self.gen_get_str("status/sessions")
        try:
            play_xml = requests.get(cmd_str, verify=False)
        except ConnectionError:
            return False
        play_dict = self.parse_xml(play_xml.text)
        return play_dict["MediaContainer"]["@size"]

    def is_alive(self, name:str=""):
        """ Checks if server is alive """
        # /servers
        cmd_str = self.gen_get_str("servers")
        try:
            servers_xml = requests.get(cmd_str, verify=False)
        except ConnectionError:
            return False
        servers_dict = self.parse_xml(servers_xml.text)
        server =  servers_dict["MediaContainer"]["Server"]["@name"]
        return server == name