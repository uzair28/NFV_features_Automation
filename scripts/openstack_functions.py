import requests
import json
import os
import logging

def send_get_request(api_url, token, header='application/json'):
   response= requests.post(api_url, headers={'content-type': header, 'X-Auth-Token': token}) 

def send_put_request(api_url, token, payload, header='application/json'):
    response= requests.put(api_url, headers = {'content-type':header, 'X-Auth-Token': token}, data=json.dumps(payload))

def send_post_request(api_url, token, payload, header='application/json'):
    response= requests.post(api_url, headers = {'content-type':header, 'X-Auth-Token': token}, data=json.dumps(payload))

def parse_json_to_search_resource(data, resource_name, resource_key, resource_value, return_key):
    data= data.json()
    for res in (data[resource_name]):
        if resource_value in (res[resource_key]):
            logging.warning("{} {} already exists".format(resource_key), resource_name)
            return res[return_key]


def get_authentication_token(keystone_ep, username, password):
    #authenticate user with keystone
    logging.debug("authenticating user")
    response= send_post_request("{}/auth/tokens".format(keystone_ep))
    logging.info("successfully authenticated") if response.ok else response.raise_for_status()
    return response.headers.get('X-Subject-Token')



def search_network(neutron_ep, token, network_name):
    #get list of networks
    response= send_get_request("{}/v2.0/network".format(neutron_ep), token)
    logging.info("Successfully Received Networks List") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "networks", "name", network_name, "id")
    
def create_network(neutron_ep, token, network_name, mtu_size, network_provider_type, is_external):
    #Create Network
    payload= {
        "network": {
            "name": network_name,
            "admin_state_up": True,
            "mtu": mtu_size,
            "provider:network_type": network_provider_type,
            "router:external": is_external
            }
        }
    response= send_post_request('{}/v2.0/networks'.format(neutron_ep), token, payload)
    logging.info("Successfully Created Network {}".format(network_name)) if response.ok else response.raise_for_status()
    data=response.json()
    return data['network']['id']


def search_subnet(neutron_ep, token, subnet_name):
    #get list of subnets
    response= send_get_request("{}/v2.0/subnets".format(neutron_ep), token)
    logging.info("Successfully Received Subnet List") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "subnets", "name", subnet_name, "id")

def create_subnet(neutron_ep, token, subnet_name, network_id, cidr):
    #creating Subnet
    payload= {
        "subnet": {
            "name": subnet_name,
            "network_id": network_id,
            "ip_version": 4,
            "cidr": cidr
            }
        }
    response= send_post_request("{}/v2.0/subnets".format(neutron_ep), token, payload)
    logging.info("successfully created subnet") if response.ok else response.raise_for_status()
    data= response.json()
    return data['subnet']['id']

def create_subnet(neutron_ep, token, subnet_name, network_id, cidr, gateway, pool_start, pool_end):
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
    response= send_post_request("{}/v2.0/subnets".format(neutron_ep), token, payload)
    logging.info("successfully created subnet") if response.ok else response.raise_for_status()
    data= response.json()
    return data['subnet']['id']


def search_flavor(nova_ep, token, flavor_name):
    # get list of flavors
    response= send_get_request("{}/v2/flavors".format(nova_ep), token)
    logging.info("Successfully Received Subnet List") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "flavours", "name", flavor_name, "id")

def create_flavor(nova_ep, token, flavor_name, flavor_ram, flavor_vcpus, flavor_disks):
    # Create Flavora
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
    response= send_post_request("{}/v2.0/flavors".format(nova_ep), token, payload)
    logging.info("successfully created flavor") if response.ok else response.raise_for_status()
    data= response.json()
    return data['flavor']['id']

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
    response= send_post_request("{}/v2.0/flavors/{}".format(nova_ep, flavor_id), token, payload)
    logging.info("Successfully Added Extra specs to  Flavor {}".format(flavor_id)) if response.ok else response.raise_for_status()



def create_router(neutron_ep, token, router_name):
    payload={"router":
        {"name": router_name,
        "admin_state_up":" true",
        }
        }
    response= requests.post('{}/v2.0/routers'.format(neutron_ep), token, payload)
    logging.info("Successfully Created Router {}".format(router_name)) if response.ok else response.raise_for_status()  
    data= response.json()
    return data['router']['id']
    
def search_security_group(neutron_ep, token, security_group_name):
    response= send_get_request("{}//v2.0/security-groups", token)
    logging.info("Successfully Received Security Group List") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "security_groups", "name", security_group_name, "id")

def create_security_group(neutron_ep, token, security_group_name):
    payload= {
    "security_group": {
        "name": security_group_name,
    }
    }
    response = send_post_request('{}/v2.0/security-groups'.format(neutron_ep), token, payload)
    logging.info("Successfully Created Security Group {}".format(security_group_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["security_group"]["id"]

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
    response= send_post_request('{}/v2.0/security-group-rules'.format(neutron_ep), token, payload)
    logging.info("Successfully added ICMP rule to Security Group ") else response.raise_for_status()

def search_keypair(nova_ep, token, keypair_name):
    response= send_get_request("{}/os-keypairs".format(nova_ep), token)
    logging.info("successfully received keypair list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "keypairs", "name", keypair_name, "public_key")

def create_keypair(nova_ep, token, keypair_name):
    payload={"keypair":
        {"type": "ssh",
        "name": keypair_name
        }
        }
    response = send_post_request('{}/os-keypairs'.format(nova_ep), token, payload)
    logging.info("successfully created keypair {}".format(keypair_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["security_group"]["id"]


def search_image(glance_ep, token, image_name):
    response= send_get_request("{}/v2/images".format(glance_ep), token)
    logging.info("successfully received images list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "images", "name", image_name, "id")

def create_image(glance_ep, token, image_name, container_format, disk_format, image_visibility):
    payload ={
        "container_format": container_format,
        "disk_format":disk_format,
        "name": image_name,
        "visibility":  image_visibility,
    }
    response = send_post_request('{}/v2/images'.format(glance_ep), token, payload)
    logging.info("successfully created image {}".format(image_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["image"]["id"]

def upload_file_to_image(glance_ep, token, image_file, image_id):
    #image_file= open("cirros-0.5.1-x86_64-disk.img", "r")
    response = send_put_request('{}/v2/images/{}/file'.format(glance_ep, image_id), token, image_file, 'application/octet-stream')
    logging.info("successfully uploaded to image") if response.ok else response.raise_for_status()


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
    payload= {"server": {"name": server_name, "imageRef": image,
        "key_name": keypair_name, "flavorRef": flavor_id, 
        "max_count": 1, "min_count": 1, "networks": [{"uuid": network}], 
        "security_groups": [{"name": security_group}]}}   
    response = send_post_request('{}/servers'.format(nova_ep), token, payload)
    logging.info("successfully created server {}".format(server_name)) if response.ok else  response.raise_for_status()
    data= response.json()
    return data["server"]["links"][0]["href"]  

def get_server_detail(nova_ep, token, server_url):
    response = send_get_request("{}/servers/{}".format(nova_ep, server_url), token)
    print("Successfully Received Server Details") if response.ok else response.raise_for_status()
    data= response.json()
    return data["server"]["id"]


def check_server_status(nova_ep, token, server_id):
    response = send_get_request("{}/servers/{}".format(nova_ep, server_id), token)
    data= response.json()
    return data["server"]["OS-EXT-STS:vm_state"] if response.ok else response.raise_for_status()

def get_server_ip(nova_ep, token, server_id, network):
    response = send_get_request('{}/servers/{}'.format(nova_ep, server_id), token)
    if not response.ok:
        response.raise_for_status()
    else: 
        data= response.json()
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
