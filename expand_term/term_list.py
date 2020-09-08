import urllib.request
import re


def get_term_list(termuri):
    with urllib.request.urlopen("http://www.python.org") as response:
        lines = response.readlines()
        result = ""
        for line in lines:
            print(line)
            if 'http://www.getty.edu/vow/' in line:
                result += line
        # take results from hierarchy page and return a csv list
        result = re.sub("[\".\&\(\[\<].*?[;\)\]\>]", "", result)
        result = re.sub("\n\n", "\n", result)
        result = re.sub("\n", ", ", result)
        results = result.split(', ')

    return results
