import requests
import json
import os



def search_network(neutron_ep, token, network_name):
    network_id= None
    res = requests.get(neutron_ep+'/v2.0/networks',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    if res.ok:
        print("Successfully Received Networks List")
        data= res.json()
        for network in (data["networks"]):
            if network_name in (network["name"]):
                network_id=network["id"]
        else :
            res.raise_for_status()
    return network_id

def create_network(neutron_ep, token, network_name, mtu_size, network_provider_type, is_external):
    #Create Network
    network_id= None
    payload= {
        "network": {
            "name": network_name,
            "admin_state_up": True,
            "mtu": mtu_size,
            "provider:network_type": network_provider_type,
            "router:external": is_external
            }
        }
    res= requests.post(neutron_ep+'/v2.0/networks',
                            headers={'content-type': 'application/json',
                                'X-Auth-Token': token},
                            data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Network "+network_name)
        data= res.json()
        network_id= data['network']['id']
    else :
        res.raise_for_status()
    return network_id

def search_subnet(neutron_ep, token, subnet_name):
    #Search Subnet
    subnet_id= None
    res = requests.get(neutron_ep+'/v2.0/subnets',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    if res.ok:
        data= res.json()
        for subnet in (data["subnets"]):
            if subnet_name in (subnet["name"]):
                print("Subnet"+ (subnet["name"]) +" already exists")
                subnet_id= subnet["id"]
    else: 
        res.raise_for_status()
    return subnet_id

def create_subnet(neutron_ep, token, subnet_name, network_id, cidr):
    #creating Subnet
    subnet_id= None
    payload= {
        "subnet": {
            "name": subnet_name,
            "network_id": network_id,
            "ip_version": 4,
            "cidr": cidr
            }
        }
    
    res = requests.post(neutron_ep+'/v2.0/subnets',
                            headers={'content-type': 'application/json',
                                'X-Auth-Token': token},
                            data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Subnet  "+ (subnet_name))
        data= res.json()
        subnet_id= data['subnet']['id']
    else :
        res.raise_for_status()
    return subnet_id

def create_subnet(neutron_ep, token, subnet_name, network_id, cidr, gateway, pool_start, pool_end):
    subnet_id= None
    payload= {"subnet":
              {"network_id": network_id,
              "ip_version": 4,
              "cidr": cidr,
               "name": subnet_name,
               "enable_dhcp": "true",
               "gateway_ip": gateway,
               "allocation_pools": [{"start": pool_start, "end": pool_end}]
              }
              }
    res = requests.post(neutron_ep+'/v2.0/subnets',
                            headers={'content-type': 'application/json',
                                'X-Auth-Token': token},
                            data=json.dumps(payload))
    if res.ok:
        print("Successfully Created External Subnet  "+ (subnet_name))
        data= res.json()
        subnet_id= data['subnet']['id']
    else :
            res.raise_for_status()
    return subnet_id

def search_flavor(nova_ep, token, flavor_name):
    # List flavors
    flavor_id= None
    res = requests.get(nova_ep+'/v2/flavors',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    if res.ok:
        data= res.json()
        for flavor in (data["flavors"]):
            if flavor in (flavor["name"]):
                flavor_id= flavor["id"]
    else:
        res.raise_for_status()
    return flavor_id

def create_flavor(nova_ep, token, flavor_name, flavor_ram, flavor_vcpus, flavor_disks):
    # Create Flavora
    flavor_id= None
    payload={
        "flavor": {
            "name": flavor_name,
            "ram":  flavor_ram,
            "vcpus": flavor_vcpus,
            "disk": flavor_disks,
            "rxtx_factor" : "1",
            "os-flavor-access:is_public": "true"
        }
    }
    res = requests.post(nova_ep+'/flavors',
                    headers={'content-type': 'application/json',
                             'X-Auth-Token':  token},
                    data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Flavor "+ flavor_name)
        data= res.json()
        flavor_id= data['flavor']['id']
    else :
        res.raise_for_status()
    return flavor_id

def put_extra_specs_in_flavor(nova_ep, token, flavor_id, mem_page_size):
    payload={
        "flavor": {
           "extra_specs": {
                "hw:numa_nodes": "1",
                "hw:cpu_policy": "dedicated",
                "hw:cpu_thread_policy": "require",
                "hw:mem_page_size": mem_page_size,
                "quota:cpu_quota": "10000",
                "quota:cpu_period": "20000",
                "hw:cpu_policy": "dedicated",
                "hw:cpu_thread_policy": "require",
                "hw:numa_nodes": "1",
                "aggregate_instance_extra_specs:hugepages": "True"
            }
        }
    }
    res = requests.put(nova_ep+'/flavors/'+flavor_id,
                    headers={'content-type': 'application/json',
                             'X-Auth-Token':  token},
                    data=json.dumps(payload))
    if res.ok:
        print("Successfully Added Extra specs to  Flavor "+ flavor_id)
    else :
        res.raise_for_status()



def create_router(neutron_ep, token, router_name):
    router_id= None
    payload={"router":
        {"name": router_name,
        "admin_state_up":" true",
        }
        }
    res = requests.post(neutron_ep+'/v2.0/routers',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))

    if res.ok:
        print("Successfully Created Router "+router_name)
        data= res.json()
        router_id= data['router']['id']
    else :
        res.raise_for_status()
    return router_id

def search_security_group(neutron_ep, token, security_group_name):
    security_group_id= None
    res = requests.get(neutron_ep+"/v2.0/security-groups",
                    headers={'content-type': 'application/json',
                             'X-Auth-Token':  token })
    if res.ok:
        print("Successfully Received Security Group List")
        data= res.json()
        for security_group in data["security_groups"]:
            if security_group["name"] == security_group_name:
                print("Security Group Already Exists")
                security_group_id= security_group["id"]
    else :
        res.raise_for_status()
    return security_group_id


def create_security_group(neutron_ep, token, security_group_name):
    security_group_id= None
    payload= {
    "security_group": {
        "name": security_group_name,
    }
    }
    res = requests.post(neutron_ep+'/v2.0/security-groups',
                  headers={'content-type': 'application/json',
                            'X-Auth-Token':  token},
                data= json.dumps(payload))

    if res.ok:
        print("Successfully Created Security Group "+security_group_name)
        data= res.json()
        security_group_id= data["security_group"]["id"]
    else :
        res.raise_for_status()

    return security_group_id

def add_rule_to_security_group(neutron_ep, token, security_group_id, direction, ip_version, protocol, min_port, max_port):
    payload= {"security_group_rule":{
            "direction": direction,
            "ethertype":ip_version,
            "remote_ip_prefix": "0.0.0.0/0",
            "protocol": protocol,
            "security_group_id": security_group_id,
            "port_range_min": min_port,
            "port_range_max": max_port
        }
    }
    res = requests.post(neutron_ep+'/v2.0/security-group-rules',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token},
                data= json.dumps(payload)
                )
    if res.ok:
        print("Successfully added ICMP rule to Security Group ")
    else :
        res.raise_for_status()
    ### i = next((elem for elem in my_list if elem == 'two'), None)

def search_keypair(neutron_ep, token, keypair_name):
    
    res = requests.get(nova_ep+'/os-keypairs',
                    headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   })                   
    if res.ok:
        print("Successfully Received Flavours List")
        data= res.json()
        for keypair in data["keypairs"]:
            if keypair["keypair"]["name"] == keypair_name:
                keypair_key= keypair["keypair"]["public_key"]
                print("KeyPair "+keypair_name+" Already Exists")
        
    else:
        res.raise_for_status()

def create_keypair(nova_ep, token, keypair_name):
    public_key= None
    payload={"keypair":
        {"type": "ssh",
        "name": keypair_name
        }
        }
    res = requests.post(nova_ep+'/os-keypairs',
                 headers={'content-type': 'application/json',
                            'X-Auth-Token':  token},
                data= json.dumps(payload))
    if res.ok:
        print("Successfully Created Keypair")
        data= res.json()
        public_key= data["keypair"]["public_key"]
        
    else :
        res.raise_for_status()
    
    return public_key

def search_image(glance_ep, token, image_name):
    # Get Images
    image_id= None
    res = requests.get(glance_ep+'/v2/images',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    if res.ok:
        data= res.json()
        for image in (data["images"]):
            if image in (data["name"]):
                image_id= data["id"]
                print("image",(image["name"]) +" already exists")
    else:
        res.raise_for_status()
    return image_id
def create_image(glance_ep, token, image_name, container_format, disk_format, image_visibility):
    image_id= None
    payload ={
        "container_format": container_format,
        "disk_format":disk_format,
        "name": image_name,
        "visibility":  image_visibility,
    }
    res = requests.post(glance_ep+ '/v2.1/images',
                    headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   }, 
                             data=json.dumps(payload))
    if res.ok:
        print("Image Created")
        data= res.json()
        image_id= data["image"]["id"]
    else:
        res.raise_for_status()
    return image_id

def upload_file_to_image(glance_ep, token, image_file, image_id):
    #image_file= open("cirros-0.5.1-x86_64-disk.img", "r")
    res = requests.put(glance_ep+'/v2.1/images/'+image_id+'/file',
                    headers={'content-type': 'application/octet-stream',
                             'X-Auth-Token':  token   }, 
                             data=image_file)
    if res.ok:
        print("File GIven to Image")
    else:
        res.raise_for_status()


def attach_volume(instance_name,vol_name,project_id,token):

    mountpoint= "/dev/vdb"
    res = requests.get('http://100.82.39.60:8774/v2.1/servers',
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})
    if res.ok:
        data=res.json()
        for sd in (data["servers"]):
            if instance_name in (sd["name"]):
            inst_id =sd["id"]


    url= "http://100.82.39.60:8776/v3/"+ project_id +"/volumes"
    res = requests.get(url,
                        headers={'content-type': 'application/json',
                            'X-Auth-Token': token})



    data= res.json()
    for sd in (data["volumes"]):
        if vol_name in (sd["name"]):
            vol_id=sd["id"]

            payload= {"volumeAttachment": {"volumeId": vol_id}}
        #    POST http://100.82.39.60:8774/v2.1/servers/b6562df0-859e-4e31-8ce3-2f743a46c8d9/os-volume_attachments
            url= "http://100.82.39.60:8774/v2.1/servers/"+ inst_id +"/os-volume_attachments"

            res = requests.post(url,
                            headers={'content-type': 'application/json',
                                    'X-Auth-Token': token},
                                     data=json.dumps(payload))
            if res.ok:
                print("Successfully attach "+ (vol_name) +"Volume with instance"+ (instance_name))

            else :
                res.raise_for_status()

def create_server(nova_ep, token, server_name, image, keypair_name, flavor,  network, security_group):
    server_url= None
    payload= {"server": {"name": server_name, "imageRef": image,
        "key_name": keypair_name, "flavorRef": flavor_id, 
        "max_count": 1, "min_count": 1, "networks": [{"uuid": network}], 
        "security_groups": [{"name": security_group}]}}   
    res = requests.post(nova_ep+ '/servers',
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token},
                  data=json.dumps(payload))

    if res.ok:
        print("Successfully Created Server "+ server_name)
        data= res.json()
        server_url= data["server"]["links"][0]["href"]  
    else :
        res.raise_for_status()
    return server_url

    def get_server_detail(nova_ep, token, server_url):
        server_id= None
        res = requests.get(server_url,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
        if res.ok:
            print("Successfully Received Server Details")
            data= res.json()
            server_id= data["server"]["id"]
        else:
            res.raise_for_status()
        return server_id 

def check_server_status(nova_ep, token, server_id):
    server_status= None
    res = requests.get(nova_ep+ '/servers/'+server_id,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   })
    if not res.ok:
        res.raise_for_status()
    else: 
        data= res.json()
        server_status= data["server"]["OS-EXT-STS:vm_state"]
    
    return server_status

def get_server_ip(server, network):
    res = requests.get(nova_ep+ '/servers/'+server,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if not res.ok:
        res.raise_for_status()
    data= res.json()
    for networks in data["server"]["addresses"][str(network)]:
        if networks["OS-EXT-IPS:type"] == "fixed":
            return networks["addr"]
def get_server_floating_ip(server, network):
    ip=""
    res = requests.get(nova_ep+ '/servers/'+server,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   },
                  data=json.dumps(payload))
    if not res.ok:
        res.raise_for_status()
    data= res.json()
    for networks in data["server"]["addresses"][str(network)]:
        if networks["OS-EXT-IPS:type"] == "floating":
            ip= networks["addr"]
    return ip
        
def get_ports(network_id, server_ip):
    res = requests.get(neutron_ep+ '/v2.0/ports?network_id='+network_id,
                   headers={'content-type': 'application/json',
                             'X-Auth-Token':  token   }
                  )
    if res.ok:
        print("Successfully Received Ports List ")
    else :
        res.raise_for_status()
    data= res.json()
    for port in data["ports"]:
        if port["fixed_ips"][0]["ip_address"] == server_ip:
            return port["id"]

def create_floating_ip(network_id, subnet_id, server_ip_address, server_port_id):
    payload= {"floatingip": 
             {"floating_network_id": network_id,
              "subnet_id": subnet_id,
              "fixed_ip_address": server_ip_address,
               "port_id": server_port_id
              }
             } 
    res = requests.post(neutron_ep+'/v2.0/floatingips',
                    headers={'content-type': 'application/json',
                             'User-Agent': 'python-novaclient',
                             'X-Auth-Token':  token   }, 
                    data=json.dumps(payload))
    if res.ok:
        print("Successfully Created Floating IP ")
    else :
        res.raise_for_status()
    data= res.json()
    return data["floatingip"]["floating_ip_address"]
