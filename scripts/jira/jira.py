#!/usr/local/bin/python

import sys
import requests
from requests.auth import HTTPBasicAuth
import json


auth = HTTPBasicAuth("1", "2")


if __name__ == "__main__":
  print(sys.argv)
  print("Hello World")