from . import celery
from datetime import datetime, timedelta
import numpy as np
from random import randint, randrange
from app.models import Drug, Market, Listing
from app import db
import time

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

@celery.task()
def add_together(a, b):
    return a + b


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