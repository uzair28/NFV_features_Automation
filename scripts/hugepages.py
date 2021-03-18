from openstack_functions import *
from test_cases import *
import logging
import paramiko
import time
import math
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
def wait_server_pause(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            if not(status == "paused"):
                logging.info("Waiting for server/s to pause")
                flag=1
                time.sleep(5)
        if flag==0:
            break
def wait_server_suspend(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            print(status)
            if not(status == "suspended"):
                logging.info("Waiting for server/s to suspend")
                flag=1
                time.sleep(5)
        if flag==0:
            break
def wait_server_shutdown(nova_ep, token, server_ids):
    while True:
        flag=0
        for server in server_ids:
            status= check_server_status(nova_ep, token, server)
            print(status)
            if not(status == "stopped"):
                logging.info("Waiting for server/s to stop")
                flag=1
                time.sleep(5)
        if flag==0:
            break

def wait_server_delete(nova_ep, token, server_names):
    while True:
        flag=0
        for server in server_names:
            id= search_server(nova_ep, token, server)
            if(id is not None ):
                logging.info("Waiting for server/s to delete")
                flag=1
                time.sleep(5)
        if flag==0:
            break


def parse_hugepage_size(huge_page_info, parameter):
    huge_page_info= huge_page_info.split('\n')
    for property in huge_page_info:
        line= property.split()
        if line[0] == parameter:
           return line[1]

def read_instance_xml(ssh_output):
    return huge_page_size, huge_page_consumption

def hugepages_test_case_1(baremetal_nodes_ips):
    '''
    Testcase Step Description:
        a) Deploy Jetpack with csp profile and huge page size set to 1 GB
        b) Log into horizon and navigate to host aggregates pages
        c) Run the below commands on all compute nodes
            #grep "Huge" /proc/meminfo 
        d) cat /sys/devices/system/node/node_id/hugepages/hugepages-1048576kB/nr_hugepages
    
    Testcase Expected Outcome:
        a) Deployment will be successful with no error in logs
        b) Host Aggregate page will show a custom aggregate with hugepage properties in metadata
        c) Compute nodes will show 1 GB Hugepage size (1048576 kb)
    '''      
    #Get Huge Pages information from node
    command= "grep Huge /proc/meminfo"
    compute_nodes_ip= [val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    for node in compute_nodes_ip:
        ssh_output= ssh_into_node(node, command)
        huge_page_size= parse_hugepage_size(ssh_output,"Hugepagesize:")
        logging.info("huge page size of compute node {}, is {}".format(node, huge_page_size))
        if huge_page_size != "1048576":
            logging.error("Compute node {} do not have 1 GB hugepage size".format(node))
            logging.error("Testcase 1 failed")
            return False
            break
    else:
        logging.info("All compute nodes have 1 GB hugepage size")
        logging.info("Testcase 1 Passed")
        return True

def hugepages_test_case_2(baremetal_nodes_ips):
    '''
    Testcase Step Description:
        a) Deploy Jetpack with csp profile and huge page size set to 2 MB
        b) Log into horizon and navigate to host aggregates pages
        c) Run the below commands on all compute nodes
            #grep "Huge" /proc/meminfo 
        d) cat /sys/devices/system/node/node_id/hugepages/hugepages-1048576kB/nr_hugepages
    
    Testcase Expected Outcome:
        a) Deployment will be successful with no error in logs
        b) Host Aggregate page will show a custom aggregate with hugepage properties in metadata
        c) Compute nodes will show 2 MB Hugepage size (2048 kb)     
    '''
    
    #Get Huge Pages information from node
    command= "grep Huge /proc/meminfo"
    compute_nodes_ip=[val for key, val in baremetal_nodes_ips.items() if "compute" in key]
    for node in compute_nodes_ip:
        ssh_output= ssh_into_node(node, command)
        huge_page_size= parse_hugepage_size(ssh_output, "Hugepagesize:")
        if huge_page_size != "2048":
            logging.error("Compute node {} do not have 2 MB hugepage size".format(node))
            logging.error("Testcase 2 failed")
            return False
            break
    else:
        logging.error("All compute nodes have 2 MB hugepage size")
        logging.error("Testcase 2 Passed")
        return True

def hugepages_test_case_3(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    '''
    Test Case Step Description:
        a) Create a flavor and set metadata as 
            #openstack flavor create --id auto --ram 4096 --vcpus 2 --disk 40 m1.hpg 
            #openstack flavor set --property "hw:mem_page_size"="1048576" --property "aggregate_instance_extra_specs:hugepages"="True" m1.hpg
        b) Launch an instance using above created flavor
        c) SSH to compute node where instance is created and run the command 
            # virsh dumpxml <instance_name>
            # grep "Huge" /proc/meminfo

    Testcase Expected Outcome:
        a) Flavor & Instance creation will be successfull
        b) Instance XML will show 1 GB hugepage size and 4 GB consumption of hugepage in /proc/meminfo
    '''
    isPassed=False
    # Search and Create Flavor
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)

    #search and create server
    compute_nodes= settings["compute0_name"]
    output= ssh_into_node(settings["compute0_ip"], " grep Huge /proc/meminfo")
    
    hugepg_free_before= parse_hugepage_size(output, "HugePages_Free:")
    server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id, settings["compute0_name"])
    server_build_wait(nova_ep, token, [server_id])  
    if( check_server_status(nova_ep, token, server_id)== "active"):
        host= get_server_host(nova_ep, token, server_id)
        instance_name= get_server_instance_name(nova_ep, token, server_id)
        host= host.split('.')
        command= "sudo cat /etc/libvirt/qemu/{}.xml | grep 'page size'".format(instance_name)
        output= ssh_into_node(baremetal_node_ips.get(host[0]), command)
        output= output.split("'")
        logging.info("Instance hugepage size is: {}".format(output[1]))
        if output[1]=="1048576":
            logging.info("Instance has valid hugepage size")
            output= ssh_into_node(settings["compute0_ip"], " grep Huge /proc/meminfo")
            hugepg_free_after= parse_hugepage_size(output, "HugePages_Free:")
            if (int(hugepg_free_before)- int(hugepg_free_after))==4:
                logging.info("Instance has consumed valid hugepages")
                logging.info("Test case 3 passed")
                isPassed= True
            else:
                 logging.error("instance has consumed invalid hugepages")
                 logging.error("Test case 3 failed")

        else: 
            logging.error("Instance has invalid hugepage size")
            logging.error("Test case 3 failed")
    else:
        logging.error("server build failed")
        logging.error("Test case 3 failed")
    
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed


def hugepages_test_case_4(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    '''
    Test Case Step Description:
        a) Create a flavor and set metadata as 
            #openstack flavor create --id auto --ram 4096 --vcpus 2 --disk 40 m1.hpg 
            #openstack flavor set --property "hw:mem_page_size"="1048576" --property "aggregate_instance_extra_specs:hugepages"="True" m1.hpg
        b) Launch an instance using above created flavor
        c) SSH to compute node where instance is created and run the command 
            # virsh dumpxml <instance_name>
            # grep "Huge" /proc/meminfo
    
    Testcase Expected Outcome:
        a) Flavor & Instance creation will be successfull
        b) Instance XML will show 1 GB hugepage size and 4 GB consumption of hugepage in /proc/meminfo
    '''

    # Search and Create Flavor
    isPassed= False
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 2048)

    #search and create server
    server_id= search_and_create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_id])
    server_status= check_server_status(nova_ep, token, server_id)
    if image_id is not None or server_status == "error":
        logging.info("Image created and server built failed")
        logging.info("Testcase 4 passed")
        isPassed= True
    else:
        logging.info("Image created and server is active")
        logging.error("Testcase 4 Failed ")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed    
    
def hugepages_test_case_6(nova_ep, neutron_ep, glance_ep, token, settings):
    '''
    Test Case Step Description:
        a) SSH to each compute node 
        b) open /var/lib/config-data/nova_libvirt/etc/nova/nova.conf and search scheduler_default_filters

    Testcase Expected Outcome:
    There should be a line in nova.conf as
        "scheduler_default_filters=RetryFilter,AvailabilityZoneFilter,RamFilter,DiskFilter,ComputeFilter,
        ComputeCapabilitiesFilter,ImagePropertiesFilter,ServerGroupAntiAffinityFilter,ServerGroupAffinityFilter,
        CoreFilter,NUMATopologyFilter,AggregateInstanceExtraSpecsFilter"
    '''
    command= "sudo grep enabled_filters /var/lib/config-data/nova_libvirt/etc/nova/nova.conf"
    compute_nodes_ip= ["192.168.10.1", "192123", "44"]
    for node in compute_nodes_ip:
        ssh_output= ssh_into_node("", command)
        ssh_output= ssh_output.read().decode('ascii')
        ssh_output= ssh_output.split('=')
        if ( "RetryFilter" not in ssh_output[1] or "AvailabilityZoneFilter" not in ssh_output[1] or "RamFilter" not in ssh_output[1] or 
                "DiskFilter" not in ssh_output[1] or "ComputeFilter"  not in ssh_output[1] or "ComputeCapabilitiesFilter"  not in ssh_output[1] or 
                "ImagePropertiesFilter" not in ssh_output[1] or "ServerGroupAntiAffinityFilter" not in ssh_output[1] or "ServerGroupAffinityFilter" not in ssh_output[1] or 
                "CoreFilter" not in ssh_output[1] or "NUMATopologyFilter" not in ssh_output[1] or "AggregateInstanceExtraSpecsFilter" not in ssh_output[1]):
            logging.error("nova.conf file is not correctly configured on compute node {}".format(node))
            logging.error("Testcase 6 Failed")
            return False
        else: 
            logging.info("nova.conf file is not correctly configured on all compute nodes")
            logging.info("Testcase 6 Passed")
            return True

def hugepages_test_case_7_and_8(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    '''
    Testcase Step Description:
        a) For a compute with Total Hugepage 180, create a flavor with 20 GB RAM and set metadata as 
            #openstack flavor create --id auto --ram 20480 --disk 40 --vcpus 2 m1.hpg 
            #openstack flavor set --property "hw:mem_page_size"="1048576" --property "aggregate_instance_extra_specs:hugepages"="True" m1.huge
        b) Create 10 instances one by one using the flavor above created on same compute
    
    Testcase Expected Outcome:
        a) Flavor creation will be successful
        b) 9 instances will be successfully created but 10th instance will fail with error 'No valid host was found'
    '''

    isPassed7= isPassed8= False
    compute_nodes = [key for key, val in baremetal_node_ips.items() if "compute" in key]
    compute_node= settings["compute0_name"]
    output= ssh_into_node(settings["compute0_ip"], " grep Huge /proc/meminfo")
    hugepg_free= parse_hugepage_size(output, "HugePages_Free:")
    print(hugepg_free)
    instance_possible= math.floor(int(hugepg_free)/20)
    print(instance_possible)
    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 20480, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)
    server_ids=[]
    try:
        for instance in range (0, instance_possible):
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node )
            server_ids.append(server_id)
    except:
        pass
    server_build_wait(nova_ep, token, server_ids)

    #Check status of instances
    for server_id in server_ids:
        server_status= check_server_status(nova_ep, token, server_id)
        if (server_status)=="error":
            logging.error("server creation failed")
            logging.error("TestCase 7 and 8 failed")
            return False, False
    else:
        logging.info("all servers successfully created")
        try:   
            server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node)
        except:
            logging.info("Test Case 7 and 8 Failed")
            logging.info("deleting flavor")
            delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
            logging.info("deleting all servers")
            for server_id in server_ids:   
                delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
            time.sleep(20)
            pass
            return False
        server_build_wait(nova_ep, token, [server_id])
        server_status= check_server_status(nova_ep, token, server_id)
        if (server_status== "error"):
            logging.info("Test case 7 Passed Successfully")
            isPassed7= True
        
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        
        #pause all instances  
        #Chck when all inastances are paused
        for server_id in server_ids:   
            perform_action_on_server(nova_ep,token, server_id, "pause")
        wait_server_pause(nova_ep, token, server_ids)
        logging.info("all Servers Paused")
        logging.info("again creating server")
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node)
        server_build_wait(nova_ep, token, [server_id])
        server_status= check_server_status(nova_ep, token, server_id)
        if (server_status== "error"):
            logging.info("Server Creation Failed when other servers paused")
            logging.info("Test case 8 passed when other servers are paused")
        logging.info("deleting server")
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        
        logging.info("unpause servers")
        for server_id in server_ids:   
            perform_action_on_server(nova_ep,token, server_id, "unpause")
        server_build_wait(nova_ep, token, server_ids)
        logging.info("All servers unpaused")

    #Check when all instances are suspended
    for server_id in server_ids:   
        perform_action_on_server(nova_ep,token, server_id, "suspend")
    wait_server_suspend(nova_ep, token, server_ids)
    logging.info("all Servers suspended")
    logging.info("again creating server")
    server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node)
    server_build_wait(nova_ep, token, [server_id])
    server_status= check_server_status(nova_ep, token, server_id)
    if (server_status== "error"):
        logging.info("Server Creation Failed when other servers suspended")
        logging.info("Test case 8 passed when other servers are suspended")
    logging.info("deleting server")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
        
    for server_id in server_ids:   
        perform_action_on_server(nova_ep,token, server_id, "resume")
    server_build_wait(nova_ep, token, server_ids)
    logging.info("All servers resumed")

    #Check when all instances are shutdown
    for server_id in server_ids:   
        perform_action_on_server(nova_ep,token, server_id, "os-stop")
    wait_server_shutdown(nova_ep, token, server_ids)
    logging.info("all Servers shutdown")
    logging.info("again creating server")
    server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format((instance_possible+1)), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node)
    server_build_wait(nova_ep, token, [server_id])
    server_status= check_server_status(nova_ep, token, server_id)
    if (server_status== "error"):
        logging.info("Server Creation Failed when other servers shutdown")
        logging.info("Test case 8 passed when other servers are shutdown")
        isPassed8= True

    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    for server_id in server_ids:   
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(20)
    return isPassed7, isPassed8

def hugepages_test_case_9(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    isPassed=False
    flavor_1_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_1", 2048, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_1_id, False, 1048576)

    flavor_2_id= search_and_create_flavor(nova_ep, token, "testcase_flavor_2", 4096, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_2_id, False, 1048576)
    
    server_id= search_and_create_server(nova_ep, token, "testcase_server", image_id,settings["key_name"], flavor_1_id,  network_id, security_group_id)
    server_build_wait(nova_ep, token, [server_id]) 
    response =resize_server(nova_ep,token, server_id, flavor_2_id)
    if response==(202):
        isPassed= True
        logging.info("Sccessfully Migrated")
        logging.info("Test Case 9 Passed")
    else: 
        logging.info("Migration Failed")
        logging.error("Test Case 9 Failed")
    logging.info("deleting flavors")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_1_id), token)
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_2_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed

def hugepages_test_case_10(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
    
    isPassed= False
    compute_node= settings["compute0_name"]
    compute_node_ip= settings["compute0_ip"]

    flavor_id= search_and_create_flavor(nova_ep, token, settings["flavor1"], 22528, 2, 40)
    put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, 1048576)
    ssh_output= ssh_into_node(compute_node_ip, "grep MemTotal: /proc/meminfo")
    print(ssh_output)
    ssh_output=ssh_output.split("       ")
    ssh_output=ssh_output[1].split(" ")
    
    available_ram= int(ssh_output[0])/(1024*1024)
    print(available_ram)
    instance_possible= math.floor(int(available_ram)/22)
    print(instance_possible)
    #ssh_output=ssh_output.strip(" ")
    server_ids=[]
    for instance in range (0, instance_possible):
        server_id= search_and_create_server(nova_ep, token, "testcase_server{}".format(instance), image_id,settings["key_name"], flavor_id,  network_id, security_group_id, compute_node )
        server_ids.append(server_id)
    server_build_wait(nova_ep, token, server_ids)
    successfully_created=0
    for i in range(0,instance_possible):
        status= check_server_status(nova_ep, token, server_ids[i])
        if status=="active":
            successfully_created=successfully_created+1
    if(successfully_created >(instance_possible-2) and successfully_created<instance_possible):
        isPassed= True
        logging.info("servers created according to available memory")
        logging.info("Test Case 10 Passed")
    else:
        logging.info("servers are not created according to available memory")
        logging.info("Test Case 10 Failed")
        logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    for server_id in server_ids:   
        delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(20)
    return isPassed

def hugepages_test_case_11(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_node_ips,  keypair_public_key, network_id, subnet_id, security_group_id, image_id):
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
    time.sleep(10)
    create_floating_ip(neutron_ep, token, public_network_id, public_subnet_id, server_ip, server_port)
    logging.info("Waiting for server to boot")
    time.sleep(90)
    server_floating_ip= get_server_floating_ip(nova_ep, token, server_id, settings["network_1_name"])
    response = os.system("ping -c 3 " + server_floating_ip)
    if response == 0:
        isPassed= True
        logging.info ("Ping successfull!")
        logging.info("Test Case 11 Passed")
    else:
        logging.info ("Ping failed")
        logging.error("Test Case 11 Failed")
    logging.info("deleting flavor")
    delete_resource("{}/v2.1/flavors/{}".format(nova_ep,flavor_id), token)
    logging.info("deleting all servers")
    delete_resource("{}/v2.1/servers/{}".format(nova_ep,server_id), token)
    time.sleep(10)
    return isPassed



    












