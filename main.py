"""
main.py: třetí projekt do Engeto Online Python Akademie

author: Martin Gabriel
email: gabmar@post.cz
"""

#builtins
import sys
import csv
import time

#third party
import validators
import requests as rq
from bs4 import BeautifulSoup as bs


#simple get request
#returns None if request was unsuccessful
def get_content(url):
    content = rq.get(url)
    if content.status_code != 200:
        print(f"Something went wrong. Could not get website content.\n Status code: {content.status_code}")
        return None
    else:
        return content

#parses content of a get request using beautifulsoup
def parse_content(content):
    return bs(content.text, features="html.parser")


def get_html(url):
    '''
    Makes a get request to the target server and parses the resulting html using beautifulsoup.
    Retruns parsed html if successful, returns None if not.
    '''
    content = get_content(url)
    if content is None:
        return content
    return parse_content(content)


def retry_get(url):
    '''
    Retries a get request 5 times. Returns parsed html if succesful. Returns None if not.
    '''
    
    for _ in range(5):
        parsed_html = get_html(url)
        if parsed_html is not None:
            break
    
    return parsed_html


def get_all_district_links():
    '''
    Gets all valid url links leading to a district. Used in script input arguments validation.
    '''

    url = "https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ"
    parsed_html = get_html(url)

    if parsed_html is None:
        parsed_html = retry_get(url)
    if parsed_html is None:
        print("Something went wrong. Server not responding properly.")
        return None

    all_links_dict = dict()
    all_rows = [row for row in parsed_html.find_all("tr") if not row.find_all("th")]
    for row in all_rows:
        all_cells = row.find_all("td")
        #print(all_cells[1], all_cells[3], sep="\n")
        all_links_dict[all_cells[1].get_text()] = "https://www.volby.cz/pls/ps2017nss/" + all_cells[3].find("a", href=True)['href']
    
    all_links_dict.pop("Zahraničí")

    return all_links_dict


def input_validation():
    '''
    Checks validity of script input arguments.
    Returns the output file name if inputs are a valid district link and an output file name.
    Returns False if inputs are invalid.
    Returns "ALL" if the user has requested to scrape all districts.
    '''

    if len(sys.argv) != 3:
        if len(sys.argv) == 2 and sys.argv[1] == "ALL":
            return "ALL"
        print("""This script need 2 arguments to run to scrape a district.
Alternatively, use a single argument 'ALL' to scrape all districts at once.""", end="\n")
        return False

    url = sys.argv[1]
    output_file_name = sys.argv[2]

    #url validity check
    if not validators.url(url):
        print("The first argument of this script must be a valid url.")
        return False
    
    #matches the script input argument directly against all valid district links, assuming these links were successfuly scraped from server
    valid_links = get_all_district_links()
    if valid_links is not None:
        if sys.argv[1] not in valid_links.values():
            print("Recieved invalid link as an argument.\nThe first script argument must be an url that leads to an electoral district.")
            return False

    #output file name checks
    invalid_chars = """<>:"/\\|?*"""

    for char in output_file_name:
        if char in invalid_chars:
            print(f"""Invalid characters in output file name. Output file name cannot contain the following characters: {invalid_chars}""")
            return False

    if output_file_name[-1] in " .":
        print("Output file name cannot contain trailing spaces and periods.")
        return False
    
    if not output_file_name[-4:] == ".csv":
        output_file_name = output_file_name + ".csv"

    return output_file_name


def get_municipality_data(url):
    '''
    Scrapes election data in a given municipality.
    Argument must be a valid link to a municipality.
    '''

    parsed_html = get_html(url)
    if parsed_html is None:
        parsed_html = retry_get(url)
    if parsed_html is None:
        return None

    all_tables = parsed_html.find_all("table")

    overview_table_data_row = all_tables[0].find_all("tr")[2].find_all("td")
    voter_data = {
        "registered voters": overview_table_data_row[3].get_text().replace("\xa0", ""),
        "total votes": overview_table_data_row[6].get_text().replace("\xa0", ""),
        "valid votes": overview_table_data_row[7].get_text().replace("\xa0", ""),
        "votes by party": None
    }
    
    party_vote_data = []
    for table in all_tables[1:]:
        all_rows = [row for row in table.find_all("tr") if not (row.find_all("th") or row.find_all(class_="hidden_td"))]
        for row in all_rows:
            all_cells = row.find_all("td")
            party_vote_data.append((all_cells[1].get_text().replace("\xa0", ""), all_cells[2].get_text().replace("\xa0", "")))

    voter_data["votes by party"] = party_vote_data
    #print(voter_data)

    return voter_data


def get_district_data(url):
    '''
    Scrapes the code, name and link of any municipality within a district.
    Argument must be a valid link to a district.
    '''

    parsed_html = get_html(url)
    if parsed_html is None:
        parsed_html = retry_get(url)
    if parsed_html is None:
        return None

    all_rows = [row for row in parsed_html.find_all("tr") if not (row.find_all("th") or row.find_all("td", class_ = "hidden_td"))]
    district_data = []
    
    for row in all_rows:

        district_info = {
            "link" : "https://www.volby.cz/pls/ps2017nss/" + row.find("a")["href"],
            "code" : row.find_all("td")[0].get_text(),
            "municipality" : row.find_all("td")[1].get_text()
        }

        district_data.append(district_info)

    return district_data


def scrape_district(url):
    '''
    Scrapes all municipalities within a given district for election data.
    Argument must be a valid link to a district.
    '''

    district_data = get_district_data(url)

    error_links = []
    for district in district_data:
        municipality_data = get_municipality_data(district["link"])

        if municipality_data is None:
            municipality_data = retry_get(district["link"])
        if municipality_data is None:
            error_links.append((district["municipality"], district["link"]))
            continue

        for key, value in municipality_data.items():
            district[key] = value
    

    if error_links:
        print("Could not scrape data from some municipalities. These have not been included in the output file. Here are their urls links:")
        for error_link in error_links:
            print(error_link[0], ": ", error_link[1], sep="", end='\n')

    return district_data


def csv_dumper(district_data, output_file_name):
    '''
    Creates a new output csv file and dumps scraped data into it.
    '''

    parties = list({party_data[0] for municipality_data in district_data for party_data in municipality_data["votes by party"]})

    headers = ["code", "municipality", "registered voters", "total votes", "valid votes"]
    for party in parties:
        headers.append(party)

    with open(output_file_name, "w", newline='', encoding="utf-8") as f:
       
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


def scrape_all(links):
    '''
    Scrapes all districts.
    Output files will be named {district name}_output.csv
    '''

    print("Scraping ALL districts. This will take a few minutes.")

    for district_name, link in links.items():
        print("Scraping district: ", district_name, " ...")
        district_data = scrape_district(link)
        csv_dumper(district_data, f"{district_name}_results.csv")
        print(f"Created file {district_name}_results.csv")


def main():

    start_time = time.time()
    
    #all valid links (1st input arguments)
    #obtained using the get_all_district_links() function
    #for convenience only, can be deleted without impacting the functionality of this script
    district_links = {
    'Benešov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2101',
    'Beroun': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2102',
    'Blansko': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6201',
    'Brno-město': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6202',
    'Brno-venkov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6203',
    'Bruntál': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=14&xnumnuts=8101',
    'Břeclav': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6204',
    'Cheb': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=5&xnumnuts=4101',
    'Chomutov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4202',
    'Chrudim': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=9&xnumnuts=5301',
    'Domažlice': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3201',
    'Děčín': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4201',
    'Frýdek-Místek': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=14&xnumnuts=8102',
    'Havlíčkův Brod': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=10&xnumnuts=6101',
    'Hodonín': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6205',
    'Hradec Králové': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=8&xnumnuts=5201',
    'Jablonec nad Nisou': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=7&xnumnuts=5102',
    'Jeseník': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7101',
    'Jihlava': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=10&xnumnuts=6102',
    'Jindřichův Hradec': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=3&xnumnuts=3103',
    'Jičín': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=8&xnumnuts=5202',
    'Karlovy Vary': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=5&xnumnuts=4102',
    'Karviná': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=14&xnumnuts=8103',
    'Kladno': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2103',
    'Klatovy': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3202',
    'Kolín': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2104',
    'Kroměříž': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=13&xnumnuts=7201',
    'Kutná Hora': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2105',
    'Liberec': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=7&xnumnuts=5103',
    'Litoměřice': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4203',
    'Louny': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4204',
    'Mladá Boleslav': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2107',
    'Most': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4205',
    'Mělník': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2106',
    'Nový Jičín': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=14&xnumnuts=8104',
    'Nymburk': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2108',
    'Náchod': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=8&xnumnuts=5203',
    'Olomouc': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7102',
    'Opava': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=14&xnumnuts=8105',
    'Ostrava-město': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=14&xnumnuts=8106',
    'Pardubice': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=9&xnumnuts=5302',
    'Pelhřimov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=10&xnumnuts=6103',
    'Plzeň-jih': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3204',
    'Plzeň-město': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3203',
    'Plzeň-sever': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3205',
    'Prachatice': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=3&xnumnuts=3105',
    'Praha': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=1&xnumnuts=1100',
    'Praha-východ': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2109',
    'Praha-západ': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2110',
    'Prostějov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7103',
    'Písek': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=3&xnumnuts=3104',
    'Přerov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7104',
    'Příbram': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2111',
    'Rakovník': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=2&xnumnuts=2112',
    'Rokycany': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3206',
    'Rychnov nad Kněžnou': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=8&xnumnuts=5204',
    'Semily': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=7&xnumnuts=5104',
    'Sokolov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=5&xnumnuts=4103',
    'Strakonice': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=3&xnumnuts=3106',
    'Svitavy': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=9&xnumnuts=5303',
    'Tachov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=4&xnumnuts=3207',
    'Teplice': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4206',
    'Trutnov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=8&xnumnuts=5205',
    'Tábor': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=3&xnumnuts=3107',
    'Třebíč': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=10&xnumnuts=6104',
    'Uherské Hradiště': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=13&xnumnuts=7202',
    'Vsetín': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=13&xnumnuts=7203',
    'Vyškov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6206',
    'Zlín': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=13&xnumnuts=7204',
    'Znojmo': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6207',
    'Ústí nad Labem': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=6&xnumnuts=4207',
    'Ústí nad Orlicí': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=9&xnumnuts=5304',
    'Česká Lípa': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=7&xnumnuts=5101',
    'České Budějovice': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=3&xnumnuts=3101',
    'Český Krumlov': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=3&xnumnuts=3102',
    'Šumperk': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=12&xnumnuts=7105',
    'Žďár nad Sázavou': 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=10&xnumnuts=6105'
    }

    check = input_validation()

    #invalid script inputs
    if check is False:
        sys.exit()
    
    #scraping all districts on https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ
    if check == "ALL":
        scrape_all(district_links)
        end_time = time.time()
        print(f"Total runtime: {end_time - start_time:.4f} seconds.")
        return

    #scraping one district
    output_file_name = check
    url = sys.argv[1]

    print("Scraping...")
    district_data = scrape_district(url)
    csv_dumper(district_data, output_file_name)
    
    end_time = time.time()
    print(f"Total runtime: {end_time - start_time:.4f} seconds.")


if __name__ == "__main__":
    main()