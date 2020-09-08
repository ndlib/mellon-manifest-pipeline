import _set_path
import json
import csv
with open('output.csv', 'w', newline='') as csvfile:

    with open('./count_terms.json') as json_file:
        data = json.load(json_file)
        wr = csv.writer(csvfile, delimiter=',',
                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
        wr.writerow([
            'term',
            'count',
            'source',
            'uri'
        ])
        for id, row in data.items():
            wr.writerow([row['name'], row['count'], row['type'], row['uri']])
