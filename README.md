# AWX API Python3 Client
## Description
This is a Python3 client for the [Ansible AWX](https://github.com/ansible/awx) REST API.

There are many features of the AWX Operator that are no longer supported through awx-manage, such as bulk addition of hosts to inventories. I do not need a fully functional REST API that is difficult to configure and use. I hope to provide a simple tool to handle a limited subset of API capabilities through a simple CLI.

## Installation
### Step 1: Clone this repository
### Step 2: Create auth.json file with contents:
{
    "username": "YOUR_AWX_USERNAME_HERE",
    "password": "YOUR_AWX_PASSWORD_HERE
}

## License
GNU GPL v3