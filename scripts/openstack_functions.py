import requests
import json
import os
import logging

def send_get_request(api_url, token, header="application/json"):
    return requests.get(api_url, headers= {'content-type': header, 'X-Auth-Token': token}) 

def send_put_request(api_url, token, payload, header='application/json'):
    return requests.put(api_url, headers= {'content-type':header, 'X-Auth-Token': token}, data= payload)

def send_post_request(api_url, token, payload, header='application/json'):
    return requests.post(api_url, headers= {'content-type':header, 'X-Auth-Token': token}, data=json.dumps(payload))

def parse_json_to_search_resource(data, resource_name, resource_key, resource_value, return_key):
    data= data.json()
    
    for res in (data[resource_name]):
        if resource_value in res[resource_key]:
            logging.warning("{} already exists".format(resource_value))
            return res[return_key]
            break
        
    else:
        logging.info("{} does not exist".format(resource_value))

def get_authentication_token(keystone_ep, username, password):
    #authenticate user with keystone
    payload= {"auth": {"identity": {"methods": ["password"],"password":
                      {"user": {"name": username, "domain": {"name": "Default"},"password": password} }},
                "scope": {"project": {"domain": {"id": "default"},"name": "admin"}}}}
    logging.debug("authenticating user")
    response= send_post_request("{}/auth/tokens".format(keystone_ep), None, payload)
    logging.info("successfully authenticated") if response.ok else response.raise_for_status()
    return response.headers.get('X-Subject-Token')
def search_network(neutron_ep, token, network_name):
    #get list of networks
    response= send_get_request("{}/v2.0/networks".format(neutron_ep), token)
    logging.info("successfully received networks list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "networks", "name", network_name, "id")
    
def create_network(neutron_ep, token, network_name, mtu_size, network_provider_type, is_external):
    #create network
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
    logging.info("successfully created network {}".format(network_name)) if response.ok else response.raise_for_status()
    data=response.json()
    return data['network']['id']

def search_subnet(neutron_ep, token, subnet_name):
    #get list of subnets
    response= send_get_request("{}/v2.0/subnets".format(neutron_ep), token)
    logging.info("Successfully Received Subnet List") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "subnets", "name", subnet_name, "id")

def create_subnet(neutron_ep, token, subnet_name, network_id, cidr, external= False, gateway=None, pool_start= None, pool_end= None):
    #create internal subnet
    payload= {
        "subnet": {
            "name": subnet_name,
            "network_id": network_id,
            "ip_version": 4,
            "cidr": cidr
            }
        }
    payload_external_subnet={"enable_dhcp": "true","gateway_ip": gateway,
               "allocation_pools": [{"start": pool_start, "end": pool_end}]}
    if external== True:
        payload= {"subnet":{**payload["subnet"], **payload_external_subnet}}
    response= send_post_request("{}/v2.0/subnets".format(neutron_ep), token, payload)
    logging.info("successfully created subnet") if response.ok else response.raise_for_status()
    data= response.json()
    return data['subnet']['id']

def search_flavor(nova_ep, token, flavor_name):
    # get list of flavors
    response= send_get_request("{}/v2.1/flavors".format(nova_ep), token)
    logging.info("successfully received flavor list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "flavors", "name", flavor_name, "id")

def create_flavor(nova_ep, token, flavor_name, flavor_ram, flavor_vcpus, flavor_disks):
    # create Flavor
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
    response= send_post_request("{}/v2.1/flavors".format(nova_ep), token, payload)
    logging.info("successfully created flavor") if response.ok else response.raise_for_status()
    data= response.json()
    return data['flavor']['id']

def put_extra_specs_in_flavor(nova_ep, token, flavor_id,is_numa, mem_page_size=None):
    #add extra specs to flavors
    if is_numa== True:
        payload= {
            "extra_specs": {
            #    "aggregate_instance_extra_specs:pinned": "True", 
                "hw:cpu_policy": "dedicated", 
                "hw:cpu_thread_policy": "require",
                "hw:numa_nodes": "1", 
                "hw:mem_page_size": "large"
                }
        }
    else: 
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
    response= send_post_request("{}/v2.1/flavors/{}/os-extra_specs".format(nova_ep, flavor_id), token, payload)
    logging.info("successfully added extra specs to  flavor {}".format(flavor_id)) if response.ok else response.raise_for_status()

def create_router(neutron_ep, token, router_name):
    payload={"router":
        {"name": router_name,
        "admin_state_up":" true",
        }
    }
    response= requests.post('{}/v2.0/routers'.format(neutron_ep), token, payload)
    logging.info("successfully created router {}".format(router_name)) if response.ok else response.raise_for_status()  
    data= response.json()
    return data['router']['id']
    
def search_security_group(neutron_ep, token, security_group_name):
    response= send_get_request("{}/v2.0/security-groups".format(neutron_ep), token)
    logging.info("successfully received security group list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "security_groups", "name", security_group_name, "id")

def create_security_group(neutron_ep, token, security_group_name):
    payload= {
    "security_group": {
        "name": security_group_name,
        }
    }
    response = send_post_request('{}/v2.0/security-groups'.format(neutron_ep), token, payload)
    logging.info("successfully created security Group {}".format(security_group_name)) if response.ok else response.raise_for_status()
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
    logging.info("Successfully added {} rule to Security Group ".format(protocol)) if response.ok else response.raise_for_status()

def search_keypair(nova_ep, token, keypair_name):
    response= send_get_request("{}/v2.1/os-keypairs".format(nova_ep), token)
    logging.info("successfully received keypair list") if response.ok else response.raise_for_status()
    data= response.json()
    for res in (data["keypairs"]):
        if keypair_name in res["keypair"]["name"]:
            logging.warning("{} already exists".format(keypair_name))
            return res["keypair"]["public_key"]
            break      
    else:
        logging.info("{} does not exist".format(keypair_name))

def create_keypair(nova_ep, token, keypair_name):
    payload={
        "keypair":{
            "name": keypair_name,
            #"type": "ssh" 
            }
        }
    #nova_ep="http://192.168.140.252:8774/V2.2"
    response= send_post_request('{}/v2.1/os-keypairs'.format(nova_ep), token, payload)
    logging.info("successfully created keypair {}".format(keypair_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["keypair"]["public_key"]


def search_image(nova_ep, token, image_name):
    response= send_get_request("{}/v2.1/images".format(nova_ep), token)
    logging.info("successfully received images list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "images", "name", image_name, "id")

def create_image(nova_ep, token, image_name, container_format, disk_format, image_visibility):
    payload ={
        "container_format": container_format,
        "disk_format":disk_format,
        "name": image_name,
        "visibility":  image_visibility,
    }

    response = send_post_request("{}/v2/images".format(nova_ep), token, payload)
    logging.info("successfully created image {}".format(image_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["id"]

def upload_file_to_image(nova_ep, token, image_file, image_id):
    #image_file= open("cirros-0.5.1-x86_64-disk.img", "r")
    response = send_put_request("{}/v2/images/{}/file".format(nova_ep, image_id), token, image_file, "application/octet-stream")
    logging.info("successfully uploaded to image") if response.ok else response.raise_for_status()

def search_server(nova_ep, token, server_name):
    response= send_get_request("{}v2.1/servers/".format(nova_ep), token)
    logging.info("successfully received server list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "servers", "name", server_name, "id")

def create_server(nova_ep, token, server_name, image_id, keypair_name, flavor_id,  network_id, security_group_id):
    payload= {"server": {"name": server_name, "imageRef": image_id,
        "key_name": keypair_name, "flavorRef": flavor_id, 
        "max_count": 1, "min_count": 1, "networks": [{"uuid": network_id}], 
        "security_groups": [{"name": security_group_id}]}}   
    response = send_post_request('{}/2.1/servers'.format(nova_ep), token, payload)
    logging.info("successfully created server {}".format(server_name)) if response.ok else  response.raise_for_status()
    data= response.json()
    return data["server"]["links"][0]["href"]  

def get_server_detail(token, server_url):
    response = send_get_request(server_url, token)
    logging.info("Successfully Received Server Details") if response.ok else response.raise_for_status()
    data= response.json()
    return data["server"]["id"]


def check_server_status(nova_ep, token, server_id):
    response = send_get_request("{}/v2.1/servers/{}".format(nova_ep, server_id), token)
    data= response.json()
    return data["server"]["OS-EXT-STS:vm_state"] if response.ok else response.raise_for_status()

def parse_server_ip(data, network, network_type):
    for networks in data["server"]["addresses"][str(network)]:
            if networks["OS-EXT-IPS:type"] == network_type:
                logging.info("received {} ip address of server".format())
                return networks["addr"]

def get_server_ip(nova_ep, token, server_id, network):
    response = send_get_request('{}/v2.1/servers/{}'.format(nova_ep, server_id), token)
    logging.info("received server network detail") if response.ok else response.raise_for_status()
    return parse_server_ip(response, network, "fixed")

def get_server_floating_ip(nova_ep, token, server_id, network):
    response = send_get_request('{}/v2.1/servers/{}'.format(nova_ep, server_id), token)
    logging.info("received server network detail") if response.ok else response.raise_for_status()
    return parse_server_ip(response, network, "floating")

def parse_port_response(data, server_fixed_ip):
    data= data.json(data)
    for port in data["ports"]:
        if port["fixed_ips"][0]["ip_address"] == server_fixed_ip:
            return port["id"]   

def get_ports(neutron_ep, token, network_id, server_ip):
    response= send_get_request("{}//v2.0/ports?network_id={}".format(neutron_ep, network_id), token)
    logging.info("successfully received ports list ") if response.ok else response.raise_for_status()
    return parse_port_response(response, server_ip)

def create_floating_ip(neutron_ep, token, network_id, subnet_id, server_ip_address, server_port_id):
    payload= {"floatingip": 
             {"floating_network_id": network_id,
              "subnet_id": subnet_id,
              "fixed_ip_address": server_ip_address,
               "port_id": server_port_id
              }
             } 
    response= send_post_request("{}/V2.0/floatingips".format(neutron_ep), token, payload)
    logging.info("successfully assigned floating ip to server") if response.ok else response.raise_for_status()
    data= response.json()
    return data["floatingip"]["floating_ip_address"]

def attach_volume_to_server( nova_ep, token, project_id, server_id, volume_id, mount_point):
    payload= {"volumeAttachment": {"volumeId": volume_id}}
    response= send_post_request("{}/v2.1/servers/{}/os-volume-attachments".format(nova_ep, server_id), token, payload)
    logging.info("volume successfully attached to server") if response.ok else response.raise_for_status()

def search_volume(storage_ep, token, volume_name, project_id):
    response= send_get_request("{}/V3/{}/volumes".format(storage_ep, project_id), token)
    logging.info("successfully received volume list") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "volumes", "name", "id")

def create_volume(storage_ep, token, project_id, volume_name, volume_size):
    payload= {

        "volume": {
        "name": volume_name,
        "size": volume_size
        }
    }
    response= send_post_request("{}/V3/{}/volumes".format(storage_ep, project_id), token, payload)
    logging.info("successfully created volume {}".format(volume_name)) if response.ok else response.raise_for_status()
    data= response.json()
    return data["volume"]["id"]

def find_admin_project_id(keystone_ep, token):
    response= send_get_request("{}/V3/projects".format(keystone_ep))
    logging.info("successfully received project details") if response.ok else response.raise_for_status()
    return parse_json_to_search_resource(response, "projects", "name", "admin", "id")


