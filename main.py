from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
from uuid import uuid4
from dbwriter import DBWriter

from time import sleep
import base64
import re
import json
import os
import asyncio

import getpass

def get_basic_infor_result(driver, result_link):
    keys1 = ["Druh výsledku", "Původní jazyk", "Název v původním jazyce", "Název v anglickém jazyce", "Klíčová slova v anglickém jazyce", "Popis v původním jazyce", "Popis v anglickém jazyce", "Rok uplatnění", "Obor m17+", "Důvěrnost údajů poskytnutých do RIV", "Odkaz", "Odkaz na výzkum", "DOI", "Editoři v citaci"]

    driver.get(result_link)
    sleep(2)
    table = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[7]/div/div/div[2]/table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    item_data = {key: "" for key in keys1}  # Initialize item_data with keys and empty strings
    for row in rows:
        key_cell = row.find_element(By.TAG_NAME, "th")  # The key is in a "th" tag
        value_cell = row.find_element(By.TAG_NAME, "td")  # The value is in a "td" tag
        key = key_cell.text
        value = value_cell.text
        if key in item_data:  # If the key is in the list of expected keys
            item_data[key] = value
    return item_data

def get_data_by_type_of_result(driver, result_link):    
    keys3 = ["Forma vydání", "ISBN nebo ISMN", "Místo vydání", "Název edice a číslo svazku", "Počet stran knihy", "Počet výtisků", "Odkaz na záznam v Databázi Národní knihovny ČR", "Vydání (verze) knihy", "Název nakladatele", "Kód UT WoS knihy podle Web of Science", "EID knihy podle Scopus"]

    driver.get(result_link)
    sleep(2)
    table = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[8]/div/div/div[2]/table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    item_data = {key: "" for key in keys3}  # Initialize item_data with keys and empty strings
    for row in rows:
        key_cell = row.find_element(By.TAG_NAME, "th")  # The key is in a "th" tag
        value_cell = row.find_element(By.TAG_NAME, "td")  # The value is in a "td" tag
        key = key_cell.text
        value = value_cell.text
        if key in item_data:  # If the key is in the list of expected keys
            item_data[key] = value
    return item_data

def get_list_of_supports(driver, result_link):
    keys4 = ["Způsob financování", "Kód projektu", "Název projektu", "Předkladatel pro RIV", "Dodavatel pro RIV"]
    driver.get(result_link)
    sleep(2)
    supports = []
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    try:
        table = soup.select_one("div.main > div:nth-of-type(12) > div > div > div:nth-of-type(2) > table")
        if table is not None:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == len(keys4):
                    support = {keys4[i]: cell.text for i, cell in enumerate(cells)}
                    supports.append(support)
    except AttributeError:
        pass
    return supports

def get_attachments_result(driver, result_link):
    keys5 = ["Název", "Velikost v kB", "Nahráno / Osoba", "Další informace"]
    driver.get(result_link)
    sleep(2)
    attachments = []
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the table using its id
    table_section = soup.find(id="prilohaVysledekList")
    
    # If the table section is not found, return an empty list
    if table_section is None:
        return attachments

    table = table_section.find('table')

    # If the table is not found, return an empty list
    if table is None:
        return attachments

    rows = table.find_all('tr')
    for row in rows[1:]:  # Skip the header row
        cells = row.find_all('td')
        if len(cells) >= len(keys5):
            attachment = {keys5[i]: cell.text for i, cell in enumerate(cells)}
            attachments.append(attachment)
    return attachments

def find_publication_detail(tbody_xpath, driver, search_text):
    # Find all rows in the tbody
    rows = driver.find_elements(By.XPATH, f"{tbody_xpath}/tr")

    # Initialize a variable to store the td text for the search_text
    detail_td_text = None

    # Iterate through each row
    for row in rows:
        # Find the th element in the current row
        th = row.find_element(By.XPATH, ".//th")
        # Check if the th text matches the search_text
        if th.text == search_text:
            # If it does, find the td element in the same row and extract its text
            td = row.find_element(By.XPATH, ".//td")
            detail_td_text = td.text
            break  # Stop searching once found

    return detail_td_text

def get_publication(driver,result_link):
    driver.get(result_link)
    sleep(2)

    id = str(uuid4())
    name = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[7]/div/div/div[2]/table/tbody/tr[3]/td").text
    published_year = find_publication_detail("/html/body/div/main/div[1]/div[7]/div/div/div[2]/table/tbody", driver, "Rok uplatnění")
    place_of_publication = find_publication_detail("/html/body/div/main/div[1]/div[8]/div/div/div[2]/table/tbody", driver, "Místo vydání")
    publication_type_name = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[7]/div/div/div[2]/table/tbody/tr[1]/td").text
    valid = True
    
    # Read the publication types from the JSON file
    with open("publication_types.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    publication_types = data['publicationtypes']

    # Find the publication type with the matching name and get its id
    publication_type_id = next((item['id'] for item in publication_types if item['name'] == publication_type_name), None)

    return {
        "id": id, 
        "name": name, 
        "published_year": published_year, 
        "place_of_publication": place_of_publication, 
        "publication_type_id": publication_type_id, 
        "valid": valid, 
        "reference": result_link
    }

def get_publication_types(driver, result_link):
    with open('publication_categories.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    category_id = data['publicationcategories'][0]['id']
    
    driver.get(result_link)
    sleep(2)

    id = str(uuid4())
    name = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[7]/div/div/div[2]/table/tbody/tr[1]/td").text
    
    name_to_name_en_mapping = {
        "Uspořádání workshopu": "Workshop Organization",
        "Ostatní": "Other",
        "Audiovizuální tvorba": "Audiovisual Creation",
        "Recenzovaný odborný článek": "Peer-reviewed Article",
        "Stať ve sborníku": "Conference Proceedings Article",
        "Kapitola/y v odborné knize": "Chapter/s in a Scholarly Book",
        "Software": "Software",
        "Odborná kniha": "Scholarly Book",
        "Poloprovoz / technologie / odrůda / plemeno": "Semi-Operational / Technology / Variety / Breed"
    }
    
    name_en = name_to_name_en_mapping.get(name, "Unknown")
    
    return {
        "id": id, 
        "category_id": category_id,
        "name": name,
        "name_en": name_en
    }
    
def get_list_of_authors(driver, result_link):
    # Load the user.json file
    with open("user.json", "r", encoding='utf-8') as file:
        users = json.load(file)
        
    # Load the publications.json file
    with open("publications.json", "r", encoding='utf-8') as file:
        publications_data = json.load(file)
    
    driver.get(result_link)
    sleep(2)
    
    try:
        tbody_element = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[5]/div/div/div[2]/table/tbody")
        # Proceed with operations on tbody_element if found
        rows = tbody_element.find_elements(By.TAG_NAME, "tr")
        authors = []
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            author_name = cells[1].text
            
            # Search for the author in the loaded users
            matching_user = next((user for user in users if user["name"] == author_name), None)
            
            # If a matching user is found, use its ID; otherwise, generate a new UUID
            user_id = matching_user["id"] if matching_user else str(uuid4())
            
            # Search for a matching publication reference
            matching_publication = next((pub for pub in publications_data["publications"] if pub["reference"] == result_link), None)
            
            # If a matching publication is found, use its ID for the author
            if matching_publication:
                publication_id = matching_publication["id"]
            
            author = {
                "id": str(uuid4()),
                "user_id": user_id,
                "publication_id": publication_id,
                "order": cells[0].text,
                "share": cells[2].text
            }
            authors.append(author)
        return authors
    except NoSuchElementException:
        matching_publication = next((pub for pub in publications_data["publications"] if pub["reference"] == result_link), None)
            
        # If a matching publication is found, use its ID for the author
        if matching_publication:
            publication_id = matching_publication["id"]
        # Element not found, skip or handle accordingly
        return [{
            "id": str(uuid4()),  # Generate a new UUID for the id
            "user_id": None,  # Explicitly set to None
            "publication_id": publication_id, 
            "order": None,  # Explicitly set to None
            "share": None  # Explicitly set to None
        }]

def login(url, username, password):
    browser_options = webdriver.ChromeOptions()
    browser_options.headless = True

    driver = webdriver.Chrome(options=browser_options)
    driver.get(url)  
    
    driver.refresh()
    assert "UoD" in driver.title
    
    username_field = driver.find_element(By.NAME, "Username")
    username_field.clear()
    username_field.send_keys(username)
    sleep(1)
    
    password_field = driver.find_element(By.NAME, "Password") 
    password_field.clear()
    password_field.send_keys(password)
    sleep(1)
    
    password_field.send_keys(Keys.RETURN)
    
    return driver
    
def scrape_publication_links(url, username, password):
    driver = login(url, username, password)
    while True:
        try:
            expand_button = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[3]/div/div[2]/button")
            actions = ActionChains(driver)
            actions.move_to_element(expand_button).click(expand_button).perform()
            sleep(2)
        except NoSuchElementException:
            break

        # Check for the alert element
        try:
            alert_element = driver.find_element(By.CSS_SELECTOR, ".alert.m-0.alert-info")
            # If the element is found, break the loop
            break
        except NoSuchElementException:
            # If the element is not found, continue with the next iteration
            continue
        
    result_elems = driver.find_elements(By.CSS_SELECTOR, "[href^='/vvi/Vysledek']")
    result_links = [result_elem.get_attribute("href") for result_elem in result_elems]
    result_links = set(result_links)
    result_links = [link for link in result_links if 'Edit' not in link and 'Index' not in link]

    driver.quit()

    return result_links

def scrape_publication_user(url, username, password):
    driver = login(url, username, password)
    while True:
        try:
            expand_button = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[3]/div/div[2]/button")
            actions = ActionChains(driver)
            actions.move_to_element(expand_button).click(expand_button).perform()
            sleep(2)
        except NoSuchElementException:
            break

        # Check for the alert element
        try:
            alert_element = driver.find_element(By.CSS_SELECTOR, ".alert.m-0.alert-info")
            # If the element is found, break the loop
            break
        except NoSuchElementException:
            # If the element is not found, continue with the next iteration
            continue
    
    tbody = driver.find_element(By.ID, "AutoriListBody")
    rows = tbody.find_elements(By.TAG_NAME, "tr")

    names = [row.find_element(By.TAG_NAME, "td").text for row in rows]
    names = set(names)
    
    users = [{"id": str(uuid4()), "name": name} for name in names]

    # Write the authors and UUIDs to a JSON file
    with open("user.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

    driver.quit()

    return users

def write_publication(url, username, password, result_links):
    driver = login(url, username, password)
    
    publications = []  
    for result_link in result_links:
        publication_data = get_publication(driver, result_link)
        publications.append(publication_data)  # Append each publication's data
        
    results = {"publications": publications}  # Wrap the accumulated list
    return results

def write_publication_types(url, username, password, result_links):
    driver = login(url, username, password)
    
    publication_types_list = []
    seen_names = set()
    for result_link in result_links:
        publication_types = get_publication_types(driver, result_link)
        if publication_types['name'] not in seen_names:
            seen_names.add(publication_types['name'])
            publication_types_list.append(publication_types)
    results = {"publicationtypes": publication_types_list}
    return results

def write_authors(url, result_links, username, password):
    driver = login(url, username, password)
    
    authors = []
    for result_link in result_links:
        authors_data = get_list_of_authors(driver, result_link)
        authors.append(authors_data)
        
    result = {"publication_authors": authors}
    
    return result


def insert_externalidstypeid():
    externalidtypes = []
    new_type = {
        "id": str(uuid4()),
        "name": "Vysledky",
        "name_en": "Results",
        "urlformat": "https://apl.unob.cz/vvi/Vysledky/%s"
    }
    result = {"externalidtypes": new_type}
    with open("externalidtypes.json", "w") as type:
        json.dump(result, type, indent=4)
def create_publication_category():
    new_id = str(uuid4())  # Generate a new UUID
    category = {
        "publicationcategories": [
            {
                "id": new_id,  # Use the generated UUID
                "name": "Vědecké",
                "name_en": "Scientific"  # Corrected typo from "Scientic" to "Scientific"
            }
        ]
    }
    
    # Write the category dictionary to a JSON file
    with open('publication_categories.json', 'w', encoding='utf-8') as f:
        json.dump(category, f, ensure_ascii=False, indent=4)
    
    return category

def creat_externalids():
    # Load the initial data from the JSON file
    with open("publications.json", "r", encoding='utf-8') as initial_file:
        data = json.load(initial_file)
        
    with open("externalidtypes.json", "r", encoding='utf-8') as f:
        types = json.load(f)

    # Create a new JSON structure for externalids
    externalids = []

    for publication in data["publications"]:
        externalid_types = types["externalidtypes"]
        outer_id = re.search(r'\d+$', publication["reference"]).group()
        external_id_entry = {
            "id": str(uuid4()),
            "inner_id": publication["id"],  
            "outer_id": outer_id,
            "typeid_id": externalid_types["id"]
        }
        externalids.append(external_id_entry)

    result = {"externalids": externalids}

    # Save externalids to a JSON file
    with open("externalids.json", "w") as result_file:
        json.dump(result, result_file, indent=4)

def merge_data():

    with (open("publication_authors.json", "r", encoding="utf-8") as publication_authors,
          open("publication_types.json", "r", encoding="utf-8") as publication_types,
          open("publications.json", "r", encoding="utf-8") as publications,
          open("externalids.json", "r", encoding="utf-8") as externalIds,
          open("publication_categories.json", "r", encoding="utf-8") as publication_categories):

        ext_ids = json.load(externalIds)
        data_authors = json.load(publication_authors)
        data_categories = json.load(publication_categories)
        data_types = json.load(publication_types)
        data_publication = json.load(publications)
        
        merged_data = [ext_ids, data_categories, data_types, data_authors, data_publication]

        # Step 3: Write the merged data to a new JSON file
        with open("systemdata.json", "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
            
async def insert_publications_from_json(db_writer):
    print("Starting to insert publications from JSON...")

    # Load publications data
    with open("publications.json", "r", encoding="utf-8") as file:
        publications = json.load(file)["publications"]
    print(f"Loaded {len(publications)} publications.")
    print(publications[1])

    # Load external IDs data
    with open("externalids.json", "r", encoding="utf-8") as file:
        externalids = json.load(file)["externalids"]
    print(f"Loaded {len(externalids)} external IDs.")

    # Create a mapping from inner_id to external ID details for quick lookup
    externalid_map = {item["inner_id"]: item for item in externalids}
    
    awaitables = []
    inserted_count = 0

    for publication in publications:
        try:
            # Prepare data for insertion
            table_name = "Publication"
            publication_inner_id = publication.get("id")

            # Lookup the matching external ID entry using the map
            matching_entry = externalid_map.get(publication_inner_id)

            if matching_entry:
                # Extract needed values if a matching entry is found
                outer_id = matching_entry["outer_id"]
                outer_id_type_id = matching_entry["typeid_id"]
                # Insert with outer_id and outer_id_type_id
                awaitables.append(db_writer.Create(table_name, publication, outer_id, outer_id_type_id))
                print(f"Inserted publication with inner_id {publication_inner_id} including external IDs.")
            else:
                # Insert without outer_id and outer_id_type_id if no match is found
                awaitables.append(db_writer.Create(table_name, publication))
                print(f"Inserted publication with inner_id {publication_inner_id} without external IDs.")

            if len(awaitables) > 9:
                await asyncio.gather(*awaitables)
                awaitables = []  # Reset the list after execution

            inserted_count += 1
        except Exception as e:
            print(f"Error inserting publication {publication_inner_id}: {e}")

    # Ensure any remaining awaitables are executed
    if awaitables:
        await asyncio.gather(*awaitables)
        awaitables = []  # Reset the list after execution

    print(f"Finished inserting publications. Total attempted: {len(publications)}. Total successfully inserted: {inserted_count}.")
    return "ok"

def main():
    #Logging in
    with open("infor.txt", "r") as f:
        lines = f.readlines()
    username = lines[0].strip()
    password = lines[1].strip()
    main_url = "https://apl.unob.cz/vvi/Vysledky"
    base_url = "https://apl.unob.cz/vvi/Vysledky?RokUplatneniList={year}&NazevVysledku=&Doi=&NazevCelku=&Issn=&KodUtIsi=&ScopusEid=&JeValidni="
    author_url= "https://apl.unob.cz/vvi/Autori"
    
    # # Scrape the publication links
    # for year in range(1951, 2025): 
    #     url = base_url.format(year=year)
    #     links = scrape_publication_links(url, username, password)
        
    #     # Write the links to a text file
    #     with open(f"result_links_test.txt", "a", encoding = "utf-8") as f:
    #         for link in links:
    #             f.write(link + "\n")
    
    # insert_externalidstypeid()
    
    with open("result_links_test.txt", "r") as file:
        result_links = file.read().splitlines()
    
    # publication_data = write_publication(main_url, username, password, result_links)
        
    # with open("publications.json", "w", encoding = "utf-8") as f:
    #     json.dump(publication_data, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>)')
    
    #creat_externalids()
    
    # publication_types_data = write_publication_types(main_url, username, password, result_links)
    
    # with open("publication_types.json", "w", encoding = "utf-8") as f:
    #     f.write(json.dumps(publication_types_data, ensure_ascii=False, indent=4))
        
    # # Scrape the publication users
    # scrape_publication_user(author_url, username, password)    
    
    # author_data = write_authors(main_url, result_links, username, password)
    
    # with open("publication_authors2.json", "w", encoding = "utf-8") as f:
    #     f.write(json.dumps(author_data, ensure_ascii=False, indent=4))
    
    #merge_data()
    
    db_writer = DBWriter()  # Instantiate your DBWriter (adjust if the constructor requires parameters)
    asyncio.run(insert_publications_from_json(db_writer))
    

    
      
if __name__ == '__main__':
    main()
