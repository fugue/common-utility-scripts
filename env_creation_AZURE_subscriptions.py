# This script is for Python v.3.6 and above and also requires Requests module installed

import json
import os
import requests

# Common parameters that can be configured as needed 
# provider: azure - Azure + Azure Govcloud
# interval: scan interval in seconds. Default is 24hrs 
# compliance_families: List of complaince families needed https://docs.fugue.co/api.html#api-compliance-format
# subscriptions: map of Azure Application Name, credentials and Resource Groups that need to be loaded into Fugue in the format "App Name": ["Tenant Id", "Subscription Id", "Application ID", "Client Secret", [Resource Groups]].
# Default for Resource Group value is "*" for automatically discovering and adding all resource groups. 
# For selective resource groups, use the format ["example-rg","another-rg"] 
# Environments are created with the App name. Details on how to create these: https://docs.fugue.co/setupazure.html#step-2a-connect-to-azure

provider = "azure"
interval = "86400"
compliance_families = ["CISAZURE"]
subscriptions = {
    "Prod App": ["1", "1", "1", "1", ["*"]],
    "Dev App": ["2", "2", "2", "2", ["example-rg","another-rg"]]
}

# Fugue API base URL
api_url = "https://api.riskmanager.fugue.co"
api_ver = 'v0'

# Client ID and secret used to authenticate with Fugue. Follow the guide here
# to create an API client: https://docs.fugue.co/api.html#getting-started
# You can set these values via environment variables or replace the os.getenv
# calls below with the string values themselves.
client_id = os.getenv('FUGUE_API_ID')
client_secret = os.getenv('FUGUE_API_SECRET')

if not client_id or not client_secret:
    print('Please follow the user guide at https://docs.fugue.co/api.html#api-user-guide to set \'FUGUE_API_ID\' and \'FUGUE_API_SECRET\'')
    exit(1)


# Authentication
# https://docs.fugue.co/api.html#auth-n
auth = (client_id, client_secret)

def get(path, params=None):
    """
    Executes an authenticated GET request to the Fugue API with the provided
    API path and query parameters.
    """
    url = '%s/%s/%s' % (api_url, api_ver, path.strip('/'))
    return requests.get(url, params=params, auth=auth).json()

def create_env(path, json=None):
    """
    Executes an authenticated POST request to the Fugue API with the provided
    API path and json to create an environment.
    """
    url = '%s/%s/%s' % (api_url, api_ver, path.strip('/'))
    return requests.post(url, auth=auth, json=json)


def create_azure_env_def(env_name, provider, credentials, compliance_families, resource_groups, interval=0):
    if interval != 0:
        scan_schedule_enabled = True
    else: 
        scan_schedule_enabled =  False     
               
    body = {
        "name": env_name,
        "provider": provider,
        "provider_options": {
            provider: {
            "tenant_id": credentials[0],
            "subscription_id": credentials[1],
            "application_id": credentials[2],
            "client_secret": credentials[3],
            "survey_resource_groups": resource_groups
            }
        },
        "compliance_families": compliance_families,
        "scan_schedule_enabled": bool(scan_schedule_enabled),
        "scan_interval": int(interval)
        }
    return body

def main():
    """
    Loop through each account and region to create an environment using Fugue API
    https://docs.fugue.co/api.html#example-create
    """
    if provider.lower() == "aws" or provider.lower() == "aws_govcloud":
        print ("This script is only for Azure environment creation")
    else:
        for name, provider_options in subscriptions.items():
        # Set environment name
            env_name = name
            credentials = provider_options[0:4]
            resource_groups = provider_options[4]

            print("Starting on creation for environment " + env_name)
            # Create JSON body  
            env_def = create_azure_env_def(env_name, provider.lower(), credentials, compliance_families, resource_groups, interval)
            print ("JSON body created for environment " + env_name )
            print ("Creating environment for " + env_name)
                
            #Create environment
            resp = create_env('environments', env_def)
                    
            if resp.status_code != 201:
                print('Environment creation failed for App: ' + name + ' with response code: {}'.format(resp.status_code) + ' and reason: {}'.format(resp.text) + "\n") 
            else:
                env_id = resp.json()['id'] 
                print ('Environment created for App: ' + name + ' with environment name: ' + resp.json()['name'] + ' and environment id: ' + resp.json()['id'] + "\n") 

if __name__ == '__main__':
    main()            