#!/usr/bin/env python3

import sys
import json
import requests
from requests.auth import HTTPBasicAuth

# Global Variables
DEBUG = False

# Utility functions
def LogMessage(msgType, msgText):
    if msgType == "debug" and DEBUG == True:
        print("[{color}DEBUG{clear}] {text}".format(color=termcolors.Cyan, clear=termcolors.End, text=msgText))
    if msgType == "error":
        print("[{color}DEBUG{clear}] {text}".format(color=termcolors.Red, clear=termcolors.End, text=msgText))
    elif msgType == "warning":
        print("[{color}DEBUG{clear}] {text}".format(color=termcolors.Yellow, clear=termcolors.End, text=msgText))
    elif msgType == "info":
        print("[{color}DEBUG{clear}] {text}".format(color=termcolors.Blue, clear=termcolors.End, text=msgText))

class termcolors:
    Blue = '\033[94m'
    Cyan = '\033[96m'
    Green = '\033[92m'
    Yellow = '\033[93m'
    Red = '\033[91m'
    End = '\033[0m'

class AwxAPI:
    def __init__(self):      
        self.loadConfig()
        self._connection = AwxConnection(self.Protocol, self.APIHost, self.Port, self.APIVersion, self.HTTPAuth)
        self.GetBaseInventories()

    def loadConfig(self):
        global DEBUG
        confFile = open("config.json")
        confData = json.load(confFile)
        self.HTTPAuth = HTTPBasicAuth(confData["username"], confData["password"])
        self.APIHost = confData["host"]
        self.Port = confData["port"]
        self.Protocol = confData["protocol"]
        self.APIVersion = confData["api_version"]
        if confData["verbose"] != None and confData["verbose"]:
            DEBUG = True
            LogMessage("debug", "Debug messages enabled through config.json")
            LogMessage("debug", "config.json has been parsed. Returning to AwxAPI.__init__()")
            
        confFile.close()
    
    def get_connection(self):
        return self._connection

    def GetBaseInventories(self):
        self.Connection.Endpoint = '/inventories'
        inventoryData = self.Connection.Get()

        if inventoryData == None:
            LogMessage("error", "Return code of the request was not 200. No usable data was returned.".format(color=termcolors.Red, clear=termcolors.End))
            return None

        self.SmartInventories = list()
        self.NonSmartInventories = list()
        for result in inventoryData["results"]:
            if result["kind"] != "smart":
                self.NonSmartInventories.append({
                    "name": result["name"],
                    "id": result["id"]
                })
                LogMessage("debug", "Added non-smart inventory with id: {id} and name: {name}".format(id=result["id"], name=result["name"]))
            else:
                self.SmartInventories.append({
                    "name": result["name"],
                    "id": result["id"]
                })
                LogMessage("debug", "Added smart inventory with id: {id} and name: {name}".format(id=result["id"], name=result["name"]))
        return True

    def ToString(self):
        return '''AwxAPI Object:
  Connection Information:
{ConnectionInfo}'''.format(ConnectionInfo=self.Connection.ToString())

    Connection = property(get_connection)

class AwxConnection:
    def __init__(self, protocol, host, port, version, auth):
        self.Protocol = protocol
        self.APIHost = host
        self.Port = port
        self.APIVersion = version
        self.HTTPAuth = auth
        self.Headers = {
            "Content-Type": "application/json"
        }
        self.BaseURL = "{protocol}://{host}:{port}/api/{version}".format(protocol=self.Protocol, host=self.APIHost, port=self.Port, version=self.APIVersion)

    def Get(self):
        LogMessage("debug", "Sending HTTP GET for {endpoint}".format(color=termcolors.Blue, clear=termcolors.End, endpoint=self.BaseURL + self.Endpoint))
        response = requests.get( self.BaseURL + self.Endpoint, headers=self.Headers, auth=self.HTTPAuth)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def ToString(self):
        return '''    BaseUrl: {baseUrl}
    Endpoint: {endpoint}'''.format(baseUrl=self.BaseURL, endpoint=self.Endpoint)

if __name__ == '__main__':
    API = AwxAPI()
    API.Connection.Endpoint = '/'        
    