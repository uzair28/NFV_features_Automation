from openstack_functions import *
import logging
import paramiko
from hugepages import *
import os
from numa import *
from test_cases import *
import time
import math

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

def server_build_wait(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            print(status)
            if not (status == "active" or status=="error"):
                logging.info("Waiting for server/s to build")
                flag=1
                time.sleep(10)
        if flag==0:
            break
def ssh_conne(server1, server2, settings):
    results=[]
    client= paramiko.SSHClient()
    paramiko.AutoAddPolicy()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server1, port=22, username="centos", key_filename=os.path.expanduser(settings["key_file"]))
    response = os.system("ping -c 3 " + server2)
    #and then check the response...
    if response == 0:
        logging.info ("Ping successfull!")
        return True
    else:
        logging.info ("Ping failed")
        return False

def parse_hugepage_size(huge_page_info, parameter):
    huge_page_info= huge_page_info.split('\n')
    for property in huge_page_info:
        line= property.split()
        if line[0] == parameter:
           return line[1]


def sriov_test_cases_7_8(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 7 and 8 running")
    isPassed7=isPassed8= False
    message7=message8=""
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    #search and create server
    port_id, port_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
    print("Port Ip is: {}  port id is {}".format(port_id, port_ip))
    server_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  port_id, "sriov", security_group_id)
    server_build_wait(nova_ep, token, [server_id])
    status= check_server_status(nova_ep, token, server_id)
    if  status == "active":
        isPassed7==True
        message7="Instance Created Successfully and its status is: {}".format(status)
        public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        flaoting_ip, floating_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_ip, port_id)
        logging.info("Waiting for server to boot")
        time.sleep(240)
        try:
            result= ssh_conne(flaoting_ip, "8.8.8.8", settings)
            print("rslt is {}".format(result))
            if result==True:
                isPassed8==True
                logging.info("Testcase 7 passed")
                message8="Successfully ssh into instance using keypair {}".format(status)
            else: 
                logging.error("Test Case 8 failed")
                message8="ssh into instance failed using keypair {}".format(status)
        except Exception as e:
            logging.error("Test Case 8 failed")
            message8="ssh into instance failed using keypair {}".format(status)
            logging.exception(e)
            pass
            
    else:
        logging.error("Test case 7 failed")
        message7="Instance Creation Failed its status is: {}".format(status)
    
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    logging.info("deleting port")
    time.sleep(10)
    delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_id), token)
    delete_resource("{}/v2.0/floatingips/".format(neutron_ep,floating_ip_id), token)
    time.sleep(2)
    
    return isPassed7, message7, isPassed8, message8


def sriov_test_cases_10(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 10 running")
    isPassed10= False
    message10=""
    compute0= settings["compute0_name"]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    #search and create server
    port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
    port_2_id, port_2_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_2" )
    server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "sriov", security_group_id, compute0)
    server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "sriov", security_group_id, compute0)
    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
    if  status1 == "error" and  status2 == "error":
        logging.error("Test Case 10 failed")
        logging.error("Instances creation failed")
        message10="Both instances can not ping eachother on same compute node same network because one of the instance is failed"
    else:
        public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
        flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_2_ip, port_2_id)

        logging.info("Waiting for server to boot")
        time.sleep(240)
        print("Server 1 ip: {}".format(flaoting_1_ip))
        print("Server 2 ip: {}".format(flaoting_2_ip))
        try:
            logging.info("ssh into server1")
            result1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            print("result 1 is: ".format(result1))
            logging.info("ssh into server2")
           
            result2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            print("result 1 is: ".format(result2))
            if result1==True and result2== True:
                isPassed10==True
                logging.info("Testcase 10 passed")
                message10="Both instances successfully pinged eachother on same compute node same network"
            else: 
                logging.error("Test Case 10 failed")
                message10="Both instances successfully pinged eachother on same compute node same network"
        except Exception as e:
            print(e)
            logging.error("Test Case 10 failed")
            message10="Both instances successfully pinged eachother on same compute node same network"
            logging.exception(e)
            pass
           
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
    logging.info("deleting port")
    time.sleep(10)
    delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
    delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
    logging.info("releasing ip")
    delete_resource("{}/v2.0/floatingips/".format(neutron_ep, floating_1_ip_id), token)
    delete_resource("{}/v2.0/floatingips/".format(neutron_ep, floating_2_ip_id), token)
    time.sleep(2)
    return isPassed10, message10
    
def sriov_test_cases_11(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):  
    logging.info("SRIOV Test Case 11 running")
    isPassed11= False
    message11=""
    compute0= settings["compute0_name"]
    compute1= settings["compute1_name"]
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 150)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    #search and create server
    port_1_id, port_1_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_1" )
    port_2_id, port_2_ip= create_port(neutron_ep, token, network_id, subnet_id, "test_case_port_2" )
    server_1_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server1", image_id, settings["key_name"], flavor_id,  port_1_id, "sriov", security_group_id, compute0)
    server_2_id= search_and_create_sriov_server(nova_ep, token, "test_case_Server2", image_id, settings["key_name"], flavor_id,  port_2_id, "nova1", security_group_id, compute1)
    server_build_wait(nova_ep, token, [server_1_id, server_2_id])
    status1= check_server_status(nova_ep, token, server_1_id)
    status2= check_server_status(nova_ep, token, server_2_id)
    if  status1 == "error" and  status2 == "error":
        logging.error("Test Case 11 failed")
        logging.error("Instances creation failed")
        message10="Both instances can not ping eachother on different compute node same network, because one of the instance is failed"
    else:
        public_network_id= search_network(neutron_ep, token, "public")
        public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
        flaoting_1_ip, floating_1_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_1_ip, port_1_id)
        flaoting_2_ip, floating_2_ip_id= create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, port_2_ip, port_2_id)
        logging.info("Waiting for server to boot")
        time.sleep(240)
        print("Server 1 ip: {}".format(flaoting_1_ip))
        print("Server 2 ip: {}".format(flaoting_2_ip))
        try:
            logging.info("ssh into server1")
            result1= ssh_conne(flaoting_1_ip, flaoting_2_ip, settings)
            print("result 1 is: ".format(result1))
            logging.info("ssh into server2")
           
            result2= ssh_conne(flaoting_2_ip, flaoting_1_ip, settings)
            print("result 1 is: ".format(result2))
            if result1==True and result2== True:
                isPassed11==True
                logging.info("Testcase 11 passed")
                message11="Both instances successfully pinged eachother on different compute node same network"
            else: 
                logging.error("Test Case 11 failed")
                message11="Both instances successfully pinged eachother on different compute node same network"
        except Exception as e:
            print(e)
            logging.error("Test Case 11 failed")
            message11="Both instances successfully pinged eachother on different compute node same network"
            logging.exception(e)
            pass
           
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_1_id), token)
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_2_id), token)
    logging.info("deleting port")
    time.sleep(10)
    delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_1_id), token)
    delete_resource("{}/v2.0/ports/{}".format(neutron_ep,port_2_id), token)
    logging.info("releasing ip")
    delete_resource("{}/v2.0/floatingips/".format(neutron_ep, floating_1_ip_id), token)
    delete_resource("{}/v2.0/floatingips/".format(neutron_ep, floating_2_ip_id), token)
    time.sleep(2)
    
    return isPassed11, message11    


