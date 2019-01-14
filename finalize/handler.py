import os, sys, json
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from finalizeStep import finalizeStep

def run(event, context):
    step = finalizeStep(event.get("id"), event.get("data"))
    step.run()

    return event

# python -c 'from handler import *; test()'
def test():
    with open("../example/example-input.json", 'r') as input_source:
        data = json.load(input_source)
    input_source.close()

    data = {
      "id": "example",
      "data": data
    }
    print(run(data, {}))