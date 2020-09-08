# handler.py
""" Module to launch application """
import _set_path  # noqa
import json
import io
import os
import time
from datetime import datetime, timedelta
from harvest_oai_eads import HarvestOaiEads  # noqa: #502
from pipelineutilities.pipeline_config import setup_pipeline_config  # noqa: E402
import sentry_sdk as sentry_sdk  # noqa: E402
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration  # noqa: E402
from pipelineutilities.add_files_to_json_object import AddFilesToJsonObject
from pipelineutilities.add_paths_to_json_object import AddPathsToJsonObject
from pipelineutilities.fix_creators_in_json_object import FixCreatorsInJsonObject
from pipelineutilities.s3_helpers import read_s3_json
from pipelineutilities.save_standard_json import save_standard_json


def run(event: dict, context: dict):
    """ Run the process to retrieve and process ArchivesSpace metadata.

    Information on the API can be found here:
        http://archivesspace.github.io/archivesspace/api/ """
    _supplement_event(event)
    _init_sentry()
    config = setup_pipeline_config(event)
    if not event.get("ids", False):
        event["ids"] = read_ids_from_s3(config['process-bucket'], "source_system_export_ids.json", "ArchivesSpace")
    # config['rbsc-image-bucket'] = "libnd-smb-rbsc"
    start_time = time.time()
    time_to_break = datetime.now() + timedelta(seconds=config['seconds-to-allow-for-processing'])
    print("Will break after ", time_to_break)
    harvest_oai_eads_class = HarvestOaiEads(config)
    add_files_to_json_object_class = AddFilesToJsonObject(config)
    add_paths_to_json_object_class = AddPathsToJsonObject(config)
    fix_creators_in_json_object_class = FixCreatorsInJsonObject(config)
    ids = event.get("ids", [])
    while len(ids) > 0 and datetime.now() < time_to_break:
        standard_json = harvest_oai_eads_class.get_standard_json_from_archives_space_url(ids[0])
        if standard_json:
            standard_json = add_files_to_json_object_class.add_files(standard_json)
            standard_json = add_paths_to_json_object_class.add_paths(standard_json)
            standard_json = fix_creators_in_json_object_class.fix_creators(standard_json)
            save_standard_json(config, standard_json)
            print("ArchivesSpace ead_id = ", standard_json.get("id", ""), " source_system_url = ", ids[0], int(time.time() - start_time), 'seconds.')
        del ids[0]
    event['archivesSpaceHarvestComplete'] = (len(ids) == 0)
    event['eadsSavedToS3'] = os.path.join(config['process-bucket'], config['process-bucket-data-basepath'])
    return event


def _supplement_event(event: dict) -> dict:
    if 'archivesSpaceHarvestComplete' not in event:
        event['archivesSpaceHarvestComplete'] = False
    if 'ssm_key_base' not in event and 'SSM_KEY_BASE' in os.environ:
        event['ssm_key_base'] = os.environ['SSM_KEY_BASE']
    return event


def read_ids_from_s3(process_bucket: str, s3_path: str, section: str) -> list:
    ids = []
    try:
        json_hash = read_s3_json(process_bucket, s3_path)
        if section in json_hash:
            ids = json_hash[section]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        print("Control file does not exit:", process_bucket, s3_path)
    return ids


def _init_sentry():
    if 'SENTRY_DSN' in os.environ:
        sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], integrations=[AwsLambdaIntegration()])


# setup:
# export SSM_KEY_BASE=/all/new-csv
# export SSM_KEY_BASE=/all/marble-manifest-deployment/prod
# aws-vault exec testlibnd-superAdmin --session-ttl=1h --assume-role-ttl=1h --
# python -c 'from handler import *; test()'
def test(identifier=""):
    """ test exection """
    filename = 'event.json'
    if os.path.exists(filename):
        with io.open(filename, 'r', encoding='utf-8') as json_file:
            event = json.load(json_file)
    else:
        event = {}
        event["local"] = False
        event["ids"] = [
            # "https://archivesspace.library.nd.edu/repositories/2/resources/1652",  # Collegiate Jazz Festival
            # "https://archivesspace.library.nd.edu/repositories/3/resources/1631",
            # "https://archivesspace.library.nd.edu/repositories/3/resources/1644",  # Irish Broadsides
        ]
        # event["ids"] = ["https://archivesspace.library.nd.edu/repositories/3/resources/1492"]  # Parsons Journals
        # event["ids"] = ["https://archivesspace.library.nd.edu/repositories/3/resources/1524"]
        # event['ids'] = ["https://archivesspace.library.nd.edu/repositories/3/resources/2038"]
        # event['ids'] = ["https://archivesspace.library.nd.edu/repositories/3/resources/1567"]
    event = run(event, {})

    if not event['archivesSpaceHarvestComplete']:
        with open('event.json', 'w') as f:
            json.dump(event, f, indent=2)
    else:
        try:
            os.remove('event.json')
        except FileNotFoundError:
            pass
    print(event)
