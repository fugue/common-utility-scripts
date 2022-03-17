# This script is for Python v.3.6 and above and also requires Requests module installed

import json
import os
import requests
import getpass

# Common parameters that can be configured as needed 
# provider: azure - Azure + Azure Govcloud
# interval: scan interval in seconds. Default is 24hrs 
# compliance_families: List of complaince families needed https://docs.fugue.co/api.html#api-compliance-format
# subscriptions: map of Azure Application Name, credentials and Resource Groups that need to be loaded into Fugue.
# Format "App Name": ["Tenant Id", "Subscription Id", "Application ID", "Client Secret", [Resource Groups]].
# Client Secret can be left blank or set to "-" if the CLI opted value needs to be used
# Default for Resource Group value is "*" for automatically discovering and adding all resource groups. 
# For selective resource groups, use the format ["example-rg","another-rg"] 
# Environments are created with the App name. Details on how to create these: https://docs.fugue.co/setupazure.html#step-2a-connect-to-azure
# allow_dups: Default = False. Flag to allow duplicate environment creation in Fugue. 
    # If set to False, a list of existing environment will be retrieved from Fugue and only applications not in Fugue will be created.  

provider = "azure"
interval = "86400"
compliance_families = ["CISAZURE"]
allow_dups = False
subscriptions = {
    "Prod App": ["tenant id", "subscription id", "app id", ["*"]],
    "Dev App": ["2", "2", "2", ["example-rg","another-rg"]],
    "QA App": ["3", "3", "3", ["example-rg","another-rg"]]
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

def get_app_list(provider):
    """
        Get list of Azure environments in Fugue tenant and extract the Applications IDs from the credentials.   
    """
    offset = 0
    max_items = 1
    app_id_list = []
    env_id = []
    is_truncated = True
    
    while is_truncated: 
        params = {
            'q.provider': provider,
            'offset' : offset,
            'max_items' : max_items,
        }
        try:
            env_list = get('environments', params=params)
        except Exception as error: 
                sys.exit("Error:" + error) 
        else: 
            for env in env_list['items']:
                app_id_list.append(env['provider_options']['azure']['application_id'])
            offset = env_list['next_offset']
            is_truncated = env_list['is_truncated']
    
    return app_id_list

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
        try:
            key = getpass.getpass(prompt='Enter client secret: ', stream=None).strip()
        except Exception as error: 
            sys.exit("Error:" + error) 
        else: 
            if key != "":
                print ("Key entered manually")
            else:
                exit("Secret was not entered.")   
        
        # If allow_dups = False, get list of Azure envrionments from Fugue and extract the application ID from credentials
        if allow_dups == False:
           print ("Duplicate environments are not allowed. Retrieving list of environments and application id" + "\n") 
           existing_app_list = get_app_list(provider)  
           print ("Existing applications list retrieved (" + str(len(existing_app_list)) + ")" + "\n") 

        for name, provider_options in subscriptions.items():
            # Set environment name and credentials
            env_name = name
            credentials = provider_options[0:3]
            app_id = provider_options[2]
            credentials.append(key)
            resource_groups = provider_options[3]

            if allow_dups == False and app_id in existing_app_list:   
                print ("Found application id in existing environment list. Skipping environment creation for - " + name + ": " + app_id + "\n")
            else:
                print("Starting creation for environment " + env_name)
                # Create JSON body  
                env_def = create_azure_env_def(env_name, provider.lower(), credentials, compliance_families, resource_groups, interval)
                print ("JSON body created for environment " + env_name )
                    
                #Create environment
                resp = create_env('environments', env_def)
                        
                if resp.status_code != 201:
                    print('Environment creation failed for App: ' + name + ' with response code: {}'.format(resp.status_code) + ' and reason: {}'.format(resp.text) + "\n") 
                else:
                    env_id = resp.json()['id'] 
                    print ('Environment created for App: ' + name + ' with environment name: ' + resp.json()['name'] + ' and environment id: ' + resp.json()['id'] + "\n") 

if __name__ == '__main__':
    main()            
