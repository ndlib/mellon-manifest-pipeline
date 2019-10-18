import os
import boto3
import json


def run(event, context):
    event.update(get_config())
    event['event_id'] = event.get('id')
    event['ecs-args'] = [json.dumps(event)]
    event['metadata-source-type'] = determine_source_type(event)
    return event


def determine_source_type(event):
    s3 = boto3.resource('s3')

    prefix = os.path.join(event["process-bucket-read-basepath"], event["id"]) + "/"
    result = s3.meta.client.list_objects(Bucket=event["process-bucket"], Prefix=prefix, Delimiter='/')
    keys = []

    for o in result.get('Contents'):
        id = o.get('Key').replace(prefix, "")
        keys.append(id)

    if (event['descriptive-mets-file'] in keys and event['structural-mets-file'] in keys):
        return "mets"
    elif (event["main-csv"] in keys and event['items-csv'] in keys):
        return 'csv'

    raise Exception('unable to determine metadata source type from {}'.format(keys))


# retrieve configuration from parameter store
def get_config():
    config = {
        "process-bucket-read-basepath": 'process',
        "process-bucket-write-basepath": 'finished',
        "image-server-bucket-basepath": '',
        "manifest-server-bucket-basepath": '',
        "items-csv": 'items.csv',
        "main-csv": 'main.csv',
        "descriptive-mets-file": "descriptive_metadata_mets.xml",
        "structural-mets-file": "structural_metadata_mets.xml",
        "canvas-default-height": 2000,
        "canvas-default-width": 2000,
        "image-data-file": "image_data.json",
        "schema-file": "schema.json"
    }

    # read the keys we want out of ssm
    client = boto3.client('ssm')
    paginator = client.get_paginator('get_parameters_by_path')
    path = os.environ['SSM_KEY_BASE'] + '/'
    page_iterator = paginator.paginate(
        Path=path,
        Recursive=True,
        WithDecryption=False,)

    response = []
    for page in page_iterator:
        response.extend(page['Parameters'])

    for ps in response:
        value = ps['Value']
        # change /all/stacks/mellon-manifest-pipeline/<key> to <key>
        key = ps['Name'].replace(path, '')
        # add the key/value pair
        config[key] = value

    config['image-server-base-url'] = "https://" + config['image-server-base-url'] + ':8182/iiif/2'
    config['manifest-server-base-url'] = "https://" + config['manifest-server-base-url']
    config['noreply-email-addr'] = os.environ.get('NO_REPLY_EMAIL', '')
    config['troubleshoot-email-addr'] = os.environ.get('TROUBLESHOOTING_EMAIL', '')

    return config


# python -c 'from handler import *; test()'
def test(id):
    if (not os.environ['SSM_KEY_BASE']):
        print("you must set an SSM_KEY_BASE for parameter store in the environment")
        return

    if (not id):
        print("you must pass an id to test")

    data = {"id": id}
    print(run(data, {}))
