import requests
import json
import os
import sys
#from automation_code import *
import argparse

def parse_arguments():
# Verify Arguments
    parser = argparse.ArgumentParser(description='Pass settings file, feature and deployment type for test cases')
    parser.add_argument('-s', '--settings',
                        help=' settings file',
                        required=True)
    parser.add_argument('-f', '--feature',
                        help='features enabled in deplyment',
                        required=True)
    parser.add_argument('-d', '--deployment',
                        help='deployment type, flex or ceph',
                        required=True)
    return parser.parse_args()

def read_settings(settings_file):
    #read settings from json file
    settings=""
    if os.path.exists(settings_file):
        try:
            data=""
            with open(settings_file, 'r') as file:
                 data = file.read().replace('\n', '')
            settings= json.loads(data)

        except Exception as e:
            print("Failed to load settings file")
            print(e)
    else:
        print("File not found!!! Exception Occurred ")
    return settings

def get_authentication_token(username, password, keystone_ep):
    #authenticate user with keystone
    token=""
    payload= {"auth": {"identity": {"methods": ["password"],"password":
                      {"user": {"name": username, "domain": {"name": "Default"},"password": password} }},
                "scope": {"project": {"domain": {"id": "default"},"name": "admin"}}}}
    # Request Api for authentication
    res = requests.post(keystone_ep+'/auth/tokens',
                        headers = {'content-type':'application/json'},
                        data=json.dumps(payload))
    #Validate Response
    if res.ok:
        print("Successfully Authenticated")
        token= res.headers.get('X-Subject-Token')
    else:
        print("Authenticated Failed")
        res.raise_for_status()
    return token

def setup_environment(keypair_name, security_group_name, token):
    #Basic Environment Setup
    create_keypair(settings["key_name"],token)
    create_security_group(settings["security_group"],token)
    add_icmp_rule(settings["security_group"],token)
    add_ssh_rule(settings["security_group"],token)
    create_keypair(settings["key_name"],token)
    image_verify(settings["image"],token)
    flavor_verify(settings["flavor"],token)

def main():
    #Parse Arguments
    arguments= parse_arguments()

    #Validate Arguments
    if arguments.feature != "numa":
        raise ValueError("Invalid Argument "+ arguments.feature)
    if arguments.deployment != "ceph":
        raise ValueError("Invalid Argument "+ arguments.feature)

    #Read Settings File
    settings= read_settings(arguments.settings)

    #Create Endpoints
    keystone_ep= settings["dashboard_ip"]+":5000/v3"
    #neutron_ep=

    #Get Authentication token
    token= get_authentication_token(settings["username"], settings["password"], keystone_ep )
    

    #Setup basic Environment


if __name__ == "__main__":
    main()
