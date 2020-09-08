import _set_path  # noqa
import os
from datetime import datetime, timedelta
from finalizeStep import FinalizeStep
from pipeline_config import load_pipeline_config, cache_pipeline_config
import sentry_sdk as sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[AwsLambdaIntegration()]
    )


def run(event, context):
    config = load_pipeline_config(event)

    # used to indicate to the choice in the step functions if the step has finished yet
    event['finalize_complete'] = False
    finalize_quittime = datetime.utcnow() + timedelta(seconds=config['seconds-to-allow-for-processing'])

    setup_config_for_restarting_step(config)
    finalize_run_limit = 10
    if config['finalize_run_number'] > finalize_run_limit:
        event['error_found'] = True
        event['finalize_error'] = str(config['finalize_run_number']) + ' finalize runs exceeded limit of ' + str(finalize_run_limit)
    else:
        for id in config.get("ids"):
            if id not in config['finalize_completed_ids']:
                step = FinalizeStep(id, config)
                # step.error = config.get("unexpected", "")
                # if not step.error:
                #    step.manifest_metadata = json.loads(mu.s3_read_file_content(s3_bucket, s3_schema_path))
                step.run()
                config['finalize_completed_ids'].append(id)

            if break_to_restart_step(finalize_quittime):
                break

        # have we processed all the fields.
        event['finalize_complete'] = finalize_is_complete(config)

        if "unexpected" in event:
            event['error_found'] = True
        else:
            event['error_found'] = False

    cache_pipeline_config(config, event)

    return event


def finalize_is_complete(config):
    return set(config['ids']) == set(config['finalize_completed_ids'])


def break_to_restart_step(finalize_quittime):
    return finalize_quittime <= datetime.utcnow()


def setup_config_for_restarting_step(config):
    if 'finalize_completed_ids' not in config:
        config['finalize_completed_ids'] = []

    if 'finalize_run_number' not in config:
        config['finalize_run_number'] = 0

    config['finalize_run_number'] = config['finalize_run_number'] + 1


# python -c 'from handler import *; test()'
def test():
    event = {
        'ssm_key_base': '/all/marble-manifest-prod',
        'config-file': '2020-04-15-13:15:10.365990.json',
        'process-bucket': 'marble-manifest-prod-processbucket-13bond538rnnb',
        'errors': []
    }

    print(run(event, {}))
