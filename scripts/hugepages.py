from openstack_functions import *
import logging
import paramiko

def ssh_into_node(host_ip, command):
    try:
        user_name = "heat-admin"
        logging.info("Trying to connect with node {}".format(host_ip))
        # ins_id = conn.get_server(server_name).id
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session = ssh_client.connect(host_ip, username="heat-admin", key_filename="/home/stack/.ssh/id_rsa")  # noqa
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

def get_hugepage_size(huge_page_info):
    huge_page_info= huge_page_info.split('\n')
    for property in huge_page_info:
        line= property.split()
        if line[0] == "Hugepagesize:":
           return line[1]

def read_instance_xml(ssh_output):
    return huge_page_size, huge_page_consumption

def hugepage_test_case_1(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_nodes_ips):
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
        huge_page_size= get_hugepage_size(ssh_output)
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

def hugepage_test_case_2(nova_ep, neutron_ep, glance_ep, token, settings, baremetal_nodes_ips):
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
        huge_page_size= get_hugepage_size(ssh_output)
        if huge_page_size != "2048":
            logging.error("Compute node {} do not have 2 MB hugepage size".format(node))
            logging.error("Testcase 2 failed")
            return False
            break
    else:
        logging.error("All compute nodes have 2 MB hugepage size")
        logging.error("Testcase 2 Passed")
        return True

def hugepages_test_case_3(nova_ep, neutron_ep, glance_ep, token, settings):
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
    flavor_id= search_flavor(nova_ep, token, settings["flavor1"])    
    if flavor_id is None:
        flavor_id= create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 40)  
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, mem_page_size= 1048576)
    logging.debug("flavor id is: {}".format(flavor_id))

    #search and create server
    server_1_id= search_server(nova_ep, token, settings["server_1_name"])
    if server_1_id is None:
        server_1_url= create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_1_id= get_server_detail(token, server_1_url)
    logging.debug("Server 1 id: "+server_1_id)

    command= "virsh dumpxml {}".format(server_1_id)
    compute_nodes_ip= ["192.168.10.1", "192123", "44"]
    ssh_output= ssh_into_node("", command)
    huge_page_size, huge_page_consumption= read_instance_xml(ssh_output)
    if huge_page_size != "1GB" and huge_page_consumption != "4gb":
        logging.error("Instance {} do not have hugepage size 1 GB and hugepage consumption 4 GB".format())
        logging.error("Testcase 3 failed")
        return False
    else:
        logging.error("Instance has 1GB hugepage size and 4GB hugepage consumption")
        logging.error("Testcase 3 Passed")
        return True

def hugepages_test_case_4(nova_ep, neutron_ep, glance_ep, token, settings):
    '''
    Test Case Step Description:
        a) Create a flavor and set metadata as 
            #openstack flavor create --id auto --ram 4096 --disk 40 --vcpus 2 m1.hpg 
            #openstack flavor set --property "hw:mem_page_size"="2048" --property "aggregate_instance_extra_specs:hugepages"="True" m1.hpg
        b) Launch an instance using above created flavor
        c) SSH to compute node where instance is created and run the command 
            # virsh dumpxml <instance_name>
            # grep "Huge" /proc/meminfo
    
    Testcase Expected Outcome:
        a) Flavor & Instance creation will be successful
        b) Instance XML will show 2 MB hugepage size and 4 GB consumption of hugepage in /proc/meminfo
        
    '''

    # Search and Create Flavor
    flavor_id= search_flavor(nova_ep, token, settings["flavor1"])    
    if flavor_id is None:
        flavor_id= create_flavor(nova_ep, token, settings["flavor1"], 4096, 2, 40)  
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, False, mem_page_size= 2048)
    logging.debug("flavor id is: {}".format(flavor_id))

    #search and create server
    server_1_id= search_server(nova_ep, token, settings["server_1_name"])
    if server_1_id is None:
        server_1_url= create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_1_id= get_server_detail(token, server_1_url)
    logging.debug("Server 1 id: "+server_1_id)

    command= "virsh dumpxml {}".format(server_1_id)
    compute_nodes_ip= ""
    ssh_output= ssh_into_node("", command)
    huge_page_size, huge_page_consumption= read_instance_xml(ssh_output)
    if huge_page_size != "1GB" and huge_page_consumption != "4gb":
        logging.error("Instance {} do not have hugepage size 2 MB and hugepage consumption 4 GB".format())
        logging.error("Testcase 4 failed")
        return False
    else:
        logging.error("Instance has 2MB hugepage size and 4GB hugepage consumption")
        logging.error("Testcase 4 Passed")
        return True
    
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

def hugepages_test_case_7(nova_ep, neutron_ep, glance_ep, token, settings):
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
    command= "grep Huge /proc/meminfo"
    ssh_output= ssh_into_node("", command)
    huge_page_size= get_hugepage_size(ssh_output)
    instance_possible= huge_page_size/20
    # create falvor
    flavor_id=""

#    for instance in range instance_possible:
 #       search_and_create_instance()
  #      wait_for_insrtances_to_boot():

        










