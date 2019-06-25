from . import celery
from datetime import datetime, timedelta
import numpy as np
from random import randint, randrange
from app.models import Drug, Market, Listing, Page
from app import db
import time
import requests
from app.rechem_scraping import rget
from time import sleep
import logging

def generate_random_listing(drugs, market, min_price, max_price, start_date, end_date, sellers=[], origins=[]):
    delta = end_date - start_date
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_delta = randrange(int_delta)
    date = start_date + timedelta(seconds=random_delta)
    price = np.random.randint(min_price, max_price)
    drug = drugs[np.random.randint(0, len(drugs) - 1)]
    origin = origins[np.random.randint(0, len(origins) - 1)] if origins else None
    seller = sellers[np.random.randint(0, len(sellers) - 1)] if sellers else None
    listing = Listing(market=market, drug=drug, price=price, country=origin, seller=seller, date=date)
    return listing


@celery.task(bind=True)
def test_task(self):
    drugs = Drug.query.all()
    market = Market.query.filter_by(id=2).first()
    total = randint(10,50)
    start_date = datetime.strptime("01/01/2018", "%d/%m/%Y")
    end_date = datetime.strptime("01/12/2018", "%d/%m/%Y")
    for i in range(total):
        listing = generate_random_listing(drugs, market, 10, 100, start_date, end_date)
        db.session.add(listing)
        db.session.commit()
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': "adding mock data"})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!', 'result': 42}


@celery.task(bind=True)
def rechem_routine_task(self):
    rechem = Market.query.filter_by(name="rechem_real").first()
    latest_pages = rechem.latest_pages()

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
    session.headers = headers
    total = len(latest_pages)
    i = 0
    for page in latest_pages:
        i += 1
        content = rget(page.listing.url, session)
        if content is None:
            logging.warning("Unable to reach product: {}".format(page.listing.url))
        else:
            db.session.add(Page(listing_id=page.listing_id), html=content.text)
            db.session.commit()

        sleep_time = randint(120, 240)
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total, sleep_time: sleep_time,
                                'status': "waiting"})
        sleep(sleep_time)
    return {'current': 100, 'total': 100, 'status': 'Task completed!', 'result': 42}
