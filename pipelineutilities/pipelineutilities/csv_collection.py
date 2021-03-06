# import csv
import json
import os
import boto3
# from io import StringIO


def load_image_data(id, config):
    if config.get('local', False):
        return load_image_from_file(id, config)
    else:
        return load_image_from_s3(config['process-bucket'], config['process-bucket-read-basepath'], id, config)


def load_image_from_file(id, config):
    filepath = config['local-path'] + "/" + id + "/" + config['image-data-file']
    try:
        with open(filepath, 'r') as input_source:
            source = input_source.read()
        input_source.close()
    except FileNotFoundError:
        return {}

    return json.loads(source)


def load_image_from_s3(s3Bucket, s3Path, id, config):
    s3Path = s3Path + "/" + id + "/" + config['image-data-file']

    try:
        content_object = boto3.resource('s3').Object(s3Bucket, s3Path)
        source = content_object.get()['Body'].read().decode('utf-8')
        return json.loads(source)
    except boto3.resource('s3').meta.client.exceptions.NoSuchKey:
        return {}


def _augment_row_data(row, all_image_data, config):
    _turn_strings_to_json(row)
    _fix_ids(row)
    _check_creator(row)
    _add_additional_paths(row, config)
    _add_image_dimensions(row, all_image_data, config)


# turns out that the json method is changing these to floats
# even though my initial test said they were going to fail with the type TypeError
def _fix_ids(row):
    row["id"] = str(row["id"])
    row["collectionId"] = str(row["collectionId"])
    row["parentId"] = str(row["parentId"])


def _turn_strings_to_json(row):
    for key in row.keys():
        if ("{" in row[key] and "}" in row[key] or "[" in row[key] and "]" in row[key]):
            try:
                row[key] = json.loads(row[key])
            # we are simply testing if this is valid json if it is not and fails do nothing
            # i realize this is an antipattern
            except (ValueError, TypeError):
                pass


def _check_creator(row):
    if not (row.get("creators", False) or row.get('creators')) and (row.get("level") == "collection" or row.get("level") == "manifest"):
        row["creators"] = [{"fullName": "unknown"}]


def _add_additional_paths(row, config):
    level = row.get('level')
    if level == "file":
        paths = _file_paths(row, config)
    elif level == "manifest" or level == "collection":
        paths = _manifest_paths(row, config)
    else:
        if level is None:
            level = "NoneType"
        raise ValueError("Level must be one of ('collection', 'manifest', 'file').  You passed: " + level)
    row.update(paths)


def _file_paths(row, config):
    return {
        "iiifResourceId": "canvas" + '/' + row.get('id', '').replace('/', '%2F')
    }


def _manifest_paths(row, config):
    return {
        "iiifResourceId": "manifest" + '/' + row.get('id', '').replace('/', '%2F')
    }


def _add_image_dimensions(row, all_image_data, config):
    level = row.get('level')
    if level != "file":
        row.update({"width": None, "height": None})
        return

    image_key = os.path.splitext(row.get('id'))[0]
    image_data = all_image_data.get(image_key, {})

    ret = {
        "height": image_data.get('height', False),
        "width": image_data.get('width', False)
    }

    if not ret["height"]:
        ret["height"] = config['canvas-default-height']

    if not ret["width"]:
        ret["width"] = config['canvas-default-width']

    row.update(ret)


# python -c 'from csv_collection import *; test()'
def test():
    from pipeline_config import setup_pipeline_config
    event = {"local": False}
    event['local-path'] = '/Users/jhartzle/Workspace/mellon-manifest-pipeline/process_manifest/../example/'

    event['ssm_key_base'] = "/all/marble-manifest-deployment/prod"
    config = setup_pipeline_config(event)

    # s3 libnd
    config['local'] = False
    # for id in ['1954.030']:
    #     parent = load_csv_data(id, config)
    #     print(parent.object['creators'][0])
    # return
    # # local
    # config['local'] = True
    # for id in ['parsons', '1976.057']:
    #     parent = load_csv_data(id, config)
    #     print(parent.get('title'))
    #     print(parent.get('height'))
    #
    #     for file in parent.files():
    #         print(file.get("height"))
