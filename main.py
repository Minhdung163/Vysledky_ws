from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoSuchElementException
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
    try:
        table = driver.find_element(By.XPATH, "/html/body/div/main/div[1]/div[12]/div/div/div[2]/table")
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == len(keys4):
                support = {keys4[i]: cell.text for i, cell in enumerate(cells)}
                supports.append(support)
    except NoSuchElementException:
        pass
    return supports

def get_attachments_result(driver, result_link):
    keys5 = ["Název", "Velikost v kB", "Nahráno / Osoba", "Další informace"]
    driver.get(result_link)
    sleep(2)
    attachments = []
    try:
        # Find the div containing the table using its id
        div = driver.find_element(By.ID, "prilohaVysledekList")
        # Find the table within the div
        table = div.find_element(By.TAG_NAME, "table")
    except NoSuchElementException:
        return attachments
    rows = table.find_elements(By.TAG_NAME, "tr")
    for row in rows[1:]:  # Skip the header row
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) >= len(keys5):
            attachment = {keys5[i]: cell.text for i, cell in enumerate(cells)}
            attachments.append(attachment)
    return attachments

def get_data(url, username, password):
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
    
    result_elems = driver.find_elements(By.CSS_SELECTOR, "[href^='/vvi/Vysledek']")
    result_links = [result_elem.get_attribute("href") for result_elem in result_elems]
    result_links = set(result_links)
    result_links = [link for link in result_links if 'Edit' not in link]
    
    results = []
    for result_link in result_links:
        result_data = get_basic_infor_result(driver, result_link)
        authors = get_list_of_authors(driver, result_link)
        data_by_type_of_result = get_data_by_type_of_result(driver, result_link)   
        supports = get_list_of_supports(driver, result_link) 
        attachments = get_attachments_result(driver, result_link)
        
        result = {"link": result_link, "basic_info": result_data, "data_by_type_of_result": data_by_type_of_result, "authors": authors, "supports_and_funding": supports, "attachments": attachments}
        results.append(result)

    driver.quit()

    return results

def main():
    #Logging in
    with open("infor.txt", "r") as f:
        lines = f.readlines()
    username = lines[0].strip()
    password = lines[1].strip()
    data = get_data("https://apl.unob.cz/vvi/Vysledky", username, password)
    
    # with open("data.json", "w", encoding = "utf-8") as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>')
    
    # with open("result_links.json", "w", encoding = "utf-8") as f:
    #     f.writelines("\n".join(data))
        
    with open("result_data.json", "w", encoding = "utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>)')
    
    
    # with open("data.json", "r", encoding='utf-8') as f:
    #     data = f.read()

    # # Split the data into lines
    # split_data = data.split('\n')

    # # Split each line at a space followed by a number and join with a newline, but only if the line contains a space followed by a number
    # split_data = ['\n'.join(re.split(r'(?<=^\d{6}) ', line)) if re.match(r'^\d{6}', line) else line for line in split_data]
    
    # # Split the modified data into lines again
    # split_data = '\n'.join(split_data).split('\n')
    
    # # First chunk of 6 lines
    # first_chunk = split_data[0:6]

    # # Special case: chunk of 7 lines
    # second_chunk = split_data[6:13]

    # # Rest of the data: chunks of 6 lines
    # rest_of_chunks = [split_data[i:i + 6] for i in range(13, len(split_data), 6)]

    # # Combine all chunks
    # chunks = [first_chunk, second_chunk] + rest_of_chunks

    # # Parse each chunk into a dictionary
    # records = []
    # for chunk in chunks:
        
    #     # Handle the special case where the title spans multiple lines
    #     if len(chunk) == 7 and "Svaz letců svobodného Československa (Českoslovenští letci v boji za obnovu československé demokracie 1951–2017" in chunk[2] and "Free Czechoslovak Air Force Association (Czechoslovak Airmen Fighting for the Restoration of Democracy in Czechoslovakia 1951–2017)" in chunk[3]:
    #         title = chunk[2] + " " + chunk[3]
    #         authors = chunk[4]
    #         Id = chunk[5]
    #         percent = chunk[6]
    #     else:
    #         title = chunk[2]
    #         authors = chunk[3]
    #         Id = chunk[4]
    #         percent = chunk[5]

    #     record = {
    #         "type": chunk[0],
    #         "year": chunk[1],
    #         "title": title,
    #         "authors": authors,
    #         "Id": Id,
    #         "percent": percent
    #     }
    #     records.append(record)


    # # Write the records to the file in JSON format
    # with open("data.json", "w", encoding='utf-8') as f:
    #     json.dump(records, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>')
      
if __name__ == '__main__':
    main()








# driver.get("https://apl.unob.cz/planovanivyuky/api/read/atributy")

# elem = driver.find_element(By.ID, "userNameInput")
# elem.clear()
# elem.send_keys("email@web.cz")
# elem.send_keys(Keys.RETURN)

# elem = driver.find_element(By.ID, "passwordInput")
# elem.clear()
# elem.send_keys(password)
# elem.send_keys(Keys.RETURN)

# elem = driver.find_element(By.ID, "submitButton")
# elem.click()


# driver.get("https://intranet.web.cz/aplikace/SitePages/DomovskaStranka.aspx")

# # Seznam akreditovanych programu
# # elem = driver.find_element(By.ID, "ctl00_ctl40_g_ba0590ba_842f_4a3a_b2ea_0c665ea80655_ctl00_LvApplicationGroupList_ctrl0_ctl00_LvApplicationsList_ctrl7_btnApp")
# elem = WebDriverWait(driver, 10).until(
#         expected_conditions.presence_of_element_located((By.ID, "ctl00_ctl40_g_ba0590ba_842f_4a3a_b2ea_0c665ea80655_ctl00_LvApplicationGroupList_ctrl0_ctl00_LvApplicationsList_ctrl7_btnApp"))
#     )
# elem.click()

# assert "No results found." not in driver.page_source
# driver.close()