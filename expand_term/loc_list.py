import urllib
import re


def get_loc_list(locuri):
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}
    response = urllib.urlopen(urllib.Request(locuri, headers=hdr))
    lines = response.readlines()
    result = ""
    for line in lines:
        result += line
    # take results from hierarchy page and return a csv list
    result = result.split("About this Item", 1)[-1]
    result = result.split("rights-and-access", 1)[0]
    result = result.lower()
    result = re.sub("</dd>", "; ", result)
    result = re.sub("</dt>", ": ", result)
    result = re.sub("[\n\r\t]", "", result)
    result = re.sub("; ;", ";", result)
    result = re.sub("[<].*?[>]", "", result)
    result = re.sub("  ", "", result)
    results = result.split("; ")
    return results
