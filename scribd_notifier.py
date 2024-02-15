from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup
import argparse
import requests
from urllib.parse import urlparse, parse_qs

#############
# Argument Handling
parser = argparse.ArgumentParser()
parser.add_argument('scribd_search_url', help='URL from Scribd Search')
parser.add_argument('-d', '--discord', help='Discord Webhook URL')
parser.add_argument('-s', '--slack', help='Slack Webhook URL')
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

if elements != None:
    for li_tag in elements.find_all('li'):
        curr_title = li_tag.find(class_="visually_hidden").text
        new_titles.append(curr_title)
        
        if args.verbose:
            print(f"Found: {curr_title}")
else:
    print("No Documents Found In Query!")

#TODO:Go For Multiple Pages if Exists... 

#############
# Read in from file for previous results
old_titles = []

query_params = parse_qs((urlparse(args.scribd_search_url).query))
search_query = query_params.get('query', [''])[0].replace(" ", "_")

try: 
    with open(search_query + ".txt", "r") as f:
        old_titles = f.readlines()
    if args.verbose:
        print("File existed, sucessfully opened.")
except FileNotFoundError:
    if args.verbose:
        print(f"File doesn't exist, creating now.")
    try: 
        open(search_query + ".txt", "x")
    except Exception as e:
        print(f"{e} occurred creating file!")
        exit(-1)
except Exception as e:
    print(f"{e} occured reading file!")
    exit(-1)

#############
# Compare and Ping
new_titles.sort()
old_titles.sort() # Redundant???

i = 0
if len(old_titles) != 0:
    for title in new_titles:
        if title.upper().strip() == old_titles[i].upper().strip():
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
            elif args.slack != None:
                try:
                    payload = {
                        'text': f"New Document: {title}"
                    }
                    response = requests.post(args.slack, json=payload)
                except Exception as e:
                    print(f"Error {e} posting to Slack")
            else: 
                print(f"Found new title: {title}")
else: 
    for title in new_titles:
        if args.discord != None:
                try:
                    payload = {
                        'content': f"New Document: {title}"
                    }
                    response = requests.post(args.discord, json=payload)
                except Exception as e:
                    print(f"Error {e} posting to Discord")
        elif args.slack != None:
            try:
                payload = {
                    'text': f"New Document: {title}"
                }
                response = requests.post(args.slack, json=payload)
            except Exception as e:
                print(f"Error {e} posting to Slack")
        else: 
            print(f"Found new title: {title}")

#TODO:Cleanup this code
#TODO:Put link to document in message

#############
# Save New Array over file
with open(search_query + ".txt", "w") as f:
    f.writelines("%s\n" % l for l in new_titles)

#############
# Exit and cleanup
driver.quit()