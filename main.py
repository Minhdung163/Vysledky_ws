from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.alert import Alert
from time import sleep
import base64
import re
import json
import os

import getpass

def get_data(url, username, password):
    browser_options = webdriver.ChromeOptions()
    browser_options.headless = True

    driver = webdriver.Chrome(options=browser_options)
    driver.get(url)  
    
    
    # alert = Alert(driver)
    # alert.dismiss()
    
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
    
    # data = driver.page_source
    data = driver.find_element(By.ID, "VysledkyListBody").text
    assert type(data) == str

    driver.quit()

    return data

def main():
    username = getpass.getpass("Username: ")
    password = getpass.getpass()
    data = get_data("https://apl.unob.cz/vvi/Vysledky", username, password)
    
    # with open("data.json", "w", encoding = "utf-8") as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>')
    
    with open("data.json", "w", encoding = "utf-8") as f:
        f.write(data)
    
    with open("data.json", "r", encoding='utf-8') as f:
        data = f.read()

    # Split the data into lines
    split_data = data.split('\n')
    # First chunk of 5 lines
    first_chunk = split_data[0:5]

    # Special case: chunk of 6 lines
    second_chunk = split_data[5:11]

    # Rest of the data: chunks of 5 lines
    rest_of_chunks = [split_data[i:i + 5] for i in range(11, len(split_data), 5)]

    # Combine all chunks
    chunks = [first_chunk, second_chunk] + rest_of_chunks

    # Parse each chunk into a dictionary
    records = []
    for chunk in chunks:
        
        # Handle the special case where the title spans multiple lines
        if len(chunk) == 6 and "Svaz letců svobodného Československa (Českoslovenští letci v boji za obnovu československé demokracie 1951–2017" in chunk[2] and "Free Czechoslovak Air Force Association (Czechoslovak Airmen Fighting for the Restoration of Democracy in Czechoslovakia 1951–2017)" in chunk[3]:
            title = chunk[2] + " " + chunk[3]
            authors = chunk[4]
            id_and_percent = chunk[5]
        else:
            title = chunk[2]
            authors = chunk[3]
            id_and_percent = chunk[4]

        record = {
            "type": chunk[0],
            "year": chunk[1],
            "title": title,
            "authors": authors,
            "id_and_percent": id_and_percent
        }
        records.append(record)


    # Write the records to the file in JSON format
    with open("data.json", "w", encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>')
      
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