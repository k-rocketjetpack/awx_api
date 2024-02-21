# AWX API Python3 Client
## Description
This is a Python3 client for the [Ansible AWX](https://github.com/ansible/awx) REST API.

There are many features of the AWX Operator that are no longer supported through awx-manage, such as bulk addition of hosts to inventories. I do not need a fully functional REST API that is difficult to configure and use. I hope to provide a simple tool to handle a limited subset of API capabilities through a simple CLI.

## Installation
### Step 1: Clone this repository
### Step 2: Create config.json file with contents:
{
    "protocol": "http" or "https",
    "host": "YOUR_AWX_SERVER_IP_OR_HOSTNAME",
    "port": "YOUR_AWX_SERVER_PORT",
    "api_version": "YOUR_AWX_API_VERSION",
    "username": "YOUR_AWX_USERNAME_HERE",
    "password": "YOUR_AWX_PASSWORD_HERE
}

Verbose output can be enabled by adding a field named "verbose" and setting the value to true in config.json.

## Implementation Status
**Implemented**:
Fetch list of non-smart inventories.
Fetch list of smart inventories.

**In Progress**:
Fetch list of hosts by inventory.
Add a host to an inventory.

## License
GNU GPL v3