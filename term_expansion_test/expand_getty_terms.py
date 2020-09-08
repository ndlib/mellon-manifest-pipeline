import _set_path
import json
import item_data
import re

with open('./all_terms.json') as json_file:
    data = json.load(json_file)
    loc_lookups = []
    for id, term in data.items():
        if data[id]['authority'] == "LOC" or data[id]['authority'] == 'lcsh':
            loc_lookups.append(term['term'])
            data[id]["all_categories"] = term['term'].split("--")
            print(item_data.get_item_data(term))
        elif term['authority'] == "AAT" or term['authority'] == 'IA':
            data[id]["all_categories"] = item_data.get_item_data(term)
        else:
            loc_lookups.append(term['term'])
            data[id]["all_categories"] = term['term'].split("--")
            print("skipped", term)


with open("all_terms_categories.json", "w") as write_file:
    json.dump(data, write_file)

with open("all_loc_to_lookup.json", "w") as write_file:
    json.dump(loc_lookups, write_file)
