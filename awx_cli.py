#!/usr/bin/env python3

import sys
import json
import requests
from requests.auth import HTTPBasicAuth

class AwxAPI:
    def __init__(self, baseUrl):
        self._connection = AwxConnection(baseUrl)
    
    def get_connection(self):
        return self._connection

    def ToString(self):
        return '''AwxAPI Object:
  Connection Information:
{ConnectionInfo}'''.format(ConnectionInfo=self.Connection.ToString())

    Connection = property(get_connection)

class AwxConnection:
    def __init__(self, url):
        self._endpoint = None
        self._baseUrl = url
        self._password = None
        self._username = None

        authFile = open("auth.json")
        authData = json.load(authFile)
        self.Username = authData["username"]
        self.Password = authData["password"]
        authFile.close()

    def get_baseUrl(self):
        return self._baseUrl

    def set_baseUrl(self, value):
        self._baseUrl = value

    def get_endpoint(self):
        return self._endpoint

    def set_endpoint(self, value):
        self._endpoint = value

    def get_username(self):
        return self._username

    def set_username(self, value):
        self._username = value

    def get_password(self):
        return self._password

    def set_password(self, value):
        self._password = value

    BaseUrl = property(get_baseUrl, set_baseUrl)
    Endpoint = property(get_endpoint, set_endpoint)

    def ToString(self):
        return '''    BaseUrl: {baseUrl}
    Endpoint: {endpoint}
    Username: {username}
    Password: {password}'''.format(baseUrl=self._baseUrl, endpoint=self._endpoint, username=self.Username, password=self.Password)

if __name__ == '__main__':
    API = AwxAPI('http://172.28.1.233:31235/api/v2')
    API.Connection.Endpoint = '/'
    print(API.ToString())

