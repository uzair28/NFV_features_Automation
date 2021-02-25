import json
import os
import sys
import requests
from openstack_functions import *
from numa import *
import argparse
import logging

#filename=time.strftime("%d-%m-%Y-%H-%M-%S")+".log"
#filename= "logs.log", filemode="w",
logging.basicConfig(level=logging.INFO,  format='%(asctime)s %(levelname)s: %(message)s', stream=sys.stdout)
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
    return parser.parse_args()

def read_settings(settings_file):
    #read settings from json file
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as file:
                 data = file.read().replace('\n', '')
            settings= json.loads(data)
        except Exception as e:
            logging.exception("Failed to load settings file")
    else:
        logging.exception("File not found")
    return settings


def setup_environment(keypair_name, security_group_name, token):
    #Basic Environment Setup
    create_keypair(settings["key_name"],token)
    create_security_group(settings["security_group"],token)
    add_icmp_rule(settings["security_group"],token)
    add_ssh_rule(setstings["security_group"],token)
    create_keypair(settings["key_name"],token)
    image_verify(settings["image"],token)
    flavor_verify(settings["flavor"],token)

def numa_test_cases(nova_ep, neutron_ep, glance_ep, image_ep, token, settings):
    numa_test_case_3(nova_ep, neutron_ep, glance_ep, image_ep, token, settings)

def main():
   
    #Parse Arguments
    try:
        arguments= parse_arguments()
        #arguments, unknown= parse_arguments()
        #if len(unknown) > 0:
         #   msg = "Invalid argument(s) :"
        #for each in unknown:
         #   msg += " " + each + ";"
        #raise AssertionError(msg)
    except:
        logging.exception("error parsing arguments")

    #Validate Arguments
    
    logging.info("validating arguments")
    if arguments.feature != "numa":
        logging.critical("Invalid Argument {}".format(arguments.feature))
        raise ValueError("Invalid Argument {}".format(arguments.feature))
    if arguments.deployment != "ceph":
        logging.critical("Invalid Argument {}".format(arguments.deployment))
        raise ValueError("Invalid Argument {}".format(arguments.deployment))

    #Read Settings File
    logging.info("Reading settings from file")
    settings= read_settings(arguments.settings)

    #Create Endpoints
    keystone_ep= settings["dashboard_ip"]+":5000/v3"
    neutron_ep= settings["dashboard_ip"]+":9696"
    cinder_ep= settings["dashboard_ip"]+":8776"
    nova_ep= settings["dashboard_ip"]+":8774"
    image_ep= settings["dashboard_ip"]+":9292"
    glance_ep= ""

    #Get Authentication token
    logging.info("auhenticating user")
    token= get_authentication_token(keystone_ep, settings["username"], settings["password"]  )
    print("Token Received:" +token) 
    logging.info("Glance endpoint {}".format(glance_ep))   
    logging.info("Neutron endpoint {}".format(neutron_ep))  
    logging.info("Cinder endpoint {}".format(cinder_ep))  
    logging.info("Nova endpoint {}".format(nova_ep))  

    #Get Undercloud Authentication Token
    undercloud_token= get_authentication_token(settings["undercloud_keystone_ip"], settings["undercloud_username"], settings["undercloud_password"])
    print("undercloud token: {}".format(undercloud_token))
    print("Get VMS")
    
    servers= receive_all_server("http://192.168.120.10:8774", undercloud_token)
    server_ips=[]
    for server in servers["servers"]:
        list= server["name"].split('-')
        server_ip= {list[-2]+list[-1], server["addresses"]["ctlplane"][0]["addr"]}
        server_ips.append(server_ip)
    print("IPSSS")
    print(server_ips)
    print(server_ips["compute0"])



    

    #Run Test Cases
#    if arguments.feature == "numa":
 #       numa_test_cases(nova_ep, neutron_ep, glance_ep, image_ep,token, settings) 

if __name__ == "__main__":
    main()
