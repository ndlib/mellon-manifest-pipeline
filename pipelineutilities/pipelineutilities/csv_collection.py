import csv
import json
import os
import boto3
from io import StringIO
from .s3_helpers import read_s3_file_content


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
        source = read_s3_file_content(s3Bucket, s3Path)
        return json.loads(source)
    except boto3.resource('s3').meta.client.exceptions.NoSuchKey:
        return {}


def load_csv_data(id, config):
    if config.get('local', False):
        objects = load_id_from_file(id, config)
    else:
        objects = load_id_from_s3(config['process-bucket'], config['process-bucket-csv-basepath'], id)

    all_image_data = load_image_data(id, config)

    for object in objects:
        _augment_row_data(object, all_image_data, config)

    return Item(objects[0], objects).collection()


def load_id_from_s3(s3Bucket, s3Path, id):
    s3Path = s3Path + "/" + id + ".csv"

    source = read_s3_file_content(s3Bucket, s3Path)
    f = StringIO(source)

    return list(csv.DictReader(f, delimiter=','))


def load_id_from_file(id, config):
    filepath = config['local-path'] + "/" + id + "/" + id + ".csv"

    with open(filepath, 'r') as input_source:
        source = input_source.read()
    input_source.close()
    f = StringIO(source)

    return list(csv.DictReader(f, delimiter=','))


class Item():

    def __init__(self, object, all_objects):
        self.object = object
        self.all_objects = all_objects

    def repository(self):
        return self.get('sourceSystem', 'aleph')

    def type(self):
        return self.get('level')

    def collection(self):
        return self._find_row(self.object.get('collectionId'))

    def parent(self):
        return self._find_row(self.object.get('parentId'))

    def get(self, key, default=False):
        return self.object.get(key, default)

    def children(self):
        children = []
        test_id = "".join(self.get('id').lower().split(" "))
        for row in self.all_objects:
            if "".join(row['parentId'].lower().split(" ")) == test_id:
                children.append(Item(row, self.all_objects))

        return children

    def files(self):
        ret = []

        for child in self.children():
            if child.type() == 'file':
                ret.append(child)
            else:
                ret = ret + child.files()

        return ret

    def _find_row(self, id):
        for this_row in self.all_objects:
            if this_row.get('id', False) == id:
                return Item(this_row, self.all_objects)

        return False


def _augment_row_data(row, all_image_data, config):
    _check_creator(row)
    _add_additional_paths(row, config)
    _add_image_dimensions(row, all_image_data, config)


def _check_creator(row):
    if not (row.get("creator", False) or row.get('creator')):
        row["creator"] = "unknown"


def _add_additional_paths(row, config):
    level = row.get('level')
    if level == "file":
        paths = _file_paths(row, config)
    elif level == "manifest" or level == "collection":
        paths = _manifest_paths(row, config)
    else:
        raise "invalid type passed to _addition_paths"

    row.update(paths)


def _file_paths(row, config):
    id_no_extension = os.path.splitext(row.get('id'))[0]
    uri_path = '/' + row.get('collectionId') + '%2F' + id_no_extension
    path = '/' + row.get('collectionId') + "/" + id_no_extension

    return {
        "iiifImageUri": config['image-server-base-url'] + uri_path,
        "iiifImageFilePath": "s3://" + config['image-server-bucket'] + path,
        "iiifUri": config["manifest-server-base-url"] + path + "/canvas",
        "iiifFilePath": "s3://" + config['manifest-server-bucket'] + path + "/canvas/index.json",
        "metsUri": "",
        "metsFilePath": "",
        "schemaUri": "",
        "schemaPath": "",
    }


def _manifest_paths(row, config):
    path = "/" + row.get('collectionId')
    if row.get('collectionId') != row.get('id'):
        path = path + "/" + row.get("id")

    return {
        "iiifImageUri": "",
        "iiifImageFilePath": "",
        "iiifUri": config["manifest-server-base-url"] + path + "/manifest",
        "iiifFilePath": "s3://" + config['manifest-server-bucket'] + path + "/manifest/index.json",
        "metsUri": config["manifest-server-base-url"] + path + "/mets.xml",
        "metsFilePath": "s3://" + config['manifest-server-bucket'] + path + "/mets.xml",
        "schemaUri": config["manifest-server-base-url"] + path,
        "schemaPath": "s3://" + config['manifest-server-bucket'] + path + "/index.json",
    }


def _add_image_dimensions(row, all_image_data, config):
    level = row.get('level')
    if level != "file":
        row.update({"width": "", "height": ""})
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
    from pipeline_config import get_pipeline_config
    event = {"local": True}
    event['local-path'] = '/Users/jhartzle/Workspace/mellon-manifest-pipeline/process_manifest/../example/'

    config = get_pipeline_config(event)

    # s3 libnd
    config['local'] = False
    for id in ['BPP1001_EAD', 'MSNCOL8500_EAD']:
        parent = load_csv_data(id, config)
        for file in parent.files():
            print(file.get("height"))

    # local
    config['local'] = True
    for id in ['parsons', '1976.057']:
        parent = load_csv_data(id, config)
        print(parent.get('title'))
        print(parent.get('height'))

        for file in parent.files():
            print(file.get("height"))
