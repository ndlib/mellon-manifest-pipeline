import boto3
import json
from ProcessCsvInput import ProcessCsvInput
from pathlib import Path
import csv
from io import StringIO
from csv_to_schema import CsvToSchema
from mets_to_schema import MetsToSchema


def run(event, context):
    id = event.get("id")

    process_bucket = event['process-bucket']
    main_key = event['process-bucket-read-basepath'] + "/" + id + "/" + event['main-csv']
    items_key = event['process-bucket-read-basepath'] + "/" + id + "/" + event['items-csv']
    image_key = event['process-bucket-read-basepath'] + "/" + id + "/" + event["image-data-file"]
    event_key = event['process-bucket-read-basepath'] + "/" + id + "/" + event["event-file"]

    main_csv = read_s3_file_content(process_bucket, main_key)
    items_csv = read_s3_file_content(process_bucket, items_key)
    image_data = json.loads(read_s3_file_content(process_bucket, image_key))

    csvSet = ProcessCsvInput(event, main_csv, items_csv, image_data)
    csvSet.buildJson()

    write_s3_json(process_bucket, event_key, csvSet.result_json)

    return event


def read_s3_file_content(s3Bucket, s3Path):
    content_object = boto3.resource('s3').Object(s3Bucket, s3Path)
    return content_object.get()['Body'].read().decode('utf-8')


def write_s3_json(s3Bucket, s3Path, json_hash):
    s3 = boto3.resource('s3')
    s3.Object(s3Bucket, s3Path).put(Body=json.dumps(json_hash), ContentType='text/json')


def csv_to_dict(main_csv, items_csv):
    dict = {"items": []}
    f = StringIO(items_csv)
    reader = csv.DictReader(f, delimiter=',')
    for this_row in reader:
        if reader.line_num != 1:
            dict["items"].append(this_row)

    f = StringIO(main_csv)
    reader = csv.DictReader(f, delimiter=',')
    for this_row in reader:
        if reader.line_num == 2:
            dict.update(this_row)
            del dict["Metadata_label"]
            del dict["Metadata_value"]
        elif reader.line_num > 2:
            dict[this_row["Metadata_label"]] = this_row['Metadata_value']

    return dict


# python -c 'from handler import *; test()'
def test():
    current_path = str(Path(__file__).parent.absolute())

    with open(current_path + "/../example/item-one-image/config.json", 'r') as input_source:
        config = json.load(input_source)
    input_source.close()
    with open(current_path + "/../example/item-one-image/main.csv", 'r') as input_source:
        main_csv = input_source.read()
    input_source.close()
    with open(current_path + "/../example/item-one-image/items.csv", 'r') as input_source:
        items_csv = input_source.read()
    input_source.close()
    with open(current_path + "/../example/item-one-image/image-data.json", 'r') as input_source:
        image_data = json.load(input_source)
    input_source.close()

    with open(current_path + "/../example/item-one-image/descriptive_metadata_mets.xml", 'r') as input_source:
        mets_structural = input_source.read()
    input_source.close()

    # print(csv_to_dict(main_csv, items_csv))

    c = CsvToSchema(config, main_csv, items_csv, image_data)
    print(c.get_json())
    print(c.errors)

    b = MetsToSchema(config, mets_structural, {}, image_data)
    print(b.dict)
    csvSet = ProcessCsvInput(config, main_csv, items_csv, image_data)
    csvSet.buildJson()

    # print(csvSet.result_json)
