"""
main.py: třetí projekt do Engeto Online Python Akademie

author: Martin Gabriel
email: gabmar@post.cz
"""

import sys
import validators
import requests as rq
from bs4 import BeautifulSoup as bs
from pprint import pprint

url_example = "https://www.volby.cz/pls/ps2017/ps3?xjazyk=CZ"


def get_content(url):
    content = rq.get(url)
    if content.status_code != 200:
        print(f"Something went wrong. Could not get website content.\n Status code: {content.status_code}")
        return None
    else:
        return content


def parse_content(content):
    return bs(content.text, features="html.parser")


def get_html(url):
    content = get_content(url)
    if content is None:
        return content
    parsed_content = parse_content(content)

    return parsed_content


def input_validation():

    if len(sys.argv) != 3:
        print("This script need 2 arguments to run.", end="\n")
        return None

    url = sys.argv[1]
    output_file_name = sys.argv[2]

    #url validity check
    if not validators.url(url):
        print("The first argument of this script must be a valid url.")
        return None

    #output file name check
    invalid_chars = """<>:"/\\|?*"""

    for char in output_file_name:
        if char in invalid_chars:
            print(f"""Invalid characters in output file name. Output file name cannot contain the following characters: {invalid_chars}""")
            return None

    if output_file_name[-1] in " .":
        print("Output file name cannot contain trailing spaces and periods.")
        return None
    
    if not output_file_name[-4:] == ".csv":
        output_file_name = output_file_name + ".csv"

    return output_file_name


def find_district_links(parsed_content):
    links = []
    for a_tag in parsed_content.find_all("a", href=True):
        if a_tag['href'][:5] == 'ps32?':
            links.append("https://www.volby.cz/pls/ps2017nss/" + a_tag['href'])

    return links


def get_all_table_rows(parsed_content):
    tables = parsed_content.find_all("table")

    all_rows = []
    for table in tables:
        rows = table.find_all("tr")
        all_rows.append(rows)

    return all_rows


def main():
    
    output_file_name = input_validation()
    if output_file_name is None:
        sys.exit()
    url = sys.argv[1]

    parsed_html = get_html(url)

    district_links = find_district_links(parsed_html)

    #todo additional validation
    


    pprint(district_links)


if __name__ == "__main__":
    main()