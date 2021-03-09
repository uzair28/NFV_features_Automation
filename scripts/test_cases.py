import json
import os
import sys
import requests
from openstack_functions import *
from numa import *
import argparse
import logging
import subprocess


#filename=time.strftime("%d-%m-%Y-%H-%M-%S")+".log"
#filsename= "logs.log", filemode="w", stream=sys.stdout
logging.basicConfig(level=logging.INFO,  format='%(asctime)s %(levelname)s: %(message)s', stream=sys.stdout)
logging = logging.getLogger("TestCase Logger")


def parse_arguments():
    # parse arguments
    logging.info("Parsing Arguments")
    parser = argparse.ArgumentParser(description='pass settings file, feature and deployment type for test cases')
    parser.add_argument('-s', '--settings',
                        help=' settings file',
                        required=True)
    parser.add_argument('-f', '--feature',
                        help='features enabled in deployment',
                        required=True)
    parser.add_argument('-d', '--deployment',
                        help='deployment type, flex or ceph',
                        required=True)
    parser.add_argument('-o', '--overcloudrc',
                        help='overrcloud rc file',
                        required=True)
    parser.add_argument('-u', '--undercloudrc',
                        help='undercloud rc file',
                        default="~/stackrc", 
                        required=False)
   
    return parser.parse_args()

def read_settings(settings_file):
    #read settings from json file
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as file:
                 data = file.read().replace('\n', '')
            settings= json.loads(data)
        except Exception as e:
            logging.exception("Failed to load settings file \n {}".format(e))
    else:
        logging.exception("File not found")
    return settings
def run_linux_command(command):
    command= subprocess.run([command], shell=True, stdout=subprocess.PIPE)
    output= command.stdout.decode('ascii')
    if not output:
        logging.error("IP NOT FOUND",  stack_info=True)
        raise ValueError("IP Not found")
    return output

def  read_rc_file(rc_file):
    if os.path.exists(os.path.expanduser(rc_file)):
        logging.info("{} file found".format(rc_file))
        #Find and parse ip
        output= run_linux_command("grep OS_AUTH_URL {}".format(os.path.expanduser(rc_file)))
        output= output.split('=')
        ip= output[1][:-6]

        #Find and parse username
        output= run_linux_command("grep OS_USERNAME {}".format(os.path.expanduser(rc_file)))
        output= output.split('=')
        username= output[1].rstrip("\n")

        #Find and parse password
        output= run_linux_command("grep OS_PASSWORD {}".format(os.path.expanduser(rc_file)))
        output= output.split('=')
        password= output[1].rstrip("\n")
        return ip, username, password

    else:
        logging.error("File {} not found".format(rc_file), stack_info=True )
        raise FileNotFoundError ("File {} not found".format(rc_file))
    
def setup_environment(keypair_name, security_group_name, token):
    #Basic Environment Setup
    create_keypair(settings["key_name"],token)
    create_security_group(settings["security_group"],token)
    add_icmp_rule(settings["security_group"],token)
    add_ssh_rule(setstings["security_group"],token)
    create_keypair(settings["key_name"],token)
    image_verify(settings["image"],token)
    flavor_verify(settings["flavor"],token)

def numa_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #Search and create keypair
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network_id = search_and_create_network(neutron_ep, token, settings["network_1_name"], settings["mtu_size"], settings["network_provider_type"], False)  

    #Search and create subnet
    subnet_id= search_and_create_subnet(neutron_ep, token, settings["subnet_1_name"], network_id, settings["subnet_cidr"]) 

    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])

    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))

    numa_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)

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
    except Exception as e:
        logging.exception("error parsing arguments {}".format(e))

    #Validate Arguments
    logging.info("validating arguments")
    if arguments.feature != "numa":
        logging.critical("Invalid Argument {}".format(arguments.feature))
        raise ValueError("Invalid Argument {}".format(arguments.feature))
    if arguments.deployment != "ceph":
        logging.critical("Invalid Argument {}".format(arguments.deployment))
        raise ValueError("Invalid Argument {}".format(arguments.deployment))

    #Read Settings File
    logging.info("reading settings from file")
    settings= read_settings(arguments.settings)

    #Read rc files
    logging.info("reading undercloud stackrc file")
    #undercloud_url, undercloud_username, undercloud_password= read_rc_file(arguments.undercloudrc)
    undercloud_ip, undercloud_username, undercloud_password= read_rc_file(arguments.undercloudrc)
    overcloud_ip, overcloud_username, overcloud_password= read_rc_file(arguments.overcloudrc)

    #Create Endpoints
    keystone_ep= "{}:5000".format(overcloud_ip)
    neutron_ep= "{}:9696".format(overcloud_ip)
    cinder_ep= "{}:8776".format(overcloud_ip)
    nova_ep= "{}:8774".format(overcloud_ip)
    image_ep= "{}:9292".format(overcloud_ip)  
    undercloud_keystone_ep= "{}:5000".format(undercloud_ip)
    undercloud_nova_ep= "{}:8774".format(undercloud_ip)

    #Get undercloud authentication Token
    undercloud_token= get_authentication_token(undercloud_keystone_ep, undercloud_username, undercloud_password)
    logging.info("Successfully authenticated with undercloud") if undercloud_token is not None else logging.error("Authentication with undercloud failed")
    
    #Get overcloud authentication token
    logging.info("auhenticating user")
    token= get_authentication_token(keystone_ep, overcloud_username,overcloud_password)

    #Get Ips of baremetal nodes
    baremetal_nodes_ips= get_baremeta_nodes_ip(undercloud_nova_ep, undercloud_token)
    logging.info("Successfully received baremetal nodes ip addresses")
    res = [val for key, val in baremetal_nodes_ips.items() if "compute1" in key] 

    #Run Test Cases
    if arguments.feature == "numa":
        numa_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 

if __name__ == "__main__":
    main()
