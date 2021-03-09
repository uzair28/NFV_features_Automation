from openstack_functions import *
import logging
import paramiko
from hugepages import *
import os
'''
def ssh_into_compute_node(conn, command):
    try:
        user_name = "heat-admin"
        logging.info("Trying to connect with a compute node")
        # ins_id = conn.get_server(server_name).id

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session = ssh_client.connect("192.168.120.215", username="heat-admin", key_filename="/home/osp_admin/.ssh/id_rsa")  # noqa
        logging.info("SSH Session is established")
        logging.info("Running command in a compute node")
        #pdb.set_trace()
        command="grep Huge /proc/meminfo"
        print("**************")
        #stdin, stdout, stderr = ssh_client.exec_command(command)
        #out = stdout.read()
        import subprocess
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output= stdout.read().decode('ascii')
        output= output.split('\n')

        #print(output)
        for property in output:
            line= property.split()
            if line[0] == "Hugepagesize:":
                print(line[1])

        print(type(output))

        #return int(out)
    except Exception as e:
        print("@@@@@")
        print(e)
        logging.error("Unable to ssh into compute node")
        # conn.delete_server(server_name)

def server_build_wait(server_ids):
'''
def parse_vcpus(output): 
    output= output.split('>')
    return output[1][0]

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


def numa_test_case_3(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    '''
    Test Case Step Description:
        a) Create a Numa flavor
        # openstack flavor create --id auto --ram 4096 --disk 40 --vcpus 4 m1.numa
        # openstack flavor set --property "aggregate_instance_extra_specs:pinned"="True" --property "hw:cpu_policy"="dedicated" --property "hw:cpu_thread_policy"="require" m1.numa
        b) Create an instance using NUMA flavor
        c) On Compute node where instance is provisioned run the command virsh dumpxml <instance-id> 
    
    Test Case Expected Outcome:
        a) Numa flavor creation is successful 
        b) Verify if the instance is successfully created on a compute
        c) Verify if the number of vcpus pinned are same as the vcpus in NUMA flavor       
        
    '''
    logging.info("Test Case 3 running")
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)

    #search and create server
    server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)

    #Get Server Host
    host= get_server_host(nova_ep, token, server_id)
    instance_name= get_server_instance_name(nova_ep, token, server_id)
    host= host.split('.')
    command= "sudo cat /etc/libvirt/qemu/{}.xml | grep vcpus".format(instance_name)
    output= ssh_into_node(baremetal_node_ips.get(host[0]), command)
    vcpus= parse_vcpus(output)
    if vcpus== "4":
        logging.info("Test Case Passed")
        return True
    else: 
        logging.error("Test Case Failed")
        return False










   # result= hugepage_test_case_1("nova_ep", "neutron_ep", "glance_ep", "token", "settings", baremetal_node_ips)
   # print(result)
    #result= hugepage_test_case_2("nova_ep", "neutron_ep", "glance_ep", "token", "settings", baremetal_node_ips)
   # print(result)








