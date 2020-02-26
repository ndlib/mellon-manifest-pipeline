# handler.py
""" Module to launch application """

import os
from pathlib import Path
import sys
where_i_am = os.path.dirname(os.path.realpath(__file__))
sys.path.append(where_i_am)
sys.path.append(where_i_am + "/dependencies/")
from harvest_aleph_marc import HarvestAlephMarc  # noqa: #502
from dependencies.pipelineutilities.pipeline_config import get_pipeline_config  # noqa: E402
import dependencies.sentry_sdk as sentry_sdk  # noqa: E402
from dependencies.sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration  # noqa: E402


if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], integrations=[AwsLambdaIntegration()])


def run(event, context):
    """ Run the process to retrieve and process Aleph metadata. """
    _supplement_event(event)
    config = get_pipeline_config(event)
    if config:
        marc_records_url = "https://alephprod.library.nd.edu/aleph_tmp/marble.mrc"
        harvest_marc_class = HarvestAlephMarc(config, event, marc_records_url)
        harvest_marc_class.process_marc_records_from_stream()
    return event


def _supplement_event(event):
    """ Add additional nodes to event if they do not exist. """
    if 'ids' not in event:
        event['ids'] = []
    if 'local' not in event:
        event['local'] = False
    if 'ssm_key_base' not in event and 'SSM_KEY_BASE' in os.environ:
        event['ssm_key_base'] = os.environ['SSM_KEY_BASE']
    if 'local-path' not in event:
        event['local-path'] = str(Path(__file__).parent.absolute()) + "/../example/"
    return


# setup:
# export SSM_KEY_BASE=/all/new-csv
# aws-vault exec testlibnd-superAdmin --session-ttl=1h --assume-role-ttl=1h --
# python -c 'from handler import *; test()'

# testing:
# python 'run_all_tests.py'
def test(identifier=""):
    """ test exection """
    event = {}
    event['local'] = False
    event = run(event, {})
    print(event)
