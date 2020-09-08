import _set_path
import json
import item_data
import re

with open('./all_terms_categories.json') as json_file:
    data = json.load(json_file)

    output = {}
    for id, term in data.items():
        for category in term['all_categories']:
            print(category)
            if not output.get(category, False):
                output[category] = {"count": 1, "ids": [], "uri": term.get('uri'), "type": [term["authority"]], "name": category}
            else:
                output[category]['count'] = output[category]['count'] + 1
                output[category]['type'].append(term["authority"])


for category, term in output.items():
    output[category]['type'] = set(output[category]['type'])


with open("count_terms.json", "w") as write_file:
    json.dump(output, write_file)
