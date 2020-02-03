import boto3
import csv
import re
import math
from io import StringIO
from pathlib import Path


def load_csv_data(id, config):
    if config.get('local', False):
        return load_id_from_file(id, config)
    else:
        return load_id_from_s3(config['process-bucket'], config['process-bucket-csv-basepath'], id)


def load_id_from_s3(s3Bucket, s3Path, id):
    s3Path = s3Path + "/" + id + ".csv"

    source = boto3.resource('s3').Object(s3Bucket, s3Path)
    source = source.get()['Body'].read().decode('utf-8')
    f = StringIO(source)

    objects = list(csv.DictReader(f, delimiter=','))
    return Item(objects[0], objects).collection()


def load_id_from_file(id, config):
    filepath = config['local-path'] + "csv_data/" + id + ".csv"

    with open(filepath, 'r') as input_source:
        source = input_source.read()
    input_source.close()
    f = StringIO(source)

    objects = list(csv.DictReader(f, delimiter=','))

    return Item(objects[0], objects).collection()


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


class DateTags():
    def __init__(self, item, field):
        self.item = item
        self.field = field
        self.date = self._find_date()
        self.years = self._pull_out_years()
        self.tags = self._find_tags()

    def _find_date(self):
        current_date_row = self.item.get(self.field, False)
        collection_date_row = self.item.collection().get(self.field, False)

        if current_date_row and current_date_row.lower() != 'undated':
            return current_date_row
        elif collection_date_row and collection_date_row.lower() != 'undated':
            return collection_date_row

        return False

    def _find_tags(self):
        return [self._year_to_ordinal(year) for year in self.years]

    def _year_to_ordinal(self, n):
        n = math.ceil(int(n) / 100)
        # https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
        return "%d%s Century" % (n, "tsnrhtdd"[(math.floor(n/10) % 10 != 1) * (n % 10 < 4) * n % 10::4])

    def _pull_out_years(self):
        exp = r"([0-9]{4})"
        matches = re.findall(exp, self.date)
        return list(matches)


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
        DateTags(parent, 'dateCreated')
        for file in parent.files():
            ""
            # print(file.get("filePath"))
    return
    # local
    config['local'] = True
    for id in ['parsons', '1976.057']:
        parent = load_csv_data(id, config)
        print(parent.get('title'))
        for file in parent.files():
            print(file.get("filePath"))
