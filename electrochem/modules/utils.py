from pkg_resources import parse_version
import requests
from requests.exceptions import HTTPError
import json
from numpy import round, isnan
import re
import modules.errors as errors

#Description: a safe rounding function
def safeRound(x, dec):
    try:
        rounded = round(x, dec)
        if isnan(x):
            return None
        else:
            return rounded
    except Exception:
        return x
# Description: Gets version data from Github
def compareVersion(version):
    try:
        response = requests.get(
        'https://api.github.com/repos/vince-wu/arbin_echem_tools/releases/latest'
        )
        json_response = response.json()
    except HTTPError:
        json_response = None
    except Exception:
        json_response = None
    if json_response:
        newestVersion = json_response['tag_name']
        newestVersionNumber = re.sub('[^0-9,.]','',newestVersion)
        if parse_version(version) == parse_version(newestVersionNumber):
            print('This program is up to date!')
            return 0
        elif parse_version(version) < parse_version(newestVersionNumber):
            return -1
        elif parse_version(version) > parse_version(newestVersionNumber):
            return 1
            print('Your program version is out of date! Please download the latest version from \
https://github.com/vince-wu/electrochemical-parsing/releases/latest.')

# Description gets the active mass of cathode material
def getActiveMass(mass, ACBratio):
    try:
        if not ACBratio:
            ratio = 1
        else:
            vals = [int(x) for x in ACBratio.split(':')]
            ratio = vals[0]/sum(vals)
    except Exception:
        raise errors.ratioError
    return ratio*mass