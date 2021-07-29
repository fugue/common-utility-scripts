# This script is for Python v.3.6 and above 
# The script requires Requests module installed (pip install requests) as well as boto3 (pip install boto3)

import json
import os
import requests
import boto3

# Common parameters that can be configured as needed 

# provider: Either aws or aws_govcloud - Azure is not supported currently by this script
# region: Region for the environment in the given account. "*" indicates all supported regions by Fugue. 
# Multiple regions format ["us-east-1", "us-east-2"] 
# interval: scan interval in seconds. Default is 24hrs 
# rolename: Name of the IAM Role created in the accounts. This assumes the roles have already been created with the 
# required permission for each of the accounts 
# already exist in the target AWS accounts with the correct policy attached 
# resource_types: List of resources for the given environment. The default value is ALL and that will invoke another Fugue API call
# to retrieve the supported list of resources from the API directly. 
# You can specify a limited set of resource types using this syntax  ["AWS.ACM.Certificate", "AWS.ACMPCA.CertificateAuthority"] 
# https://docs.fugue.co/servicecoverage.html  
# compliance_families: List of complaince families needed https://docs.fugue.co/api.html#api-compliance-format
# aws_profile_name: the profile name for AWS Org that allows the script to extract the list of active AWS accounts 

provider = "aws"
regions = ["*"]
rolename = "FugueRiskManager"
interval = "86400"
resource_types = ["All"] 
compliance_families = ["FBP","CIS"]
aws_profile_name = "fugueorg"

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

def get_accounts_from_org(profile):
    session = boto3.Session(profile_name=profile)
    org_client = session.client("organizations")
    accounts_in_org = []
    accounts_list = {}
    response = org_client.list_accounts()

    while response:
        accounts_in_org += response["Accounts"]
        response = org_client.list_accounts(NextToken=response['NextToken']) if 'NextToken' in response else None
    for account in accounts_in_org:
        name = account["Name"]
        id = account["Id"]
        if account["Status"] == "ACTIVE":
            accounts_list[name] = id
    return accounts_list

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

def get_resource_types(resource_types, region, provider):
    """
    Executes an authenticated GET request to Fugue API to retrieve entire list
    of supported resource types if value is set to "All"
    """
    if resource_types == ["All"]:
        params = {
        'region': region,
        'beta_resources': "true"
    }
        survey_resource_types = get('metadata/' + provider + '/resource_types', params=params)['resource_types']
    else: 
        survey_resource_types = resource_types

    return survey_resource_types    

def create_aws_env_def(env_name, provider, region, accountid, resource_types, compliance_families, rolename, interval=0):
    if interval != 0:
        scan_schedule_enabled = True
    else: 
        scan_schedule_enabled =  False     
    
    body = {
        "name": env_name,
        "provider": provider,
        "provider_options": {
            provider: {
            "regions": [region],
            "role_arn": "arn:aws:iam::" + accountid + ":role/" + rolename
            }
        },
        "compliance_families": compliance_families,
        "survey_resource_types": resource_types,
        "remediate_resource_types": [],
        "scan_schedule_enabled": bool(scan_schedule_enabled),
        "scan_interval": int(interval)
        }
    return body

def main():
   """
    Loop through each account and region to create an environment using Fugue API
    https://docs.fugue.co/api.html#example-create
    """
    
if provider.lower() == "azure" or provider.lower() == "aws_govcloud":
        print ("This script is only for AWS environment creation")
else:
    accounts= get_accounts_from_org(aws_profile_name)
    
    for name, acct_id in accounts.items():
        for region in regions: 
            # Set environment name
            if region == "*": 
                env_name = name + " - " + acct_id + " - " + "All Regions"
            else:
                env_name = name + " - " + acct_id + " - " + region
            print("Starting on creation for environment " + env_name + " and id: " + acct_id +  " and region: " + region)
                
            # Get resource types from Fugue API based on provider and region
            if region != "*":
                    survey_resource_types = get_resource_types(resource_types, region.lower(), provider.lower())
            else:
                    survey_resource_types = get_resource_types(resource_types, "us-east-1", provider.lower())    
            print("Resource types created for environment " + env_name + " and id: " + acct_id +  " and region: " + region)

            # Create JSON body  
            env_def = create_aws_env_def(env_name, provider.lower(), region.lower(), acct_id, survey_resource_types, compliance_families, rolename, interval)
            print ("JSON body created for environment " + env_name + " and region: " + region)
            print ("Creating environment for " + env_name + " and id: " + acct_id +  " and region: " + region)

            # Create environment
            resp = create_env('environments', env_def)
                
            if resp.status_code != 201:
                print('Environment creation failed for Account: ' + acct_id + ' with response code: {}'.format(resp.status_code) + ' and reason: {}'.format(resp.text) + "\n") 
            else:
                env_id =resp.json()['id'] 
                print ('Environment created for Account: ' + acct_id + ' with environment name: ' + resp.json()['name'] + ' and environment id: ' + resp.json()['id'] + "\n") 
 
if __name__ == '__main__':
    main()            
