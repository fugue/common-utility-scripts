# This script is for Python v.3.6 and above and also requires Requests module, Google Cloud SDK installed (https://cloud.google.com/sdk/docs/install) 
# and Resource Manager Python CLI installed (pip install google-cloud-resource-manager)

import json
import os
import requests
from google.cloud import resource_manager

# Common parameters that can be configured as needed 

# provider: agoogle - Others are not supported currently by this script
# interval: scan interval in seconds. Default is 24hrs 
# service_account_email: Service account email created for onboarding projects. This assumes the service account has already been created with the 
    # required permission for each of the projects and it already exists in the target Org 
# compliance_families: List of complaince families needed https://docs.fugue.co/api.html#api-compliance-format
# projects: map of Google Cloud project names and Ids that needed to be loaded into Fugue. Environments are created with the
    # names in the format "Name - id" 
# allow_dups: Default = False. Flag to allow duplicate environment creation in Fugue. 
    # If set to False, a list of existing environment will be retrieved from Fugue and only accounts not in Fugue will be created.  


provider = "google"
service_account_email = "<service account email>"
interval = "86400"
compliance_families = ["CIS-Google_v1.1.0"]
allow_dups = False
# projects = {
#     "Prod Project": "ultra-depot-307716",
#     "Dev Project": "5678"
# }

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

def get_projects_from_org():
    projects_in_org = []
    project_list = {}
    env_filter = {'lifecycleState': 'Active'}
    org_client = resource_manager.Client()
    response = org_client.list_projects(env_filter)
   
    for project in response:
        name = project.name
        id = project.project_id
        project_list[project.name] = id

    return project_list

def get(path, params=None):
    """
    Executes an authenticated GET request to the Fugue API with the provided
    API path and query parameters.
    """
    url = '%s/%s/%s' % (api_url, api_ver, path.strip('/'))
    return requests.get(url, params=params, auth=auth).json()

def get_project_list(provider):
    """
        Get list of AWS environments in Fugue tenant and extract the Account IDs from the Role ARN.   
    """
    offset = 0
    max_items = 100
    project_id_list = []
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
                project_id_list.append(env['provider_options']['google']['project_id'])
            offset = env_list['next_offset']
            is_truncated = env_list['is_truncated']

    return project_id_list
    
def create_env(path, json=None):
    """
    Executes an authenticated POST request to the Fugue API with the provided
    API path and json to create an environment.
    """
    url = '%s/%s/%s' % (api_url, api_ver, path.strip('/'))
    return requests.post(url, auth=auth, json=json)


def create_google_env_def(env_name, provider, projectid, compliance_families, service_account_email, interval=0):
    if interval != 0:
        scan_schedule_enabled = True
    else: 
        scan_schedule_enabled =  False     
    
    body = {
        "name": env_name,
        "provider": provider,
        "provider_options": {
            provider: {
            "service_account_email": service_account_email,
            "project_id": projectid
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
    if provider.lower() != "google":
        print ("This script is only for AWS environment creation")
    else:
        # If allow_dups = False, get list of AWS envrionments from Fugue and extract the AWS account ID from Role ARN
        if allow_dups == False:
           print ("Duplicate environments are not allowed. Retrieving list of environments and project ids" + "\n") 
           existing_project_list = get_project_list(provider)  
           print ("Existing project list retrieved (" + str(len(existing_project_list)) + ")" + "\n")   
        
        projects = get_projects_from_org()

        for name, proj_id in projects.items():
            if allow_dups == False and proj_id in existing_project_list:   
                print ("Found project id in existing environment list. Skipping environment creation for - " + name + ": " + proj_id)
            else:
                print ("Creating env for: " + proj_id)
                env_name = proj_id
                print("Starting on creation for environment " + env_name + " and id: " + proj_id)
                        
                # Create JSON body  
                env_def = create_google_env_def(env_name, provider.lower(), proj_id, compliance_families, service_account_email, interval)
                print ("JSON body created for environment " + env_name)
                print ("Creating environment for " + env_name + " and id: " + proj_id)
                    
                #Create environment
                resp = create_env('environments', env_def)
                        
                if resp.status_code != 201:
                    print('Environment creation failed for Project: ' + proj_id + ' with response code: {}'.format(resp.status_code) + ' and reason: {}'.format(resp.text) + "\n") 
                else:
                    env_id = resp.json()['id'] 
                    print ('Environment created for Project: ' + proj_id + ' with environment name: ' + resp.json()['name'] + ' and environment id: ' + resp.json()['id'] + "\n") 

if __name__ == '__main__':
    main()            