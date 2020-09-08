import urllib.request
import re
from bs4 import BeautifulSoup


def get_term_list(termuri):
    matches = re.findall(r"^.*[/]([0-9]*)$", termuri)
    if not matches:
        return []

    id = matches[0]
    url = "http://www.getty.edu/vow/AATHierarchy?find=&logic=AND&note=&page=1&subjectid=" + id
    with urllib.request.urlopen(url) as response:
        soup = BeautifulSoup(response.read())
        all = soup.select('a[href*="http://www.getty.edu/vow/"]')

        result = []
        for tag in all:
            if tag.text:
                result.append(tag.text)
        return result


        result = ""
        for line in lines:
            line = str(line)
            if 'http://www.getty.edu/vow/' in line:
                print(line)
                print(re.match(r"[<]A.*[>](.*)[<][/]A[>]", line))
                result += line

        # take results from hierarchy page and return a csv list
        result = re.sub("[\".\&\(\[\<].*?[;\)\]\>]", "", result)
        result = re.sub("\n\n", "\n", result)
        result = re.sub("\n", ", ", result)
        results = result.split(', ')

    print(results)
    return results
