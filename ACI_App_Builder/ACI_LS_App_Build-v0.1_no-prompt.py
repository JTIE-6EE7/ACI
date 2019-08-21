#!/usr/local/bin/python3
'''                                                                                                                                           

    Low Security Network Build for ACI Deployments - Please review documentation on proper usage!

    This script will prompt for: Service Request number, APIC FQDN or IP, Username and RSA Passcode

    It will use the required accompanying files below in order to generate and apply config for 
    an ACI Low Security Network Build including Application Profiles, Application End Point Groups,
    Bridge Domains and Attachable Entity Profile assignments.
                                                                                                                                           
    =================================================================================================

    Required CSV files:
    
    SRxxxxxxxx_int.csv
    SRxxxxxxxx_app.csv

    Variables in SRxxxxxxxx_int.csv
                                                                                                 
    Variable Name       Description                                                 Example          
    ===============     ===================================================         =================
    {{Tenant}}          VRF or Environment Deployments Will Be Built in             Corporate        
    {{Alias}}           VRF or Environment Abbreviation                             CORP             
    {{AppID}}           CMDB Application ID                                         1809             
    {{Supernet}}        Application Supernet                                        10.100.141.0     
    {{Tier}}            What Tier in 3-Tier App Stack                               PRES             
    {{Vlan}}            Assigned VLAN                                               1501             
    {{LeafNode}}        Leaf Switch                                                 1001             
    {{Interface}}       Physical Interface                                          eth1/12         

    ================================================================================================

    Variables in SRxxxxxxxx_app.csv:                                                             

    Variable Name       Description                                                Example          
    ================    ==================================================         =================
    {{Tenant}}          VRF or Environment Deployments Will Be Built in            Corporate        
    {{Alias}}           VRF or Environment Abbreviation                            CORP             
    {{AppID}}           CMDB Application ID                                        1809             
    {{Supernet}}        Application Supernet                                       10.100.140.0     
    {{Tier}}            What Tier in 3-Tier App Stack                              PRES             
    {{Vlan}}            Assigned VLAN                                              1501             
    {{Subnet}}          Network ID of Allocated Subnet                             10.100.141.0     
    {{Gateway}}         Gateway IP of Allocated Subnet                             10.100.141.1     
    {{CIDR}}            "Slash" CIDR Notation for Allocated Subnet                 24               
'''

import csv, sys, getpass, requests
from jinja2 import Template, Environment, FileSystemLoader

# Function to get API auth token from the APIC
def apic_login(apic):

    # Get username and passcode
    user = "admin" # dev testing - DELETE
    #user = input("Username: ")
    pwd = "ciscopsdt" # dev testing - DELETE
    #pwd = getpass.getpass(prompt="Passcode: ")
       
    # APIC authtication API URL, username/password and HTTP headers
    url = f"https://{apic}/api/aaaLogin.json"
    body = {"aaaUser": {"attributes": {"name": f"{user}", "pwd": f"{pwd}"}}}
    headers = {
        'cache-control': "no-cache"
            }
    
    # disable self-signed cert security warnings 
    requests.packages.urllib3.disable_warnings()

    # HTTP response to authtication request    
    response = requests.request("POST", url, json=body, headers=headers, verify=False)

    # exit if authentication fails
    if response.status_code != 200:
        print("\n**** Authentication failed! ****")
        sys.exit()

    else:
        print("\n**** Authentication successful! ****")

        # get JSON body
        auth = response.json()
       
        # Extract token from within the JSON structure for future POSTs
        token = auth["imdata"][0]["aaaLogin"]["attributes"]["token"]

        return token

# build json payloads to be deployed for interface configurations
def build_int_payloads(sr_num):
    int_build = f"SR{sr_num}_int.csv"
    int_configs = []

    with open(int_build) as build_file:
        # create dictionary from CSV build file
        build_data = csv.DictReader(build_file)
        # insert CSV data into JSON payload via f-strings
        for row in build_data:

            # json nightmare   


            # add interface config to list of interface configs
            int_configs.append(int_cfg_json)
            
        # return list of app_profile configs
        return int_configs

# build json payloads to be deployed for app profiles
def build_app_payloads(sr_num):
    app_build = f"SR{sr_num}_app.csv"
    app_configs = []

    with open(app_build) as build_file:
        # create dictionary from CSV build file
        build_data = csv.DictReader(build_file)
        # insert CSV data into JSON payload via f-strings
        for row in build_data:

            # json nightmare   


            # add app_profile config to list of app_profile configs
            app_configs.append(app_profile_json)
            
        # return list of app_profile configs
        return app_configs

def post_configs(configs, apic_url,headers):
    for index, body in enumerate(configs):

        # HTTP response to authtication request    
        response = requests.request("POST", apic_url, json=body, headers=headers, verify=False)

        # print results
        print(f"Row: {index + 1} - Status code: {response.status_code}")
        
        response.raise_for_status()

def main():
    # prompt user for APIC 
    apic = "sandboxapicdc.cisco.com" # dev testing - DELETE
    #apic = input("Please enter the APIC FQDN or IP address: ")

    # prompt user for SR number
    sr_num = "xxxxxxxx" # dev testing - DELETE
    #sr_num = input("Please enter your SR number: ")

    # run login function and capture auth token
    token = apic_login(apic)

    # set headers to include auth token
    headers = {"Cookie": f"APIC-Cookie={token}"}

    # set APIC API URL
    apic_url = f"https://{apic}/api/mo/uni.json"

    # run functions to generate and post interface configs
    int_configs = build_int_payloads(sr_num)
    print("\nInterface configuration results:\n")
    post_configs(int_configs, apic_url, headers)

    # run function to generate app configs
    app_configs = build_app_payloads(sr_num)
    print("\nApplication Profile configuration results:\n")
    post_configs(app_configs,apic_url,headers)
    print("\nScript complete. Verify results above.\n")
    
    return sr_num, apic_url

if __name__ == "__main__":
    main()