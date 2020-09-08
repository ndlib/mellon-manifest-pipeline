import urllib.request
from bs4 import BeautifulSoup
import re
import os


def get_loc_list(term):
    stream = os.popen("cd ../../Loc-reconcile; /Users/jhartzle/.pyenv/shims/python search_cmd.py '" + term + "'")
    output = stream.read().strip()

    if not output:
        return []

    url = output + ".html"
    print(url)
#    try:
    with urllib.request.urlopen(url) as response:
        soup = BeautifulSoup(response.read())
        all = soup.select('li[rel="skos:broader"] a[property="skos:preflabel"]')
        print("all", all)
        result = []
        for tag in all:
            if tag.text:
                text = tag.text.replace(".", "")
                result.append(text)

        return result

#    except urllib.error.URLError:
#        return []
