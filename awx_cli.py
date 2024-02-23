#!/usr/bin/env python3

import sys
import json
import requests
import inquirer
from requests.auth import HTTPBasicAuth
import argparse

# Global Variables
DEBUG = False

# Utility functions
def LogMessage(msgType, msgText):
    if msgType == "debug" and DEBUG == True:
        print("[{color}DEBUG{clear}] {text}".format(color=termcolors.Cyan, clear=termcolors.End, text=msgText))
    if msgType == "error":
        print("[{color}ERROR{clear}] {text}".format(color=termcolors.Red, clear=termcolors.End, text=msgText))
    elif msgType == "warning":
        print("[{color}WARNING{clear}] {text}".format(color=termcolors.Yellow, clear=termcolors.End, text=msgText))
    elif msgType == "info":
        print("[{color}INFO{clear}] {text}".format(color=termcolors.Blue, clear=termcolors.End, text=msgText))
    elif msgType == "success":
        print("[{color}SUCCESS{clear}] {text}".format(color=termcolors.Green, clear=termcolors.End, text=msgText))

def PromptSelectFromList(promptText, optionList):
    questions = [
        inquirer.List(
            "response",
            message=promptText,
            choices=optionList,
        )
    ]
    answers = inquirer.prompt(questions)["response"]
    return answers

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
        self.Hostname = None

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

    def CreateHostInInventory(self, hostname, inventoryname):
        LogMessage("info", "Creating host {host} in inventory {inventory}.".format(host=hostname, inventory=inventoryname))

    def GetNonSmartInventoryNames(self):
        retval = list()
        for inventory in self.NonSmartInventories:
            retval.append(inventory["name"])
        return retval

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
    validActions = ['create', 'update', 'delete']
    # Parse arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-n', '--name', help='Name of a host to perform an action on.', action="store")
    argParser.add_argument('-i', '--inventory', help='Name of an inventory to perform an action on.', action="store")
    argParser.add_argument('-a', '--action', help='Type of action to perform. Options are [create|update|delete].', action="store")
    args = argParser.parse_args()
    
    # Check arguments
    if args.action == None or args.action not in validActions:
        print('Plese specify a valid action. Options are: {options}'.format(options=validActions))
        exit(1)

    # Spawn the API class and handle initialization of members
    API = AwxAPI()
    API.Connection.Endpoint = '/'

    if args.action in ['create', 'update', 'delete']:    
        # These actions require a hostname
        if args.name == None or args.name == '':
            print('Hostname is required for the specified action ({action}).'.format(action=args.action))
            exit(1)

        if args.action == 'create':
            if args.inventory != None:
                if args.inventory in [ inventory['name'] for inventory in API.NonSmartInventories ]:
                    LogMessage("debug", "Action is create and valid inventory name was specified in the command.")
                    API.CreateHostInInventory(args.name, args.inventory)
                else:
                    LogMessage("debug", "Action is create and no valid inventory was specified in the command. Prompting for selection.")
                    inventory = PromptSelectFromList("Select an inventory to create this host in:", [ inventory['name'] for inventory in API.NonSmartInventories ])
                    API.CreateHostInInventory(args.name, inventory)
            else:
                LogMessage("debug", "Action is create and no valid inventory was specified in the command. Prompting for selection.")
                inventory = PromptSelectFromList("Select an inventory to create this host in:", [ inventory['name'] for inventory in API.NonSmartInventories ])
                API.CreateHostInInventory(args.name, inventory)

        

    


#Example code:
#Present a select question with a list of regular inventories from awx
#print("Answer was {answer}".format(answer=PromptSelectFromList("Select an inventory", [ inventory['name'] for inventory in API.NonSmartInventories ])))