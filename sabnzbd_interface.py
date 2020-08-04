# Sabnzbd interface

import requests
import json

class Sabnzbd():
    """ Handler for Sabnzbd API interface """
    def __init__(self, host:str="127.0.0.1", port:str="8085", api_key:str="c2e944a1f6c7110e9bb84930fabd3e2d"):
        self.baseurl = f"https://{host}:{port}/sabnzbd/api?output=json&apikey={api_key}"
        self.status = self.get_full_status()

    def create_get(self, cmd:str=""):
        """ Creates get command """
        return f"{self.baseurl}&mode={cmd}"

    def generic_json_return(self, response):
        """ checks request response and if possible returns json dict """
        if response.status_code == 200:
            return json.loads(response.text)

    def generic_get(self, cmd:str=""):
        """ Generic get command for not supported commands """
        response = requests.get(self.create_get(cmd), verify=False)
        return self.generic_json_return(response)

    def get_full_status(self):
        """ Returns full status of Sabnzbd """
        response = requests.get(self.create_get("fullstatus"), verify=False)
        return self.generic_json_return(response)
        
    def get_queue(self):
        """ Returns the current queue of sabnzbd """
        response = requests.get(self.create_get("queue"), verify=False)
        return self.generic_json_return(response)

    def get_queue_length(self):
        """ Returns the number of items in download queue """
        queue = self.get_queue()
        return queue["queue"]["noofslots_total"]

    def get_paused(self):
        """ Determins if sabnzbd is currently active/paused """
        status = self.get_full_status()
        return status["status"]["paused"]

    def restart(self):
        response = requests.get(self.create_get("restart"), verify=False)
        return self.generic_json_return(response)

    def pause_all(self):
        """ Pauses Queue """
        response = requests.get(self.create_get("pause"), verify=False)
        return self.generic_json_return(response)

    def resume_all(self):
        """ Resumes Queue """
        response = requests.get(self.create_get("resume"), verify=False)
        return self.generic_json_return(response)