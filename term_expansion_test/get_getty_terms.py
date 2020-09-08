import _set_path
import json
from pipelineutilities.s3_helpers import read_s3_json

bucket = "marble-manifest-prod-manifestbucket-lpnnaj4jaxl5"


all_terms = {}
with open('../../marble-website-starter/site/content/manifests.json') as json_file:
    data = json.load(json_file)
    for id in data['manifest_ids']:
        path = id + "/standard/index.json"
        record = read_s3_json(bucket, path)

        for term in record.get("subjects", []):
            term['source_id'] = id
            id = term.get("uri", False)
            if not id:
                id = term.get("term")
                id = id.replace("'", "")

            if not all_terms.get(id):
                if not term.get("authority", False):
                    term['authority'] = 'LOC'

                term['count'] = 1
                all_terms[id] = term

            else:
                all_terms[id]['count'] += 1


with open("all_terms.json", "w") as write_file:
    json.dump(all_terms, write_file)

exit()

all_terms = {}
with open('./snite_ids.json') as json_file:
    data = json.load(json_file)
    for id in data:
        path = id + "/standard/index.json"
        record = read_s3_json(bucket, path)

        for term in record.get("subjects", []):
            if not term.get("uri", False):
                term['count'] = 1
                all_terms[term['uri']] = term

            else:
                all_terms[term['uri']]['count'] += 1


with open("all_getty_terms.json", "w") as write_file:
    json.dump(all_terms, write_file)
