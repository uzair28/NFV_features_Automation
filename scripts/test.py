import os
import json
import random

def get_status():
    return random.randint(0,2)

def wait_for_server(servers_metadeta):
    for i in range(10):
        print("@@@@@@")
        for server in servers_metadeta:
            status= get_status() 
            server["status"]= get_status()
            print("server {} status is: {}".format(server.get("name"), server.get("status")))
        if()
        
    



print("Hello")
servers_metadeta=[]
for i in range(5):
    id= "id"
    servers_metadeta.append({"name":"server {}".format(i), "id": id, "status":None})

print(servers_metadeta)  
wait_for_server(servers_metadeta)






'''
def fun():
    try:
        with open("settings.json", 'r') as file:
            data = file.read().replace('\n', '')
        settings= json.loads(data)

    except Exception as e:
        print(e)
        print("Failed to load settings file")
    return settings

s= fun()
prnt(s)
def return_test():
    list=[5,6,7,8,9]
    for number in list:
        if number==10:
            id=number
            break

    return id if ('id') in locals() else None

payload= {
    "networks": [
        {
            "admin_state_up": "true",
            "id": "396f12f8-521e-4b91-8e21-2e003500433a",
            "name": "net3",
            "provider:network_type": "vlan",
            "provider:physical_network": "physnet1",
            "provider:segmentation_id": 1002,
            "router:external": "false",
            "shared": "false",
            "status": "ACTIVE",
            "subnets": [],
            "tenant_id": "20bd52ff3e1b40039c312395b04683cf",
            "project_id": "20bd52ff3e1b40039c312395b04683cf"
        },
        {
            "admin_state_up": "true",
            "id": "71c1e68c-171a-4aa2-aca5-50ea153a3718",
            "name": "net2",
            "provider:network_type": "vlan",
            "provider:physical_network": "physnet1",
            "provider:segmentation_id": 1001,
            "router:external": "false",
            "shared": "false",
            "status": "ACTIVE",
            "subnets": [],
            "tenant_id": "20bd52ff3e1b40039c312395b04683cf",
            "project_id": "20bd52ff3e1b40039c312395b04683cf"
        }
    ],
    "networks_links": [
        {
            "href": "http://127.0.0.1:9696/v2.0/networks.json?limit=2&marker=71c1e68c-171a-4aa2-aca5-50ea153a3718",
            "rel": "next"
        },
        {
            "href": "http://127.0.0.1:9696/v2.0/networks.json?limit=2&marker=396f12f8-521e-4b91-8e21-2e003500433a&page_reverse=True",
            "rel": "previous"
        }
    ]
}
'''