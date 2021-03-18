from openstack_functions import *
import logging
import paramiko
from hugepages import *
import os
from hugepages import*
import math
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
        c) On Compute node where instance is provisioned run the command sudo cat /etc/libvirt/qemu/<instance-id>.xml | grep vcpus 
    
    Test Case Expected Outcome:
        a) Numa flavor creation is successful 
        b) Verify if the instance is successfully created on a compute
        c) Verify if the number of vcpus pinned are same as the vcpus in NUMA flavor       
    '''
    logging.info("Test Case 3 running")
    isPassed= False
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 10)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)

    #search and create server
    server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_id])  
    if(check_server_status(nova_ep, token, server_id)== "active"):
    #Get Server Host
        host= get_server_host(nova_ep, token, server_id)
        instance_name= get_server_instance_name(nova_ep, token, server_id)
        host= host.split('.')
        command= "sudo cat /etc/libvirt/qemu/{}.xml | grep vcpus".format(instance_name)
        output= ssh_into_node(baremetal_node_ips.get(host[0]), command)
        vcpus= parse_vcpus(output)
        if vcpus== "4":
            logging.info("Numa Test Case 3 Passed")
            isPassed= True
        else: 
            logging.error("Numa Test Case 3 Failed")
    else:
        logging.error("Server creation failed")
        logging.error("Numa Test Case 3 Failed")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed
    
def numa_test_case_5(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    compute_node= settings["compute0_name"]
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    
    server_ids=[]
    cpu_cores= int(settings["compute0_cores"])
    instance_possible=  math.floor(cpu_cores/4)
    for instance in range (0, instance_possible):
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node )
        server_ids.append(server_id)
    server_build_wait(nova_ep, token, server_ids)


    if(check_server_status(nova_ep, token, server_ids[0])== "active" and check_server_status(nova_ep, token, server_ids[1])=="active" and check_server_status(nova_ep, token, server_ids[2])== "error"):
        isPassed= True
        logging.info("Numa testcase 6 passed")
    else:
        logging.info("Numa testcase 6 failed")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)

    return isPassed




def numa_test_case_6(nova_ep, neutron_ep, image_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute_node= settings["compute0_name"]
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 20, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_ids=[]
    cpu_cores= int(settings["compute0_cores"])
    instance_possible=  math.floor(cpu_cores/20)
    for instance in range (0, instance_possible):
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node )
        server_ids.append(server_id)
    server_build_wait(nova_ep, token, server_ids)
    flag=True
    for i in range (0,instance_possible-1):
        status= check_server_status(nova_ep, token, server_ids[i])
        if(status != "active"):
            flag== False

    status= check_server_status(nova_ep, token, server_ids[instance_possible-1])
    if (status=="error" and flag==True):
        isPassed= True
        logging.info("Numa testcase 6 passed")
    else:
        logging.info("Numa testcase 6 failed")
    
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    for server_id in server_ids:   
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(20)
    return isPassed
def numa_test_case_7(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute_node= settings["compute0_name"]
    flavor_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_ids=[]
    for i in range (0,2):
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(i), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node)
        server_ids.append(server_id)
    server_build_wait(nova_ep, token, server_ids) 
    instance_1_name= get_server_instance_name(nova_ep, token, server_ids[0])
    output1= ssh_into_node(settings["compute0_ip"], " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_1_name))
    output1= output1.split("'")
    output1= output1[1].split(",")

    instance_2_name= get_server_instance_name(nova_ep, token, server_ids[1])
    output2= ssh_into_node(settings["compute0_ip"], " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_2_name))
    output2= output2.split("'")
    output2= output2[1].split(",")
    logging.info("VCPU for instance 1 are: {}".format(output1))
    logging.info("VCPU for instance 2 are: {}".format(output2))
    validate = [i for i in output1 if i in output2]
    if not validate:
        logging.info("Numa Testcase 7 passed")
        isPassed= True
    else: 
        logging.error("Numa Testcase 7 failed") 
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[0]), token)
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[1]), token)
    time.sleep(10)
    return isPassed
    
def numa_test_case_8(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed= False
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute_node= settings["compute0_name"]
    flavor_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_ids=[]
    for i in range (0,2):
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(i), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node)
        server_ids.append(server_id)
    server_build_wait(nova_ep, token, server_ids) 
    instance_1_name= get_server_instance_name(nova_ep, token, server_ids[0])
    output1= ssh_into_node(settings["compute0_ip"], " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_1_name))
    output1= output1.split("'")
    output1= output1[1].split(",")

    instance_2_name= get_server_instance_name(nova_ep, token, server_ids[1])
    output2= ssh_into_node(settings["compute0_ip"], " sudo cat /etc/libvirt/qemu/{}.xml | grep 'emulatorpin cpuset'".format(instance_2_name))
    output2= output2.split("'")
    output2= output2[1].split(",")
    logging.info("VCPU for instance 1 are: {}".format(output1))
    logging.info("VCPU for instance 2 are: {}".format(output2))
    output_1_even=output_1_odd=output_2_even=output_2_odd=0
    
    for num in output1: 
        if int(num) % 2 == 0: 
            output_1_even += 1
        else: 
            output_1_odd += 1
    for num in output2: 
        if int(num) % 2 == 0: 
            output_2_even += 1
        else: 
            output_2_odd += 1
    if(output_1_even ==0 or output_1_odd==0) and (output_2_even ==0 or output_2_odd==0):
        logging.info("Numa Testcase 8 passed")
        isPassed= True
    else: 
        logging.error("Numa Testcase 8 failed")

    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[0]), token)
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_ids[1]), token)
    time.sleep(10)
    return isPassed


def numa_test_case_10(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    flavor_1_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_1_id, True)
    flavor_2_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_2", 4096, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_2_id, True)
    server_id= search_and_create_server(nova_ep, token, "testcase_server", image_id,settings["key_name"], flavor_2_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_id]) 
    response= resize_server(nova_ep,token, server_id, flavor_1_id)
    if response==(202):
        isPassed= True
        logging.info("Sccessfully Migrated")
        logging.info("Test Case 10 Passed")
    else: 
        logging.info("Migration Failed")
        logging.error("Test Case 10 Failed")
    logging.info("deleting flavors")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed
    
def numa_test_case_11(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute_node= settings["compute0_name"]
    flavor_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 4096, 4, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_id= search_and_create_server(nova_ep, token, "testcase_server", image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node)
    server_build_wait(nova_ep, token, [server_id]) 
    response= migrate_server(nova_ep,token, server_id)
    print(response)
    if response == 202:
        logging.info("Numa Testcase 11 passed")
        isPassed=True
    else:
        logging.error("Numa Testcase 11 failed")

    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed
def numa_test_case_12(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 28, 60)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    server_id= search_and_create_server(nova_ep, token, "test_case_Server1", image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_id])
    server_ip= get_server_ip(nova_ep, token, server_id, settings["network_1_name"])
    logging.info("Server 1 Ip is: {}".format(server_ip))
    server_port= get_ports(neutron_ep, token, network_id, server_ip)
    logging.info("Server 1 Port is: {}".format(server_port))
    public_network_id= search_network(neutron_ep, token, "public")
    public_subnet_id= search_subnet(neutron_ep, token, "external_sub")
    create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
    logging.info("Waiting for server to boot")
    time.sleep(90)
    server_floating_ip= get_server_floating_ip(nova_ep, token, server_id, settings["network_1_name"])
    response = os.system("ping -c 3 " + server_floating_ip)
    if response == 0:
        isPassed= True
        logging.info ("Ping successfull!")
        logging.info("Test Case 12 Passed")
    else:
        logging.info ("Ping failed")
        logging.error("Test Case 12 Failed")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed




