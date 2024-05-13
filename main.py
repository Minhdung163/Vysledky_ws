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
    
    wait = WebDriverWait(driver, 20)  # wait up to 10 seconds

    while True:
            try:
                # Scroll down the webpage
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait until the button is clickable
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-light.border.bg-btn-hover-light-1.no-wrap.w-100")))

                # Click the button using JavaScript
                driver.execute_script("arguments[0].click();", button)

                # Wait for the page to load
                sleep(10)
            except Exception as e:
                # If the button is not found or not clickable, break the loop
                break
    
    # Wait for the AJAX data to load
    wait.until(EC.presence_of_element_located((By.ID, "VysledkyListBody")))
    
    # data = driver.page_source
    data = driver.find_element(By.ID, "VysledkyListBody").text
    assert type(data) == str

    driver.quit()

    return data

def click_link_and_extract_data(driver, link_href):
    # Click on the link with the specified href attribute
    driver.get(link_href)
    wait = WebDriverWait(driver, 2)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table table-borderless table-striped table-light table-cellspacing1 border mb-0")))

    # Extract data from the page after clicking on the link
    with open("data2.json", "r", encoding='utf-8') as f:
        existing_data = json.load(f)

    # Append the new data
    new_data = driver.find_element(By.CLASS_NAME, "table table-borderless table-striped table-light table-cellspacing1 border mb-0").text
    existing_data.append(new_data)

    # Write the updated data back to the JSON file
    with open("data2.json", "w", encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
    return new_data

def main():
    browser_options = webdriver.ChromeOptions()
    browser_options.headless = True
    driver = webdriver.Chrome(options=browser_options)
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

    # Split each line at a space followed by a number and join with a newline, but only if the line contains a space followed by a number
    split_data = ['\n'.join(re.split(r'(?<=^\d{6}) ', line)) if re.match(r'^\d{6}', line) else line for line in split_data]
    
    # Split the modified data into lines again
    split_data = '\n'.join(split_data).split('\n')
    
    # First chunk of 6 lines
    first_chunk = split_data[0:6]

    # Special case: chunk of 7 lines
    second_chunk = split_data[6:13]

    # Rest of the data: chunks of 6 lines
    rest_of_chunks = [split_data[i:i + 6] for i in range(13, len(split_data), 6)]

    # Combine all chunks
    chunks = [first_chunk, second_chunk] + rest_of_chunks

    # Parse each chunk into a dictionary
    records = []
    for chunk in chunks:
        
        # Handle the special case where the title spans multiple lines
        if len(chunk) == 7 and "Svaz letců svobodného Československa (Českoslovenští letci v boji za obnovu československé demokracie 1951–2017" in chunk[2] and "Free Czechoslovak Air Force Association (Czechoslovak Airmen Fighting for the Restoration of Democracy in Czechoslovakia 1951–2017)" in chunk[3]:
            title = chunk[2] + " " + chunk[3]
            authors = chunk[4]
            Id = chunk[5]
            percent = chunk[6]
        else:
            title = chunk[2]
            authors = chunk[3]
            Id = chunk[4]
            percent = chunk[5]

        record = {
            "type": chunk[0],
            "year": chunk[1],
            "title": title,
            "authors": authors,
            "Id": Id,
            "percent": percent
        }
        records.append(record)

        # link_href = "https://apl.unob.cz/vvi/Vysledek/" + Id
        # click_link_and_extract_data(driver, link_href)
    # Write the records to the file in JSON format
    with open("data.json", "w", encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>')
    
    
    # link_clicked = False
    # while not link_clicked:
    #     try:
    #         link = driver.find_element(By.XPATH, "//a[contains(@href,'Vysledek') and contains(@href,'563052')]")
    #         link.click()
    #         link_clicked = True
    #     except Exception as e:
    #         pass

    # if link_clicked:
    #     data2 = click_link_and_extract_data(driver, "https://apl.unob.cz/vvi/Vysledek/563052")
    # with open("data2.json", "w", encoding='utf-8') as f:
    #     json.dump(data2, f, ensure_ascii=False, indent=4)
    
    
      
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