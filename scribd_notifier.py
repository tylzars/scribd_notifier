from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup
import argparse
import requests

#############
# Argument Handling
parser = argparse.ArgumentParser()
parser.add_argument('scribd_search_url', help='URL from Scribd Search')
parser.add_argument('-d', '--discord', help='Discord Webhook URL')
parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
args = parser.parse_args()

#############
# Selenium Handling
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

#############
# Get HTML Page
scribd_url = args.scribd_search_url
driver.get(scribd_url)
sleep(2)
soup = BeautifulSoup(driver.page_source, 'html.parser')

if args.verbose:
    print(f"Got HTML Source from Scribd Search")

#############
# Get All Title In Search Result
new_titles = []
elements = soup.find('ul', class_="_1kBhLK _3S_oce _1gyGKg _3MyJWQ _3qn-sP _3NAnxI _2q7Jiq _3MqOhW")
# XPATH = //*[@id="root"]/div/main/section/div[2]/div/div/ul

for li_tag in elements.find_all('li'):
    curr_title = li_tag.find(class_="visually_hidden").text
    new_titles.append(curr_title)
    
    if args.verbose:
        print(f"Found: {curr_title}")

#TODO:Go For Multiple Pages if Exists... 

#############
# Read in from file for previous results
old_titles = []
with open("scribd_prev_search.txt", "r") as f:
    old_titles = f.readlines()

#TODO:Use query to name file to allow multiple queries

#############
# Compare and Ping
new_titles.sort()
old_titles.sort() # Redundant???

i = 0
for title in new_titles:
    if title == old_titles[i]:
        i += 1
    else: 
        if args.discord != None:
            try:
                payload = {
                    'content': f"New Document: {title}"
                }
                response = requests.post(args.discord, json=payload)
            except Exception as e:
                print(f"Error {e} posting to Discord")
        else: 
            print(f"Found new title: {title}")

#TODO:Add more notification methods

#############
# Save New Array over file
with open("scribd_prev_search.txt", "w") as f:
    f.writelines(new_titles)

#############
# Exit and cleanup
driver.quit()