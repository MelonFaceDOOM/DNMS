import sqlite3
from datetime import datetime
from random import randint
from time import sleep
import logging

# Connect to database and create tables
db_filepath = "rechem_listings.db"
conn = sqlite3.connect(db_filepath)
c = conn.cursor()
c.execute("SELECT id, url FROM Listing_index")
listing_index = c.fetchall()
latest_listings = [] # will hold urls and their latest scraping time

# get all listings from listing_index. Keep the url and only the latest scraping time.
for row in listing_index:
    c.execute("SELECT scraped_time FROM Listings WHERE Listing_index_id=?", (row[0],))
    times = c.fetchall() # will be None if no entries found in Listings
    if times:
        times = [x[0] for x in times]
        times.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d %H:%M:%S"))
        newest = times[-1]
    else:
        newest = "1900-01-01 12:00:00" # default old time so it is placed at the front of the queue
    latest_listings.append((row[0], row[1], newest)) # Listing_index_id, url, timestamp
    
# sort urls with oldest scrape times at the start.
latest_listings.sort(key=lambda listing: datetime.strptime(listing[2], "%Y-%m-%d %H:%M:%S"))
ordered_listings = [{"Listing_index_id":x[0], "url":x[1]} for x in latest_listings]

import requests
from app.rechem_scraping import rget
        
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

for listing in ordered_listings:
    sleep(randint(1200,2400)) # Make a request every 20-40 minutes
    content = rget(listing['url'], session)
    if content is None:
        logging.warning("Unable to reach product: {}".format(url))
    else:
        c.execute("""INSERT INTO Listings (listing_index_id, page_text) VALUES (?, ?)""",
               (listing['Listing_index_id'], content.text))
        conn.commit()