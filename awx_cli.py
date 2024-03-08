#!/usr/bin/env python3

# Required imports
# Standard imports
import sys
import argparse
import re
import json
import requests
from requests.auth import HTTPBasicAuth

# Inquirer is a library for interactive user prompts
import inquirer

# Global Variables
# DEBUG determines if messages of type debug are displayed to the user
DEBUG = False

# Utility functions
def IsValidInventoryName(inventoryName, inventoryList):
    # Check for inventoryName in inventoryList
    # Return: True if present, False if not
    for i in inventoryList:   
        if i['name'] == inventoryName:
            return True
    return False
        

def ExpandGlob(glob):
    # Support for SLURM/Bash like hostname globs
    # Example: lc01g[01-03] should expand to a list of [lc01g01, lc01g02, lc01g03]

    # Use a regular expression to see if the supplied string contains a usable glob
    pattern_match = re.match(r'(.+)\[([0-9]+)-([0-9]+)\]', glob)

    if pattern_match:
        # Break the supplied string into a prefix (non-globbed, shared by all hostnames)
        prefix = pattern_match.group(1)
        # Determine the first number to start enumeration at
        start_num = int(pattern_match.group(2))
        # Determine the final number to be enumerated
        end_num = int(pattern_match.group(3))

        # Append a prefix followed by the glob
        expanded_list = [f"{prefix}{i:02}" for i in range(start_num, end_num+1)]
        return expanded_list
    else:
        # Return the regular expression
        return [glob_pattern]

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
    # Present an Inquirer multiple choice to the user using the promptText and list of options supplied
    questions = [
        inquirer.Checkbox(
            "response",
            message=promptText,
            choices=optionList,
        )
    ]
    answers = inquirer.prompt(questions)["response"]
    # Return the chosen answers as a list
    return answers

# Some useful color codes to use for printing messages based on type of message.
class termcolors:
    Blue = '\033[94m'
    Cyan = '\033[96m'
    Green = '\033[92m'
    Yellow = '\033[93m'
    Red = '\033[91m'
    End = '\033[0m'

class AwxAPI:
    # This class represents the "controller" level logic
    def __init__(self):
        self.loadConfig() # Read the config file
        self._connection = AwxConnection(self.Protocol, self.APIHost, self.Port, self.APIVersion, self.HTTPAuth) # Establish the AWX API connection
        self.GetBaseInventories() # Fetch all basic inventories (not smart or constructed)

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
        inventory_id = self.GetInventoryByName(inventoryname)
        LogMessage("debug", "Creating host {host} in inventory {inventory}.".format(host=hostname, inventory=inventoryname))
        jsonData = { "name": hostname, "description": "", "enabled": True, "instance_id": "", "variables": "" }
        self.Connection.Endpoint="/inventories/{id}/hosts/".format(id=inventory_id)
        retVal = self.Connection.Post(json.dumps(jsonData))

    def DeleteHost(self, host_id):
        print("Delete host_id {hid}.".format(hid=host_id))
        self.Connection.Endpoint = '/hosts/{id}/'.format(id=host_id)
        jsonData = { "id": host_id }
        retVal = self.Connection.Delete(json.dumps(jsonData))

    def GetInventoryByName(self, inventory_name):
        for inventory in self.NonSmartInventories:
            if inventory["name"] == inventory_name:
                return inventory["id"]
        return false

    def GetNonSmartInventoryNames(self):
        retval = list()
        for inventory in self.NonSmartInventories:
            retval.append(inventory["name"])
        return retval

    def GetInventoriesForHost(self, hostname):
        # Use the AWX API to get a list of all inventories based on a specified hostname.
        # Return format:
        #    A list containing entries of ["host_id", "inventory_id", "inventory_name"] entries
        # Inventory type is not available at this endpoint, so this list will include all smart/constructed inventories that the node belongs to as well as all standard ones.
        LogMessage("debug", "Getting inventory membership for {host}".format(host=hostname))

        # Set the API endpoint
        self.Connection.Endpoint = '/hosts'

        # Run a HTTP Get to fetch all hosts known to AWX in all inventories
        allHostData = self.Connection.Get()

        if allHostData == None:
            LogMessage("error", "Return code of the request was not 200. No usable data was returned (GetInventoriesForHost).".format(color=termcolors.Red, clear=termcolors.End))
            sys.exit(1)

        retVal = [] # array to be returned
        
        # For every host returned check if the hostname matches the specified name.
        # If the hostname matches create an array containing host_id, inventory_id, and inventory_name and append it to retVal
        for result in allHostData['results']:
            if result['name'] == hostname:
                retVal.append({ 
                    "host_id": result['id'],
                    "inventory_id": result['summary_fields']['inventory']['id'],
                    "inventory_name": result['summary_fields']['inventory']['name']
                })

        # Processing complete, return
        return retVal

    def GetBaseInventories(self):
        self.Connection.Endpoint = '/inventories'
        inventoryData = self.Connection.Get()

        if inventoryData == None:
            LogMessage("error", "Return code of the request was not 200. No usable data was returned (GetBaseInventories).".format(color=termcolors.Red, clear=termcolors.End))
            sys.exit(1)

        self.SmartInventories = list()
        self.NonSmartInventories = list()
        for result in inventoryData["results"]:
            if result["kind"] != "smart" and result["kind"] != "constructed":
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
    # This class represents the HTTP conneciton to the AWX REST API and implements basic REST client program flow
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
        LogMessage("debug", "Sending HTTP GET for {endpoint}".format(endpoint=self.BaseURL + self.Endpoint))
        response = requests.get( self.BaseURL + self.Endpoint, headers=self.Headers, auth=self.HTTPAuth)
        if response.status_code == 200:
            return response.json()
        else:
            return None

    def Post(self, jsonData):
        LogMessage("debug", "Sending HTTP POST for {endpoint} using supplied JSON data.".format(endpoint=self.BaseURL + self.Endpoint))
        response = requests.post( self.BaseURL + self.Endpoint, headers=self.Headers, auth=self.HTTPAuth, data=jsonData)
        LogMessage("debug", "Response status code for HTTP POST is {code}.".format(code=response.status_code))
        if response.status_code < 200 or response.status_code > 300:
            LogMessage("error", "Unexpected HTTP response code {code} returned from API.".format(code=response.status_code))

    def Delete(self, jsonData):
        LogMessage("debug", "Sending HTTP DELETE for {endpoint} using supplied JSON data.".format(endpoint=self.BaseURL + self.Endpoint))
        response = requests.delete( self.BaseURL + self.Endpoint, headers=self.Headers, auth=self.HTTPAuth, data=jsonData)
        LogMessage("debug", "Response status code for HTTP DELETE is {code}.".format(code=response.status_code))
        if response.status_code < 200 or response.status_code > 300:
            LogMessage("error", "Unexpected HTTP response code {code} returned from API.".format(code=response.status_code))

    def ToString(self):
        return '''    BaseUrl: {baseUrl}
    Endpoint: {endpoint}'''.format(baseUrl=self.BaseURL, endpoint=self.Endpoint)

if __name__ == '__main__':
    validActions = ['create', 'update', 'delete']
    # Parse arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-n', '--name', help='Name of a host to perform an action on. Supports globs such as lc02g[01-30]', action="store")
    argParser.add_argument('-i', '--inventory', help='Name of an inventory to perform an action on. Can be used repeatedly.', nargs="+", action="append")
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
        elif "[" in args.name:
            # We have received a glob from the user, parse it into a list
            hostnameList = ExpandGlob(args.name)
        else:
            hostnameList = [ args.name, ]


        inventoryList = []
        if args.action == 'create':
            if args.inventory != None:
                for item in args.inventory:
                    if IsValidInventoryName(item[0], API.NonSmartInventories):
                        LogMessage("debug", "The supplied inventory name  '{name}' is a valid non-smart inventory.".format(name=item[0]))
                        inventoryList.append(item[0])
                    else:
                        LogMessage("error", "The supplied inventory name  '{name}' is a not a valid non-smart inventory.".format(name=item[0]))
                        sys.exit(1)
            else:
                LogMessage("debug", "Action is create and no valid inventory was specified in the command. Prompting for selection.")
                inventoryList = PromptSelectFromList("Select all inventories to create the host(s) in:", [ inventory['name'] for inventory in API.NonSmartInventories ])
            
            LogMessage("info", "Creating {nHosts} hosts in {nInventories} inventories.".format(nHosts=len(hostnameList), nInventories=len(inventoryList)))

            for thisHostname in hostnameList:
                for thisInventory in inventoryList:
                    LogMessage("debug", "Creating '{host}' in inventory '{inventory}'.".format(host=thisHostname, inventory=thisInventory))
                    API.CreateHostInInventory(thisHostname, thisInventory)
        elif args.action == 'delete':
            for thisHost in hostnameList:
                thisHostInventories = API.GetInventoriesForHost(thisHost)
                if len(thisHostInventories) == 0:
                    LogMessage("warning", "No inventory membership is known for {host}.".format(host=thisHost))
                    continue
                
                # The returned data may include membership in constructed inventories.
                # Membership in these inventories is inherited by filters in AWX.
                # Hosts cannot be manually added/removed from constructed inventories.
                # Trim the returned data to only include basic inventories.

                inventoryList = [] # Holds inventory names for presentation to users
                for thisHostInventory in thisHostInventories:
                    if IsValidInventoryName(thisHostInventory['inventory_name'], API.NonSmartInventories) == False:
                        thisHostInventories.remove(thisHostInventory) # Remove any constructed inventories
                    else:
                        inventoryList.append(thisHostInventory) # Append name to the list to be presented to the user

                inventoriesToRemoveFrom = PromptSelectFromList("Mark all inventories to remove {host} from.".format(host=thisHost), inventoryList)

                # Iterate through all selected inventories to remove this host from
                # Make a new 
                for i in inventoriesToRemoveFrom:
                    API.DeleteHost(i['host_id'])
                    
