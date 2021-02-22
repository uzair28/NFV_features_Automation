import json
import os
import sys
import requests
from openstack_functions import *
import argparse
import logging

#filename=time.strftime("%d-%m-%Y-%H-%M-%S")+".log"
logging.basicConfig(level=logging.DEBUG, filename= "logs.log", filemode="w", format='%(asctime)s %(levelname)s: %(message)s')
logging = logging.getLogger("TestCase Logger")

def parse_arguments():
    # parse arguments
    logging.info("Parsing Arguments")
    parser = argparse.ArgumentParser(description='Pass settings file, feature and deployment type for test cases')
    parser.add_argument('-s', '--settings',
                        help=' settings file',
                        required=True)
    parser.add_argument('-f', '--feature',
                        help='features enabled in deployment',
                        required=True)
    parser.add_argument('-d', '--deployment',
                        help='deployment type, flex or ceph',
                        required=True)
    return parser.parse_known_args()

def read_settings(settings_file):
    #read settings from json file
    try: os.path.exists(settings_file)
    try:
            with open(settings_file, 'r') as file:
                 data = file.read().replace('\n', '')
            settings= json.loads(data)
    except Exception as e:
            logging.exception("Failed to load settings file")
    except(FileNotFoundError, IOError):
        logging.exception("File not found")
    return settings


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
    try:
        arguments, unknown= parse_arguments()
        if len(unknown) > 0:
            msg = "Invalid argument(s) :"
        for each in unknown:
            msg += " " + each + ";"
        raise AssertionError(msg)
    
    except:
        logging.exception("error parsing arguments")

    #Validate Arguments
    
    logging.info("validating arguments")
    if arguments.feature != "numa":
        logging.critical("Invalid Argument {}".format(arguments.feature))
        raise ValueError("Invalid Argument {}".format(arguments.feature))
    if arguments.deployment != "ceph":
        logging.critical("Invalid Argument {}".format(arguments.feature))
        raise ValueError("Invalid Argument {}".format(arguments.feature))

    #Read Settings File
    logging.info("Reading settings from file")
    settings= read_settings(arguments.settings)

    #Create Endpoints
    keystone_ep= settings["dashboard_ip"]+":5000/v3"
    #neutron_ep=

    #Get Authentication token
    logging.info("athenticationg user")
    token= get_authentication_token(settings["username"], settings["password"], keystone_ep )
    

    #Setup basic Environment


if __name__ == "__main__":
    main()
