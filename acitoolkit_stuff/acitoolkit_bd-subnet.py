#from credentials_to_myACI import *
from acitoolkit.acitoolkit import *

# JT added this cause he's lazy
URL = "https://sandboxapicdc.cisco.com"
LOGIN = "admin"
PASSWORD = "ciscopsdt"
y = "BD_list.txt"

#Begin the session
session = Session(URL, LOGIN, PASSWORD)
session.login()

#This script creates BDs from a list

#Variables
tenant_name = 'Greenfish'
tenant = Tenant(tenant_name)
vrf = Context('VRF1', tenant)

#First, creating a dictionary from the list
dictionary = {}

#y = input("What file is your list of bridge domains?")

with open(y) as f:
    for line in f:
        key, value = line.strip("\n").split(":",1)
        dictionary[key] = value

#Create each BD and subnet
for key in dictionary:
   
    bd_name = key
    bridge_domain = BridgeDomain(bd_name, tenant)
    bridge_domain.add_context(vrf)
    subnet_name = key
    subnet = Subnet(subnet_name, bridge_domain)
    subnet.set_scope("public")
    subnet.set_addr(dictionary[key]) 
    
#Committing the config to APIC and reporting the results
resp = session.push_to_apic(tenant.get_url(), data=tenant.get_json())

if resp.ok:
    #print("\n{}: {}\n\n{} is ready for use".format(resp.status_code, resp.reason, http://tenant.name))
    print("OK!")
 
else:
    #print("\n{}: {}\n\n{} was not created!\n\n Error: {}".format(resp.status_code, resp.reason, http://subnet.name, resp.content))
    print("BAD!!")
    print(resp.reason)
    print(resp.status_code)
    print(resp.content)

