"""
This is an example of using the Fugue API to output compliance results as CSV.

Follow instructions in the API User Guide to create a client ID and secret
that are used to authenticate with Fugue:

https://docs.fugue.co/api.html#api-user-guide

The client ID and secret may be passed to this script using the following
environment variables: FUGUE_API_ID and FUGUE_API_SECRET. Alternatively,
edit the script itself to set the values directly in this script.

This script should be run using Python 3 however it could be modified for
Python 2 compatibility if needed.

One dependency must be installed using pip: the requests library.
 * pip install requests

"""
from datetime import datetime
import json
import os
import requests


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


def list_environments():
    """
    Returns all environments present in your Fugue account.
    https://docs.fugue.co/_static/swagger.html#tag-environments
    """
    return get('environments')['items']


def list_scans(environment_id, max_items=10, status='SUCCESS'):
    """
    Returns the most recent successful scans on the specified environment.
    https://docs.fugue.co/_static/swagger.html#tag-scans
    """
    params = {
        'environment_id': environment_id,
        'status': status,
        'max_items': max_items,
    }
    return get('scans', params)['items']


def get_latest_scan(environment_id):
    """
    Returns the most recent successful scan of the specified environment.
    None is returned if there has not yet been a successful scan.
    """
    scans = list_scans(environment_id, max_items=1)
    if scans:
        return scans[0]
    return None


def get_compliance_by_rules(scan_id):
    """
    Lists compliance results by rule for a scan.
    """
    items = []
    offset = 0
    while True:
        params = {'offset': offset}
        response = get('scans/%s/compliance_by_rules' % scan_id, params)
        items.extend(response['items'])
        if not response['is_truncated']:
            break
        offset = response['next_offset']
    return items


def format_message(message):
    """
    Ensures the message does not have commas since that would interfere with
    CSV formatting.
    """
    return message.replace(',', ' ').replace('"', '')


def records_from_failed_type(family, control, failure):
    """
    Builds a spreadsheet record for a failure for a resource type.
    """
    return [dict(
        family=family,
        control=control,
        resource_type=failure['resource_type'],
        resource_id=None,
        message=format_message(message),
    ) for message in failure['messages']]


def records_from_failed_resource(family, control, failure):
    """
    Builds a spreadsheet record for a failure for a single resource.
    """
    return [dict(
        family=family,
        control=control,
        resource_type=failure['resource']['resource_type'],
        resource_id=failure['resource']['resource_id'],
        message=format_message(message),
    ) for message in failure['messages']]


def records_from_unsurveyed_type(family, control, resource_type):
    """
    Builds a spreadsheet record for a resource type that was not surveyed.
    """
    return [dict(
        family=family,
        control=control,
        resource_type=resource_type,
        resource_id=None,
        message=format_message('Resource type was not scanned'),
    )]


def records_from_rule(rule):
    """
    Generator that yields spreadsheet records for a given compliance rule.
    """
    family = rule['family']
    control = rule['rule']
    for failure in rule['failed_resource_types']:
        for record in records_from_failed_type(family, control, failure):
            yield record
    for failure in rule['failed_resources']:
        for record in records_from_failed_resource(family, control, failure):
            yield record
    for failure in rule['unsurveyed_resource_types']:
        for record in records_from_unsurveyed_type(family, control, failure):
            yield record


def record_with_metadata(record, environment, scan):
    """
    Adds environment and scan metadata to a compliance record.
    """
    day, tod = date_from_timestamp(scan['finished_at'])
    record.update(dict(
        environment_id=environment['id'],
        environment_name=environment['name'],
        account=account_from_environment(environment),
        region=region_from_environment(environment),
        scan_id=scan['id'],
        day=day,
        time=tod,
    ))
    return record


def account_from_environment(environment):
    """
    Returns the AWS account ID or Azure subscription ID of the environment.
    """
    provider_opts = environment['provider_options']
    if environment['provider'] == 'aws':
        return account_from_role_arn(provider_opts['aws']['role_arn'])
    elif environment['provider'] == 'aws_govcloud':
        return account_from_role_arn(provider_opts['aws_govcloud']['role_arn'])
    elif environment['provider'] == 'azure':
        return provider_opts['azure']['subscription_id']
    return '-'


def region_from_environment(environment):
    """
    Returns the AWS region of the environment.
    """
    provider_opts = environment['provider_options']
    if environment['provider'] == 'aws':
        if 'region' in provider_opts['aws']:
            return provider_opts['aws']['region']
        else:
            return ','.join(provider_opts['aws']['regions'])
    elif environment['provider'] == 'aws_govcloud':
        return provider_opts['aws_govcloud']['region']
    return '-'


def account_from_role_arn(role_arn):
    """
    Returns the AWS account ID portion of the given IAM role ARN.
    """
    parts = role_arn.split(':')
    if len(parts) == 6:
        return parts[4]
    return '-'


def date_from_timestamp(ts):
    """
    Returns a tuple containing (date, time) strings for a given Unix timestamp.
    """
    day = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
    tod = datetime.utcfromtimestamp(ts).strftime('%H:%M:%S')
    return (day, tod)


# Columns to be output as CSV
COLUMNS = [
    'environment_name',
    'account',
    'region',
    'family',
    'control',
    'resource_type',
    'resource_id',
    'day',
    'time',
    'message',
    'environment_id',
    'scan_id',
]


def value_or_default(value, default='-'):
    if value is not None:
        return value
    return default


def quote_csv_value(value):
    """
    Surrounds a string value with quoting to avoid excel autoformatting.
    Ref: https://stackoverflow.com/a/165052/9806588
    """
    if len(value) < 64:
        return '"=""%s"""' % value
    return value


def csv(values):
    return ",".join(values)


def format_value(column_name, value):
    # All columns but the message column should be wrapped with double quotes
    # to avoid excel autoformatting behavior.
    value = value_or_default(value)
    if column_name != 'message':
        value = quote_csv_value(value)
    return ' '.join(value.split())


def format(record, fmt='csv'):
    if fmt == 'csv':
        return csv([format_value(col, record[col]) for col in COLUMNS])
    else:
        return json.dumps(record)


def main():
    """
    Loop over all Fugue environments in your account and output compliance
    results from the most recent scan in each. Output is in CSV format.
    """
    now = datetime.now().strftime('%Y-%m-%d-%H%M%S')
    filename = 'compliance-%s.csv' % now
    with open(filename, 'w') as f:
        print(csv(COLUMNS), file=f)
        for env in list_environments():
            scan = get_latest_scan(env['id'])
            if not scan:
                continue
            for rule in get_compliance_by_rules(scan['id']):
                for record in records_from_rule(rule):
                    record = record_with_metadata(record, env, scan)
                    print(format(record), file=f)
    print('Wrote %s' % f.name)


if __name__ == '__main__':
    main()
