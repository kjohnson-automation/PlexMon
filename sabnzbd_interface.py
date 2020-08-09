# Sabnzbd interface

import requests
import json

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Sabnzbd():
    """ Handler for Sabnzbd API interface """
    def __init__(self, host:str="127.0.0.1", port:str="8085", api_key:str="c2e944a1f6c7110e9bb84930fabd3e2d"):
        self.baseurl = f"https://{host}:{port}/sabnzbd/api?output=json&apikey={api_key}"
        self.status = self.get_full_status()

    def create_get(self, cmd:str=""):
        """ Creates get command """
        return f"{self.baseurl}&mode={cmd}"

    def _get_request(self, cmd:str):
        """ Called by all commands - returns full response if available """
        get = self.create_get(cmd)
        try:
            response = requests.get(get, verify=False)
            return self.generic_json_return(response)
        except requests.ConnectionError as error:
            print("Sabnzbd Unavailable")
            print(f"Error: {error}")
            return ""

    def generic_json_return(self, response):
        """ checks request response and if possible returns json dict """
        if response.status_code == 200:
            return json.loads(response.text)

    def generic_get(self, cmd:str=""):
        """ Generic get command for not supported commands """
        return self._get_request(cmd)
        # response = requests.get(self.create_get(cmd), verify=False)
        # return self.generic_json_return(response)

    def get_full_status(self):
        """ Returns full status of Sabnzbd """
        return self._get_request("fullstatus")
        # response = requests.get(self.create_get("fullstatus"), verify=False)
        # return self.generic_json_return(response)
        
    def get_queue(self):
        """ Returns the current queue of sabnzbd """
        return self._get_request("queue")
        # response = requests.get(self.create_get("queue"), verify=False)
        # return self.generic_json_return(response)

    def get_queue_length(self):
        """ Returns the number of items in download queue """
        queue = self.get_queue()
        if queue == "":
            return "Sabnzbd Unavailable"
        return queue["queue"]["noofslots_total"]

    def get_paused(self):
        """ Determins if sabnzbd is currently active/paused """
        status = self.get_full_status()
        if status == "":
            return "Sabnzbd Unavailable"
        return status["status"]["paused"]

    def restart(self):
        """ Restarts Sabnzbd """
        return self._get_request("restart")
        # response = requests.get(self.create_get("restart"), verify=False)
        # return self.generic_json_return(response)

    def pause_all(self):
        """ Pauses Queue """
        return self._get_request("pause")
        # response = requests.get(self.create_get("pause"), verify=False)
        # return self.generic_json_return(response)

    def resume_all(self):
        """ Resumes Queue """
        return self._get_request("resume")
        # response = requests.get(self.create_get("resume"), verify=False)
        # return self.generic_json_return(response)
