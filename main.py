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

from time import sleep
import base64
import re
import json
import os

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

def get_list_of_authors(driver, result_link):
    keys2 = ["Pořadí", "Příjmení Jméno", "Podíl [%]", "Vztah", "Součást v době uplatnění výsledku", "Další"]
    driver.get(result_link)
    sleep(2)
    table = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[5]/div/div/div[2]/table")
    rows = table.find_elements(By.TAG_NAME, "tr")
    authors = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) == len(keys2):
            author = {keys2[i]: cell.text for i, cell in enumerate(cells)}
            authors.append(author)
    return authors

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

def get_publication(driver,result_link):
    driver.get(result_link)
    sleep(2)

    id = str(uuid4())
    name = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[7]/div/div/div[2]/table/tbody/tr[3]/td").text
    published_year = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[7]/div/div/div[2]/table/tbody/tr[8]/td").text
    place_of_publication = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[8]/div/div/div[2]/table/tbody/tr[3]/td").text

    return {"id": id, "name": name, "published_year": published_year, "place_of_publication": place_of_publication, "publication_type_id": publication_type_id}

def get_publication_types(driver, result_link):
    driver.get(result_link)
    sleep(2)

    id = str(uuid4())
    name = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[7]/div/div/div[2]/table/tbody/tr[3]/td").text
    
    return {"id": id, "name": name}


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


def get_data(url, username, password, result_links):
    driver = login(url, username, password)
        
    results = []
    for result_link in result_links:
        publication_data = get_publication(driver, result_link)
        publication_type_data = get_publication_types(driver, result_link)
        # result_data = get_basic_infor_result(driver, result_link)
        # authors = get_list_of_authors(driver, result_link)
        # data_by_type_of_result = get_data_by_type_of_result(driver, result_link)   
        # supports = get_list_of_supports(driver, result_link) 
        # attachments = get_attachments_result(driver, result_link)
        
        result = {"publication": publication_data , "publication_type": publication_type_data}
        
        results.append(result)
    return results

def main():
    #Logging in
    with open("infor.txt", "r") as f:
        lines = f.readlines()
    username = lines[0].strip()
    password = lines[1].strip()
    main_url = "https://apl.unob.cz/vvi/Vysledky"
    base_url = "https://apl.unob.cz/vvi/Vysledky?RokUplatneniList={year}&NazevVysledku=&Doi=&NazevCelku=&Issn=&KodUtIsi=&ScopusEid=&JeValidni="

    # for year in range(1951, 2025): 
    #     url = base_url.format(year=year)
    #     links = scrape_publication_links(url, username, password)
        
    #     # Write the links to a text file
    #     with open(f"result_links_test.txt", "a", encoding = "utf-8") as f:
    #         for link in links:
    #             f.write(link + "\n")
    
    driver = login(main_url, username, password)
    
    with open("result_links_test.txt", "r") as file:
        result_links = file.read().splitlines()
    
    # data = get_data(main_url, username, password, result_links)
        
    # with open("result_data_test.json", "w", encoding = "utf-8") as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>)')
    publication_types_set = set()
    for result_link in result_links:
        publication_types = get_publication_types(driver, result_link)
        # Convert the dictionary to a tuple with only the values and add it to the set
        publication_types_set.add(tuple(publication_types.values()))

    # Convert the set of tuples back to a list of dictionaries
    publication_types_list = [dict(zip(publication_types.keys(), values)) for values in publication_types_set]

    with open("publication_types.json", "w", encoding = "utf-8") as f:
        f.write(json.dumps(publication_types_list, ensure_ascii=False, indent=4))
        
    

    
      
if __name__ == '__main__':
    main()
