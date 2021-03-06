"""This module is used in the step functions init lambda to setup data for the manifest part of the pipeline."""

import _set_path  # noqa
import os
import json
from helpers import get_file_ids_to_be_processed, get_all_file_ids, generate_config_filename

from pipelineutilities.pipeline_config import setup_pipeline_config, cache_pipeline_config
from pipelineutilities.s3_helpers import get_matching_s3_objects

import sentry_sdk as sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[AwsLambdaIntegration()]
    )


def run(event, context):
    if 'ssm_key_base' not in event and not event.get('local', False):
        event['ssm_key_base'] = os.environ['SSM_KEY_BASE']

    # name  config file for rhe pipeline to use
    event['config-file'] = generate_config_filename()
    event['errors'] = []
    config = setup_pipeline_config(event)

    if event.get('ids'):
        config['ids'] = event['ids']
    else:
        all_files = get_matching_s3_objects(config['process-bucket'], config['process-bucket-data-basepath'] + "/")
        if event.get("run_all_ids", False):
            config['ids'] = list(get_all_file_ids(all_files, config))
        else:
            config['ids'] = list(get_file_ids_to_be_processed(all_files, config))

    # reset the event because the data has been moved to config
    event = {
        'config-file': config['config-file'],
        'process-bucket': config['process-bucket'],
        'errors': config['errors'],
        'local': event.get('local', False)
    }

    cache_pipeline_config(config, event)
    event['ecs-args'] = [json.dumps(event)]

    return event


# python -c 'from handler import *; test()'
def test():
    data = {}
    # data['local'] = True
    # data['local-path'] = str(Path(__file__).parent.absolute()) + "/../example/"
    # data['process-bucket-csv-basepath'] = ""
    data['ssm_key_base'] = '/all/marble-manifest-prod'
    data['ids'] = [
        '1934.007.001'
    ]
    data['local'] = True

    print(run(data, {}))
