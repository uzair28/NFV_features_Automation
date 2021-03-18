import json
import os
import sys
import requests
from openstack_functions import *
from numa import *
import argparse
import logging
import subprocess
from ovsdpdk import*
import time
from sriov import *


#filename=time.strftime("%d-%m-%Y-%H-%M-%S")+".log"
#filsename= "logs.log", filemode="w", stream=sys.stdout
#logging.basicConfig(level=logging.INFO,  format='%(asctime)s %(levelname)s: %(message)s', stream=sys.stdout)
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename= "logs/"+time.strftime("%d-%m-%Y-%H-%M-%S")+".log",
                    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
#logging = logging.getLogger("TestCase Logger")
logging.getLogger().addHandler(console)


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
def ssh_into_node(host_ip, command):
    try:
        user_name = "heat-admin"
        logging.info("Trying to connect with node {}".format(host_ip))
        # ins_id = conn.get_server(server_name).id
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session = ssh_client.connect(host_ip, username="heat-admin", key_filename="/home/osp_admin/.ssh/id_rsa")  # noqa
        logging.info("SSH Session is established")
        logging.info("Running command in a compute node")
        stdin, stdout, stderr = ssh_client.exec_command(command)
        logging.info("command {} successfully executed on compute node {}".format(command, host_ip))
        output= stdout.read().decode('ascii')
        return output
    except Exception as e:
        logging.exception(e)
        logging.error("error ocurred when making ssh connection and running command on remote server") 
    finally:
        ssh_client.close()
        logging.info("Connection from client has been closed")  

def numa_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #Search and create keypair
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network_id = search_and_create_network(neutron_ep, token, settings["network_1_name"], settings["mtu_size"], settings["network_provider_type"], False)  

    #Search and create subnet
    subnet_id= search_and_create_subnet(neutron_ep, token, settings["subnet_1_name"], network_id, settings["subnet_cidr"]) 
    router_id= search_router(neutron_ep, token, "testing_router")
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        router_id= create_router(neutron_ep, token, "testing_router", public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet_id)

    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass

    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    passed=failed=0
    
    t3= numa_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t3 == True:
        t3= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t3="Failed"
    
  
    #numa_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    
    t6= numa_test_case_6(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t6 == True:
        t6= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t6="Failed"
    
    t7= numa_test_case_7(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    
    t8= numa_test_case_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"
    
    t10= numa_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    
    t11= numa_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t11 == True:
        t11= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t11="Failed"
    

    #numa_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)

    print("------------------------")
    print("Numa Test Cases")
    print("Test Cases Passed: {}".format(passed))
    print("Test Cases Failed: {}".format(failed))
    print("Test Case 3: {}".format(t3))
    print("Test Case 6: {}".format(t6))
    print("Test Case7: {}".format(t7))
    print("Test Case 8: {}".format(t8))
    print("Test Case 10: {}".format(t10))
    print("Test Case 11: {}".format(t11))
def hugepages_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #Search and create keypair
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network_id = search_and_create_network(neutron_ep, token, settings["network_1_name"], settings["mtu_size"], settings["network_provider_type"], False)  

    #Search and create subnet
    subnet_id= search_and_create_subnet(neutron_ep, token, settings["subnet_1_name"], network_id, settings["subnet_cidr"]) 
    router_id= search_router(neutron_ep, token, "testing_router")
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        router_id= create_router(neutron_ep, token, "testing_router", public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet_id)

    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass

    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    passed=failed=0
    
    t1= hugepages_test_case_1(baremetal_nodes_ips)
    if t1 == True:
        t1= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t1="Failed"

    t2= hugepages_test_case_2(baremetal_nodes_ips)
    if t2 == True:
        t2= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t2="Failed"
    
    t3= hugepages_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t3 == True:
        t3= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t3="Failed"
    
    t4= hugepages_test_case_4(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t4 == True:
        t4= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t4="Failed"
    
    t7,t8= hugepages_test_case_7_and_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t7 == True:
        t7= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t7="Failed"
    if t8 == True:
        t8= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t8="Failed"
    
    t9= hugepages_test_case_9(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)

    if t9 == True:
        t9= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t9="Failed"
    
    t10= hugepages_test_case_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t10 == True:
        t10= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t10="Failed"
    
    t11= hugepages_test_case_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t11 == True:
        t11= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t11="Failed"
    
    print("------------------------")
    print("Hugepages Test Cases")
    print("Test Cases Passed: {}".format(passed))
    print("Test Cases Failed: {}".format(failed))
    print("Test Case 1: {}".format(t1))
    print("Test Case 2: {}".format(t2))
    
    print("Test Case 3: {}".format(t3))
    print("Test Case 4: {}".format(t4))
    print("Test Case 7: {}".format(t7))
    print("Test Case 8: {}".format(t8))
    print("Test Case 9: {}".format(t9))
    print("Test Case 10: {}".format(t10))
    print("Test Case 11: {}".format(t11))

def sriov_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #Search and create keypair
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network_id = search_and_create_network(neutron_ep, token, settings["network_1_name"], settings["mtu_size"], settings["network_provider_type"], False)  

    #Search and create subnet
    subnet_id= search_and_create_subnet(neutron_ep, token, settings["subnet_1_name"], network_id, settings["subnet_cidr"]) 

    
    router_id= search_router(neutron_ep, token, "testing_router")
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        router_id= create_router(neutron_ep, token, "testing_router", public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet_id)

    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    logging.info("creating router")
    router_id= search_router(neutron_ep, token, "testing_router")
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        router_id= create_router(neutron_ep, token, "testing_router", public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet_id)

    t7,msg7, t8,msg8= sriov_test_cases_7_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    t10,msg10= sriov_test_cases_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    t11,msg11= sriov_test_cases_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    print("Test case 7 is: ".format(t7))
    print("Test case 7 is: ".format(t8))
    print("Test case 7 is: ".format(t10))
    print("Test case 7 is: ".format(t11))
def ovsdpdk_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips):
    #Search and create keypair
    keypair_public_key= search_and_create_kaypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network_id = search_and_create_network(neutron_ep, token, settings["network_1_name"], settings["mtu_size"], settings["network_provider_type"], False)  

    #Search and create subnet
    subnet_id= search_and_create_subnet(neutron_ep, token, settings["subnet_1_name"], network_id, settings["subnet_cidr"]) 

    #Search and create security group
    security_group_id= search_and_create_security_group(neutron_ep, token, settings["security_group_name"])
    try:
        add_icmp_rule_to_security_group(neutron_ep, token, security_group_id)
        add_ssh_rule_to_security_group(neutron_ep, token, security_group_id)
    except:
        pass
    #search and create image
    image_id= search_and_create_image(image_ep, token, settings["image_name"], "bare", "qcow2", "public", os.path.expanduser(settings["image_file"]))
    logging.info("creating router")
    router_id= search_router(neutron_ep, token, "testing_router")
    if router_id is None:
        public_network_id= public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        router_id= create_router(neutron_ep, token, "testing_router", public_network_id,public_subnet_id )
        add_interface_to_router(neutron_ep, token, router_id, subnet_id)

    passed=failed=0
    '''
    t15= ovsdpdk_test_cases_15(nova_ep, token, settings)
    if t15 == True:
        t15= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t15="Failed"
    
    t18= ovsdpdk_test_cases_18(baremetal_nodes_ips)
    if t18 == True:
        t18= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t18="Failed"
    t22= ovsdpdk_test_cases_22(baremetal_nodes_ips)
    if t22 == True:
        t22= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t22="Failed"

    t25= ovsdpdk_test_case_25(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t25 == True:
        t25= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t25="Failed"
    
    t36= ovsdpdk_test_case_36(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t36 == True:
        t36= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t36="Failed"
    '''
    t43= ovsdpdk_test_cases_43(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t43 == True:
        t43= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t43="Failed"
    '''
    t46= ovsdpdk_test_case_46(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t46 == True:
        t46= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t46="Failed"
    t47= ovsdpdk_test_case_47(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t47 == True:
        t47= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t47="Failed"
    t48= ovsdpdk_test_case_48(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips, keypair_public_key, network_id, subnet_id, security_group_id, image_id)
    if t48 == True:
        t48= "Passed"
        passed=passed+1
    else:
        failed=failed+1
        t48="Failed"
    '''
    print("------------------------")
    print("OVSDPDK Test Cases")
    print("Test Cases Passed: {}".format(passed))
    print("Test Cases Failed: {}".format(failed))
    print("Test Case 15: {}".format(t15))
    print("Test Case 18: {}".format(18))
    print("Test Case 22: {}".format(t22))
    print("Test Case 25: {}".format(t25))
    print("Test Case 36: {}".format(t36))
    print("Test Case 43: {}".format(t43))
    print("Test Case 46: {}".format(t46))
    print("Test Case 47: {}".format(t47))
    print("Test Case 48: {}".format(t48))
  
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
    if not(arguments.feature == "numa" or  arguments.feature == "hugepages" or arguments.feature == "ovsdpdk" or arguments.feature == "sriov"):
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
    if arguments.feature == "hugepages":
        hugepages_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "ovsdpdk":
        ovsdpdk_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    if arguments.feature == "sriov":
        sriov_test_cases(nova_ep, neutron_ep, image_ep, token, settings, baremetal_nodes_ips) 
    

if __name__ == "__main__":
    main()
