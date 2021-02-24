from openstack_functions import *
import logging
import paramiko
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

def numa_test_case_3(nova_ep, neutron_ep, glance_ep, token, settings):
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
    flavor_id= search_flavor(nova_ep, token, settings["flavor1"])    
    if flavor_id is None:
        flavor_id= create_flavor(nova_ep, token, settings["flavor1"], 4096, 4, 40)  
        put_extra_specs_in_flavor(nova_ep, token, flavor_id, True)
    logging.debug("flavor id is: {}".format(flavor_id))

    #Search and create keypair
    keypair_public_key= search_keypair(nova_ep, token, settings["key_name"])
    if keypair_public_key is None:
        keypair_public_key= create_keypair(nova_ep, token, settings["key_name"])

    #Search and create network
    network_id= search_network(neutron_ep, token, settings["network_1_name"])    
    if network_id is None:
        network_id =create_network(neutron_ep, token, settings["network_1_name"], settings["mtu_size"], settings["network_provider_type"], False)  
    logging.debug("network id is: {}".format(network_id))

    #Search and create subnet
    subnet_id= search_subnet(neutron_ep, token, settings["subnet_1_name"])    
    if subnet_id is None:
        subnet_id =create_subnet(neutron_ep, token, settings["subnet_1_name"], network_id, settings["subnet_cidr"]) 
    logging.debug("subnet id is: {}".format(subnet_id)) 

    #Search and create security group
    security_group_id= search_security_group(neutron_ep, token, settings["security_group_name"]) 
    if security_group_id is None:
        security_group_id= create_security_group(neutron_ep, token, settings["security_group_name"])
    logging.debug("security group id is: {}".format(subnet_id)) 

    #search and create image
    image_id= search_image(nova_ep, token, settings["image_name"])
    if image_id is None:
        image_id= create_image(nova_ep, token, settings["image_name"], "bare", "qcow2", "public")
        image_file= open(settings["image_file"], 'rb')
        logging.info("Uploading image file")
        upload_file_to_image(nova_ep, token, image_file, image_id)
        logging.debug("image id is: {}".format(image_id))
    #try:
    #   image_file= open(settings["image_file"], "r")
    #except Exception as e:
    #        logging.exception("Failed to load image file")
    
    #search and create server
    server_1_id= search_server(nova_ep, token, settings["server_1_name"])
    if server_1_id is None:
        server_1_url= create_server(nova_ep, token, settings["server_1_name"], image_id,settings["key_name"], flavor_id,  network_id, security_group_id)
        server_1_id= get_server_detail(token, server_1_url)
    logging.debug("Server 1 id: "+server_1_id)

    
    
    #Verify Deployment of HP
    ssh_into_compute_node(token, "")







