import urllib.request
from bs4 import BeautifulSoup
import re

def get_cona_ia_list(conaiauri):
    matches = re.findall(r"^.*[/]([0-9]*)$", conaiauri)
    if not matches:
        return []

    id = matches[0]
    url = "http://www.getty.edu/cona/CONAIconographyRecord.aspx?iconid=" + id
    try:
        with urllib.request.urlopen(url) as response:
            soup = BeautifulSoup(response.read())
            all = soup.select('table#HierarchyDetailTable a font')

            result = []
            for tag in all:
                if tag.text:
                    text = tag.text.replace(".", "")
                    result.append(text)

            return result

    except urllib.error.URLError:
        return []
