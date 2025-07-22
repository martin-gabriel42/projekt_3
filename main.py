"""
main.py: třetí projekt do Engeto Online Python Akademie

author: Martin Gabriel
email: gabmar@post.cz
"""

import sys
import validators
import requests as rq
import csv
from bs4 import BeautifulSoup as bs
from pprint import pprint


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


def get_district_links(parsed_content):
    links = []
    for a_tag in parsed_content.find_all("a", href=True):
        if a_tag['href'][:5] == 'ps32?':
            links.append("https://www.volby.cz/pls/ps2017nss/" + a_tag['href'])

    return links


def get_district_data(url):

    parsed_html = get_html(url)

    all_rows = [row for row in parsed_html.find_all("tr") if not row.find_all("th")]

    district_data = []
    
    for row in all_rows:

        district_info = {}
        district_info["link"] = "https://www.volby.cz/pls/ps2017nss/" + row.find("a")["href"]
        district_info["code"] = row.find_all("td")[0].get_text()
        district_info["municipality"] = row.find_all("td")[1].get_text()

        district_data.append(district_info)

    return district_data


def scrape_district(url):

    district_data = get_district_data(url)

    for district in district_data:
        municipality_data = get_municipality_data(district["link"])
        print("scaped municipality: ", district["municipality"])
        for key, value in municipality_data.items():
            district[key] = value

    return district_data


def get_municipality_data(url):

    parsed_html = get_html(url)

    all_tables = parsed_html.find_all("table")

    overview_table_data_row = all_tables[0].find_all("tr")[2].find_all("td")
    voter_data = {
        "registered voters": overview_table_data_row[3].get_text(),
        "total votes": overview_table_data_row[6].get_text(),
        "valid votes": overview_table_data_row[7].get_text(),
        "votes by party": None
    }
    
    party_vote_data = []
    for table in all_tables[1:]:
        all_rows = [row for row in table.find_all("tr") if not (row.find_all("th") or row.find_all(class_="hidden_td"))]
        for row in all_rows:
            all_cells = row.find_all("td")
            party_vote_data.append((all_cells[1].get_text(), all_cells[2].get_text()))

    voter_data["votes by party"] = party_vote_data
    #pprint(voter_data)

    return voter_data


def get_all_table_rows(parsed_content):
    tables = parsed_content.find_all("table")

    all_rows = []
    for table in tables:
        rows = table.find_all("tr")
        all_rows.append(rows)

    return all_rows


def csv_dumper(district_data, output_file_name):

    parties = list({party_data[0] for municipality_data in district_data for party_data in municipality_data["votes by party"]})

    headers = ["code", "municipality", "registered voters", "total votes", "valid votes"]
    for party in parties:
        headers.append(party)

    with open(output_file_name, "w+", newline='', encoding="utf-8") as f:
       
        writer = csv.DictWriter(f, fieldnames=headers, restval="0")
        writer.writeheader()
       
        for municipality_data in district_data:
            row_dict = dict()

            for key, value in municipality_data.items():
                if key not in ("link", "votes by party"):
                    row_dict[key] = value

            for key, value in municipality_data["votes by party"]:
                row_dict[key] = value

            writer.writerow(row_dict)


        


def main():

    url_example = "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2101"
    
    output_file_name = input_validation()
    if output_file_name is None:
        sys.exit()
    url = sys.argv[1]


    #pprint(get_district_data("https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2101"))
    #pprint(get_municipality_data("https://www.volby.cz/pls/ps2017nss/ps311?xjazyk=CZ&xkraj=2&xobec=529303&xvyber=2101"))

    district_data = scrape_district(url_example)

    #pprint(district_data)

    csv_dumper(district_data, output_file_name)



if __name__ == "__main__":
    main()