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

##############
# Helper Functions
def post_to_discord(title, link, author):
    try:
        payload = {
            'content': f"New Document: [{title}]({link}) from {author}"
        }
        response = requests.post(args.discord, json=payload)
    except Exception as e:
        print(f"Error {e} posting to Discord")

def post_to_slack(title, link, author):
    try:
        payload = {
            'text': f"New Document: <{link}|{title}> from {author}"
        }
        response = requests.post(args.slack, json=payload)
    except Exception as e:
        print(f"Error {e} posting to Slack")

#############
# Selenium Handling
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

#############
# Get HTML Page
scribd_url = args.scribd_search_url
try:
    driver.get(scribd_url)
    sleep(5)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    if args.verbose:
        print(f"Got HTML source from Scribd search")
except Exception as e:
    print(f"Error {e} occured getting HTML source")

#############
# Get All Title In Search Result
new_titles = []
elements = soup.find('ul', class_="_1kBhLK _3S_oce _1gyGKg _3MyJWQ _3qn-sP _3NAnxI _2q7Jiq _3MqOhW")
if elements == None:
    elements = soup.find('ul', class_="_1kBhLK _1gyGKg _3MyJWQ _3qn-sP _3NAnxI _2q7Jiq _3MqOhW")
# XPATH = //*[@id="root"]/div/main/section/div[2]/div/div/ul
# TODO:Switch to XPATH Parsing instead finding a guess to class names

if elements != None:
    for li_tag in elements.find_all('li'):
        # Get data
        curr_title = li_tag.find(class_="visually_hidden").text
        curr_title_link = li_tag.find('a', class_='FluidCell-module_linkOverlay__v8dDs')['href']
        curr_title_author = li_tag.find('span', {'data-e2e': 'author'}).text
        
        # Build dict and add to list
        curr_dict = {
            'title' : curr_title,
            'link' : curr_title_link,
            'author' : curr_title_author
        }
        new_titles.append(curr_dict)
        
        if args.verbose:
            print(f"Found: {curr_title}")
else:
    print("No Documents Found In Query!")

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

old_titles = [x.upper().strip() for x in old_titles]

#############
# Compare and Ping
if len(old_titles) != 0:
    for dict in new_titles:
        if dict['title'].upper().strip() not in old_titles:
            if args.discord != None:
                post_to_discord(dict['title'], dict['link'], dict['author'])
            elif args.slack != None:
                post_to_slack(dict['title'], dict['link'], dict['author'])
            else: 
                print(f"Found new title: {dict['title']}")
else: 
    for dict in new_titles:
        if args.discord != None:
            post_to_discord(dict['title'], dict['link'], dict['author'])
        elif args.slack != None:
            post_to_slack(dict['title'], dict['link'], dict['author'])
        else: 
            print(f"Found new title: {dict['title']}")

#############
# Save New Array over file
with open(search_query + ".txt", "w") as f:
    f.writelines("%s\n" % l['title'] for l in new_titles)

#############
# Exit and cleanup
driver.quit()