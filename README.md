# Fugue (Part of Snyk) Common Utility Scripts
## Purpose
This repository contains scripts that enable Fugue users to programmatically onboard Amazon Web Services (AWS) accounts, Miscrosoft Azure subscriptions, and Google Cloud projects as [Fugue (part of Snyk)](https://riskmanager.fugue.co) environments.

## How to use these scripts
### Prerequisites
1. An active Fugue account (register for an account [here](https://riskmanager.fugue.co/register)).
2. Active Fugue API credentials created using [these instructions](https://docs.fugue.co/api.html#getting-started-create-client-id-and-secret) and saved as environment variables `FUGUE_API_ID` and `FUGUE_API_SECRET`.
3. Python v3.6 or above.
4. `pip` version 22.2 or above.
5. Cloud provider credentials saved locally according to provider specifications.

### Getting started
Begin by cloning this repository locally, changing your working directory to `common-utility-scrips`, then use `pip` to install the packages required for execution of these scripts:
```
git clone https://github.com/fugue/common-utility-scripts.git
cd common-utility-scripts
pip install -r requirements.txt
```

### Select the right script for your needs
- **AWS options**:
  - Use [this script](env_creation_AWS_accounts.py) to create Fugue environments for a list of AWS accounts and regions.
  - Use [this script](env_creation_AWS_org.py) to create Fugue environments for a list of accounts and regions, extracted from AWS Organizations.
  - Use [this script](env_creation_AWS_govcloud_accounts.py) to create Fugue environments for a list of AWS GovCloud accounts and regions.
- **Microsoft Azure options**:
  - Use [this script](env_creation_AZURE_subscriptions.py) to create Fugue environments for a list of Azure subscriptions with listed credentials.
  - Use [this script](env_creation_AZURE_subscriptions_cli.py) to create Fugue environments for a list of Azure subscriptions with listed credentials. Will ask for secret at command prompt instead of having them listed in the file as plain text.
- **Google Cloud**: use [this script](env_creation_Google.py) to create Fugue environments for a list of active Google projects, extracted from Google Organization.

### Define the parameters for your selected script
#### Common parameters
| Parameter   | Options |
| ----------- | ----------- |
| `provider` | `aws`, `aws_govcloud`, `azure`, `google` |
| `compliance_families` | `AWS-Well-Architected_v2020-07-02`, `CIS-AWS_v1.2.0`, `CIS-AWS_v1.3.0`, `CIS-AWS_v1.4.0`, `CIS-Azure_v1.1.0`, `CIS-Azure_v1.3.0`, `CIS-Docker_v1.2.0`, `CIS-Google_v1.1.0`, `CIS-Google_v1.2.0`, `CIS-Controls_v7.1`, `CSA-CCM_v3.0.1`, `GDPR_v2016`, `HIPAA_v2013`, `ISO-27001_v2013`, `NIST-800-53_vRev4`, `PCI-DSS_v3.2.1`, `SOC-2_v2017`, `FBP` (AWS & AWS GovCloud only), `Custom`. For multiple compliance families, use `["ComplianceFamilyA", "ComplianceFamilyB"]`.|
| `interval` | Scan interval in seconds. Default is 24hrs (or `86400` seconds). |
| `allow_dups` | Default = `False`. Flag to allow duplicate environment creation in Fugue. If set to `False`, a list of existing environment will be retrieved from Fugue and only accounts not in Fugue will be created. |



#### AWS parameters
| Parameter   | Options |
| ----------- | ----------- |
| `regions`      | `us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`, `ap-south-1`, `ap-northeast-2`, `ap-southeast-1`, `ap-southeast-2`, `ap-northeast-1`, `ca-central-1`, `eu-central-1`, `eu-west-1`, `eu-west-2`, `eu-west-3`, `eu-south-1`, `eu-north-1`, `me-south-1`, `sa-east-1`, `us-gov-east-1`, `us-gov-west-1`. For multiple regions, use `["region-a", "region-b"]`. For all supported regions, use `["*"]`. |
| `resource_types` | Default value is `All`, which will invoke another Fugue API call to retrieve supported list of resources types. To specify a limited set of resource types, use this syntax: `["AWS.ACM.Certificate", "AWS.ACMPCA.CertificateAuthority"]`. Refer to [Fugue's Service Coverage](https://docs.fugue.co/servicecoverage.html) for a list of supported resource types. |
| `rolename` | Name of the IAM Role created in the accounts. This assumes the roles have already been created with the required permission for each of the accounts already exist in the target AWS accounts with the correct policy attached. |
| `accounts` | Map of AWS Account Name and Account numbers (`{"account-name": "12345678910"}`) that needed to be loaded into Fugue. Environments are created with the names in the format "Name - id - region". |
| `aws_profile_name` | Profile name for AWS Org that allows the script to extract the list of active AWS accounts. |

#### Microsoft Azure parameters
| Parameter | Options |
| ----------- | ----------- |
| `subscriptions` | Map of Azure Application Name, credentials and Resource Groups that need to be loaded into Fugue in the format `"App Name": ["Tenant Id", "Subscription Id", "Application ID", "Client Secret", [Resource Groups]]`. Default for Resource Group value is `"*"` for automatically discovering and adding all resource groups. For selective resource groups, use the format `["example-rg","another-rg"]`. Environments are created with the App name. [Here](https://docs.fugue.co/setupazure.html#step-2a-connect-to-azure) is how to create these. |

#### Google Cloud parameters
| Parameter | Options |
| ----------- | ----------- |
| `service_account_email` | Service account email created for onboarding projects. Instructions [here](https://docs.fugue.co/setup-google.html#adding-a-google-organization-level-service-account). This assumes the service account has already been created with the required permission for each of the projects and it already exists in the target Organization. |
| `service_account_email_keyfile` | Path to JSON key file generated for the service account using the instructions [here](https://cloud.google.com/docs/authentication/production#cloud-console). |
| `projects` | Map of Google Cloud project names and IDs (`{"project A": "project-a-id"}`) that needed to be loaded into Fugue. Environments are created with the names in the format "Name - id". |

### Execute the script
Once you have modified your selected script's parameters according to your needs, execute the script using Python:

```
python3 <your script here>.py
```

### Additional resources
For more information about Fugue, see [fugue.co](https://www.fugue.co) and [docs.fugue.co](https://docs.fugue.co).