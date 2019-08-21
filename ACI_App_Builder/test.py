#!/usr/local/bin/python3

import csv, sys, getpass, requests
from jinja2 import Template, Environment, FileSystemLoader

file_loader = FileSystemLoader('.')
# Load the enviroment
env = Environment(loader=file_loader)
template = env.get_template('JSON/app_profile.j2')

output = template.render(Tenant="Tenant58",Alias="Bob",Subnet="1.1.1.1", AppID="XXX", Tier="GFY")

print(output)