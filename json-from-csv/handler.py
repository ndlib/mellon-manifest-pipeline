import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from processCsv import processCsv

def run(event, context):
    csvSet = processCsv(event.get("id"))
    csvSet.buildJson()
    event.update( { "data": csvSet.result_json })
    #print resulting json to STDOUT
    return event

# python -c 'from handler import *; test()'
def test():
    data = { "id": "example"}
    print(run(data, {}))
