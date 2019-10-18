import urllib
import re


def get_term_list(termuri):
    response = urllib.urlopen(termuri)
    lines = response.readlines()
    result = ""
    for line in lines:
        if 'http://www.getty.edu/vow/' in line:
            result += line
    # take results from hierarchy page and return a csv list
    result = re.sub("[\".\&\(\[\<].*?[;\)\]\>]", "", result)
    result = re.sub("\n\n", "\n", result)
    result = re.sub("\n", ", ", result)
    results = result.split(', ')
    return results
