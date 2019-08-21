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
            int_cfg_json = {
                "fvTenant": {
                    "attributes": {
                        "descr": f"{row['Tenant']} VRF",
                        "dn": f"uni/tn-{row['Tenant']}",
                        "name": f"{row['Tenant']}",
                        "nameAlias": f"{row['Alias']}",
                    },
                    "children": [
                        {
                            "fvAp": {
                            "attributes": {
                                "name": f"APP{row['AppID']}_LS_{row['Supernet']}-AP"
                            },
                            "children": [
                                {
                                    "fvAEPg": {
                                        "attributes": {
                                        "name": f"APP{row['AppID']}_{row['Tier']}_Vlan{row['Vlan']}-EPG"                       
                                        },
                                        "children": [
                                            {
                                            "fvRsPathAtt": {
                                                "attributes": {
                                                    "dn": f"uni/tn-{row['Tenant']}/ap-APP{row['AppID']}_LS_{row['Supernet']}-AP/epg-APP{row['AppID']}_{row['Tier']}_Vlan{row['Vlan']}-EPG/rspathAtt-[topology/pod-1/paths-{row['LeafNode']}/pathep-[{row['Interface']}]]",       
                                                    "encap": f"vlan-{row['Vlan']}",        
                                                    "instrImedcy": "immediate",         
                                                    "tDn": f"topology/pod-1/paths-{row['LeafNode']}/pathep-[{row['Interface']}]"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }
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
            app_profile_json = {
                "fvTenant": {
                    "attributes": {
                        "descr": f"{row['Tenant']} VRF",
                        "dn": f"uni/tn-{row['Tenant']}",
                        "name": f"{row['Tenant']}",
                        "nameAlias": f"{row['Alias']}"
                    },
                    "children": [
                        {
                            "fvBD": {
                                "attributes": {
                                    "name": f"APP{row['AppID']}_{row['Tier']}_Vlan{row['Vlan']}-BD",
                                    "nameAlias": f"{row['Subnet']}",
                                    "OptimizeWanBandwidth": "no",
                                    "arpFlood": "no",
                                    "epClear": "no",
                                    "intersiteBumTrafficAllow": "no",
                                    "intersiteL2Stretch": "no",
                                    "ipLearning": "yes",
                                    "limitIpLearnToSubnets": "yes",
                                    "llAddr": "::",
                                    "mac": "00:22:BD:F8:19:FF",
                                    "mcastAllow": "no",
                                    "multiDstPktAct": "bd-flood",
                                    "type": "regular",
                                    "unicastRoute": "yes",
                                    "unkMacUcastAct": "proxy",
                                    "unkMcastAct": "flood",
                                    "vmac": "not-applicable"
                                },
                                "children": [
                                    {
                                        "fvSubnet": {
                                            "attributes": {
                                                "ip": f"{row['Gateway']}/{row['CIDR']}",
                                                "preferred": "no",
                                                "scope": "public",
                                                "virtual": "no"
                                            },
                                            "children": [
                                                {
                                                    "fvRsBDSubnetToProfile": {
                                                        "attributes": {
                                                            "tnL3extOutName": f"GOLF-{row['Alias']}-L3-Out",
                                                            "tnRtctrlProfileName": ""
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "fvRsCtx": {
                                            "attributes": {
                                                "tnFvCtxName": f"{row['Alias']}"
                                            }
                                        } 
                                    },
                                    {
                                        "fvRsBdToEpRet": {
                                            "attributes": {
                                            "resolveAct": "resolve",
                                            }
                                        }
                                    },
                                    {
                                        "fvRsBDToOut": {
                                            "attributes": {
                                                "tnL3extOutName": f"GOLF-{row['Alias']}-L3-Out"
                                            } 
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "fvAp": {
                                "attributes": {
                                    "name": f"APP{row['AppID']}_LS_{row['Supernet']}-AP",
                                    "prio": "unspecified"
                                },
                                "children": [
                                    {
                                        "fvAEPg": {
                                            "attributes": {
                                            "isAttrBasedEPg": "no",
                                            "matchT": "AtleastOne",                                 
                                            "name": f"APP{row['AppID']}_{row['Tier']}_Vlan{row['Vlan']}-EPG",
                                            "nameAlias": f"{row['Subnet']}",
                                            "pcEnfPref": "unenforced",
                                            "prefGrMemb": "exclude",
                                            "prio": "unspecified"                             
                                            },
                                            "children": [
                                                {
                                                    "fvRsBd": {
                                                        "attributes": {
                                                            "tnFvBDName": f"APP{row['AppID']}_{row['Tier']}_Vlan{row['Vlan']}-BD"
                                                        }
                                                    }                                                   
                                                },
                                                {
                                                    "fvRsCons": {
                                                        "attributes": {
                                                            "prio": "unspecified",
                                                            "tnVzBrCPName": "Wan-Permit-All"                                                        
                                                        }
                                                    }                           
                                                },
                                                {
                                                    "fvRsProv": {
                                                        "attributes": {
                                                            "matchT": "AtleastOne",
                                                            "prio": "unspecified",
                                                            "tnVzBrCPName": "Wan-Permit-All"
                                                        }
                                                    }
                                                },
                                                {
                                                    "fvRsDomAtt": {
                                                        "attributes": {
                                                            "classPref": "encap",
                                                            "encap": "unknown",
                                                            "encapMode": "auto",
                                                            "epgCosPref": "disabled",
                                                            "instrImedcy": "lazy",
                                                            "tDn": "uni/phys-Comp-PhyDom",
                                                            "netflowDir": "both",
                                                            "netflowPref": "disabled",
                                                            "resImedcy": "immediate"
                                                        }
                                                    }                             
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
            # add app_profile config to list of app_profile configs
            app_configs.append(app_profile_json)
            print(app_profile_json)
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