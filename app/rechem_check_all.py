import re
import requests
import sqlite3
from sqlite3 import IntegrityError
import os
import sys
from lxml import html
import logging
from rechem_scraping import rget

logging.basicConfig(level = logging.DEBUG, filename = "rechem_check_all.log")

class Rechem_organizer():
    def __init__(self):
        self.categories = []
        self.sub_categories = []
        self.products = []
        
    def classify_urls(self, requests_content, c):
        tree = html.fromstring(requests_content.text) 
        links = tree.xpath('//a')
        for link in links:
            try:
                url = link.attrib['href']
                r.classify_url(url, c)
            except:
                pass

    def classify_url(self, url, c):
        
        if re.match(".+route=product/category&path=\d+$", url):
            if url not in self.categories:
                self.categories.append(url)
        elif re.match(".+route=product/category&path=\d+_\d+$", url):
            if url not in self.sub_categories:
                self.sub_categories.append(url)
        elif re.match(".+route=product/product", url):
            # If a product is found, keep track of the url in To_scrape
            try:
                c.execute('INSERT INTO To_scrape VALUES (?)', (url,))
                conn.commit()
            except IntegrityError:
                logging.info("duplicate not entered into To_scrape for {}".format(url))
            
            # Check if this url is already in Listing_index, if no, save in self.products
            # Self.products serves as the queue for what will be scraped later
            c.execute("SELECT url FROM Listing_index")
            rows = c.fetchall()
            already_scraped = [row[0] for row in rows]
            if url not in already_scraped and url not in self.products:
                self.products.append(url)


c.execute('''CREATE TABLE IF NOT EXISTS Listing_index
    (id INTEGER PRIMARY KEY,
    title STRING NOT NULL UNIQUE,
    url TEXT NOT NULL);''')

c.execute('''CREATE TABLE IF NOT EXISTS Listings
    (id INTEGER PRIMARY KEY,
    page_text STRING,
    scraped_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    listing_index_id STRING,
    FOREIGN KEY (listing_index_id) REFERENCES Listing_index (id));''')

c.execute('''CREATE TABLE IF NOT EXISTS To_scrape
    (url STIRNG NOT NULL UNIQUE);''')
    
# Listing_index will ideally hold one listing title and url per item on the Rechem.ca website
# Listings will hold all listings ever scraped as well as a time component. The same listing (from Listing_index)
# can be scraped multiple times and appear in this table multiple times
# To_scrape is just a list of urls that have been found that aren't in listing_index that haven't yet been scraped.
# The purpose of To_scrape is not to lose this information in case the program crashes before they are scraped
    
    
# Create session object 
# using a session with cookies seems to generally get more consistent responses from rechem.ca
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;'
              'q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'referer': 'https://www.rechem.ca/index.php?route=common/home',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/73.0.3683.103 Safari/537.36'
}
session = requests.session()
session.headers=headers
r = Rechem_organizer() # object used to organize different types of links

# The table To_scrape will keep links that were found, but not yet scraped, in the previous attempt at running this
# These are moved to the r.products, which acts as the scraping queue
c.execute("""SELECT url FROM To_scrape""")
rows = c.fetchall()
listing_urls = [row[0] for row in rows]
for url in listing_urls:
    r.classify_url(url, c)

# Grab category links from the main page
content = rget("https://www.rechem.ca", session)
if content is None:
    logging.error('Unable to reach main page')
    sys.exit()
r.classify_urls(content, c)

# Go through categories and classify all links
for url in r.categories:
    content = rget(url, session)
    if content is None:
        logging.warning("Unable to reach category: {}".format(url))
    else:
        r.classify_urls(content, c)
        
# Go through all sub_category links that have been found up until this point and classify all the links within them
for url in r.sub_categories:
    content = rget(url, session, delay=True)
    if content is None:
        logging.warning("Unable to reach subcategory: {}".format(url))
    else:
        r.classify_urls(content, c)

# Go through all the product links
# Save page content associated with the link
# Remove the link from To_scrape
for url in r.products:
    content = rget(url, session)
    if content is None:
        logging.warning("Unable to reach product: {}".format(url))
    else:
        # Enter into listing index
        title = html.fromstring(content.text).xpath("//h1")[0].text
        try:
            c.execute("""INSERT INTO Listing_index (title, url) VALUES (?, ?)""",
                   (title, url))
            conn.commit()
        except IntegrityError:
            logging.info("duplicate not entered into Listing_index for {}".format(url))
        
        # Get listing_index_id for this listing
        c.execute("""SELECT id FROM Listing_index WHERE title=?""",
                (title,))
        rows = c.fetchall()
        listing_index_id = rows[0][0]
        
        # Enter into listing table
        c.execute("""INSERT INTO Listings (listing_index_id, page_text) VALUES (?, ?)""",
               (listing_index_id, content.text))
        conn.commit()
        
        # Remove url from To_scrape
        c.execute("""DELETE FROM To_scrape WHERE url=?""",(url,))