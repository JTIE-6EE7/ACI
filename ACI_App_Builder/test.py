#!/usr/local/bin/python3

import csv, sys, getpass, requests
from jinja2 import Template, Environment, FileSystemLoader

file_loader = FileSystemLoader('.')
# Load the enviroment
env = Environment(loader=file_loader)
template = env.get_template('JSON/static_ports.j2')

#output = template.render(Tenant="Tenant58",Alias="Bob",Subnet="1.1.1.1", AppID="XXX", Tier="GFY")

#print(output)

int_build = "SRxxxxxxxx_int.csv"
int_configs = []

with open(int_build) as build_file:
    # create dictionary from CSV build file
    build_data = csv.DictReader(build_file)
    # insert CSV data into JSON payload via f-strings
    for row in build_data:
        int_cfg_json = template.render(
            Tenant=row["Tenant"],
            Alias=row["Alias"],
            AppID=row["AppID"],
            Supernet=row["Supernet"],
            Tier=row["Tier"],
            Vlan=row["Vlan"],
            LeafNode=row["LeafNode"],
            Interface=row["Interface"]
        )
        int_configs.append(int_cfg_json)
        print(int_cfg_json)
