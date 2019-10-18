import urllib
import re


def get_cona_ia_list(conaiauri):
    response = urllib.urlopen(conaiauri)
    lines = response.readlines()
    result = ""
    for line in lines:
        result += line
    # take results from hierarchy page and return a csv list
    result = result.split('<div class="page">', 1)[-1]
    result = result.split('Sources:', 1)[0]
    result = result.lower()
    result = re.sub("<br>", "; ", result)
    result = re.sub("</td>", "; ", result)
    result = re.sub("[<].*?[>]", "", result)
    result = re.sub("[\n\r\t]", "", result)
    result = re.sub("; ;", ";", result)
    result = re.sub("  ", "", result)
    result = re.sub("\.\.", "", result)
    results = result.split("; ")
    return results
