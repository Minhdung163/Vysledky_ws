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
    username = getpass.getpass()
    password = getpass.getpass()
    data = get_data("https://apl.unob.cz/vvi/Vysledky", username, password)
    
    with open("data.json", "w", encoding = "utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=lambda o: '<not serializable>')
      
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