from app import celery
from random import randint, randrange
from app.models import Market, Page
from app import db
from flask import current_app
import requests
from app.rechem_scraping import rget
from time import sleep
import logging


@celery.task(bind=True)
def rechem_single_page(self):

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
    rechem = Market.query.filter_by(name="rechem_real").first()
    last_updated_listing = rechem.latest_page_for_each_listing()[0].listing
    url = last_updated_listing.url

    self.update_state(state='PROGRESS',
                      meta={'url': url, 'status': "Attempting to scrape {}".format(url)})

    content = rget(url, session)  # note that automatic retries are part of rget
    if content is None:
        self.update_state(state='FAILURE')
        return {'url': url, 'status': "Unable to reach {}".format(url)}
    else:
        db.session.add(Page(listing_id=last_updated_listing.id, html=content.text))
        db.session.commit()

        self.update_state(state='SUCCESS')
        return {'url': url, 'status': "Successfully scraped {} and entered in db".format(url)}


@celery.task(bind=True)
def rechem_routine_task(self):

    # stats tracked over time
    successes = 0
    failures = 0
    pages_processed = 0

    self.update_state(state='PENDING',
                      meta={'status': "Prioitizing page scraping queue"})

    # find market and pages to scrape
    # TODO: create clear error message in rechem market is not found
    rechem = Market.query.filter_by(name="rechem_real").first()
    latest_pages = rechem.latest_page_for_each_listing()
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

    for i, page in enumerate(latest_pages):
        pages_processed += 1
        current_url = page.listing.url
        next_url = ""
        if i+1 < len(latest_pages):
            next_url = latest_pages[i+1].listing.url
        self.update_state(state='PROGRESS',
                          meta={'current': pages_processed, 'total': total, 'successes': successes,
                                'failures': failures, 'url': current_url, 'next_url': next_url, 'sleeptime': 0,
                                'status': "Attempting to scrape {}".format(current_url)})

        content = rget(current_url, session)  # note that automatic retries are part of rget

        if content is None:
            logging.warning("Unable to reach product: {}".format(page.listing.url))
            failures += 1
            status = "Failed to reach {}".format(current_url)
        else:
            logging.info("attempting to add page with listing id: {} and html: {}".format(page.listing.id,
                                                                                          content.text[:15]))
            with current_app._get_current_object().app_context():
                db.session.add(Page(listing_id=page.listing.id, html=content.text))
                db.session.commit()

            successes += 1
            status = "Successfully scraped {} \n waiting before attempting next page".format(current_url)

        sleeptime = randint(120, 240)
        for remaining in range(sleeptime, 0, -1):
            self.update_state(state='PROGRESS',
                              meta={'current': pages_processed, 'total': total, 'successes': successes,
                                    'failures': failures, 'url': current_url, 'next_url': next_url, 'sleeptime': remaining,
                                    'status': status})
            sleep(1)

    self.update_state(state='SUCCESS')
    return {'current': pages_processed, 'total': total, 'successes': successes, 'failures': failures,
            'status': 'Completed attempting to scrape all known pages', 'result': 42}


@celery.task(bind=True)
def test_task(self):

    self.update_state(state='PENDING',
                      meta={'status': "Beginning loop"})
    total = 20
    for i in range(total):
        logging.info("on loop {}".format(i+1))
        status = "Working through task {} of {}".format(i + 1, total)
        db.session.add(Page(listing_id=1, html="test"))
        db.session.commit()
        sleeptime=4
        for remaining in range(sleeptime, 0, -1):
            self.update_state(state='PROGRESS',
                              meta={'current': i + 1, 'total': total, 'successes': i + 1,
                                    'failures': 0, 'sleeptime': remaining, 'status': status})
            sleep(1)

    self.update_state(state='SUCCESS')
    return {'current': total, 'total': total, 'successes': 5, 'failures': 0,
            'status': 'Completed'}

