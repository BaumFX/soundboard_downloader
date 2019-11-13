import os
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests

url = "http://www.soundboard.com/sb/username"

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

driver = webdriver.Firefox()

driver.get(url)
link_list = list()

print("fetching links...")
for div in driver.find_element_by_xpath("//*[@id=\"playlist\"]").find_elements_by_tag_name("div"):
    for tag in div.find_elements_by_css_selector("*"):
        if tag.get_attribute("href") is None:
            continue

        if "sb/sound/" in tag.get_attribute("href"):
            link_list.append(tag.get_attribute("href"))
            print("fetched link.")

download_list = list()

for link in link_list:
    driver.get(link)
    onclick = driver.find_element_by_xpath("//*[@id=\"btnDownload\"]").get_attribute("onclick")
    download_list.append(onclick)
    print("appended download link.")

count = 0
for link in download_list:
    print("downloading file.")
    link = link[:-3]
    link = link[15:]

    download_result = requests.get(link)
    open("C:/path/to/folder/" + str(count) + ".mp3", 'wb').write(download_result.content)
    count += 1

driver.close()
