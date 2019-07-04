from app import celery
from random import randint, randrange
from app.models import Market, Page
from app import db
import time
import requests
from app.rechem_scraping import rget
from time import sleep
import logging


@celery.task(bind=True)
def rechem_routine_task(self):

    # stats tracked over time
    successes = 0
    failures = 0
    pages_processed = 0

    self.update_state(state='PENDING',
                      meta={'status': "Prioitizing page scraping queue"})

    # find market and pages to scrape
    rechem = Market.query.filter_by(name="rechem_real").first()
    latest_pages = rechem.latest_pages()
    total = len(latest_pages)

    self.update_state(state='PENDING',
                      meta={'status': "{} pages found. Beginning scraping".format(total)})


    # create session object with some generic headers
    # TODO: add randomized headers in. This as well as creating the session itself could probably be
    #  done in rechem_scraping
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

    for page in latest_pages:
        pages_processed += 1
        content = rget(page.listing.url, session)
        if content is None:
            logging.warning("Unable to reach product: {}".format(page.listing.url))
            failures += 1
        else:
            db.session.add(Page(listing_id=page.listing_id, html=content.text))
            db.session.commit()
            successes += 1

        sleeptime = randint(120, 240)
        self.update_state(state='PROGRESS',
                          meta={'current': pages_processed, 'total': total, 'successes': successes,
                                'failures': failures, 'sleeptime': sleeptime, 'status': "waiting"})
        sleep(sleeptime)
    self.update_state(state='SUCCESS')
    return {'current': pages_processed, 'total': total, 'successes': successes, 'failures': failures,
            'status': 'Completed attempting to scrape all known pages', 'result': 42}

@celery.task(bind=True)
def test_task(self):
    for i in range(1000):
        logging.info("on loop {}".format(i))
        self.update_state(state='PROGRESS',
                          meta={'current': i+1, 'total': 1000, 'successes': 0,
                                'failures': 0, 'sleeptime': 3, 'status': "waiting"})
        time.sleep(3)
    self.update_state(state='SUCCESS')
    return {'current': 1000, 'total': 1000, 'successes': 0, 'failures': 0,
            'status': 'Completed', 'result': 42}