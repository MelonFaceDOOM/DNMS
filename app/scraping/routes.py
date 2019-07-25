from flask import render_template, flash, redirect, url_for, request, current_app, jsonify, json
from flask_login import login_required
from app import db
from app.models import Country, Drug, Listing, Market, Page
from app.scraping import bp
from app.scraping.forms import CreateMockDataForm
from app.scraping import mock_data
import numpy as np
from random import randrange, randint
from datetime import datetime, timedelta
import sqlite3
import ast
import pandas as pd
import redis
import re

# assuming rs is your redis connection
def is_redis_available():
    pattern = "(redis:\/\/)(h:)*([-@A-z0-9.]+):([0-9]+)(\/0)*"
    match = re.match(pattern, current_app.config['CELERY_BROKER_URL'])
    url = match.groups()[2]
    # if match.groups()[1] is not None:
    #     url = match.groups()[1] + url
    port = match.groups()[3]
    print(url, port)
    r = redis.Redis(host=url, port=port, socket_connect_timeout=1)  # short timeout for the test
    try:
        r.ping()
        return True
    except redis.exceptions.ConnectionError:
        return False


@bp.route('/scrapers')
def scrapers():
    if is_redis_available():
        redis_running = True
    else:
        redis_running = False
    return render_template("scrapers.html", scrapers=current_app.scrapers, redis_running=redis_running)


@bp.route('/raw_results/<page_id>')
def raw_results(page_id):
    page = Page.query.filter_by(id=page_id).first()
    return render_template("raw_results.html", page=page)


@bp.route('/test')
def test():
    scraper_name = "test"
    scraper = current_app.scrapers[scraper_name]

    if scraper.is_running():
        status_url = url_for("scraping.check_status", scraper_name=scraper_name)  # signals that task is running
    else:
        status_url = None  # also works signal that indicates there is no task running

    return render_template('test.html', status_url=status_url)

@bp.route('/rechem')
def rechem():
    # It might make sense to eventually just have one task page that takes a task_name argument, but I'm not sure
    # How different the templates will be for different tasks. I imagine a crawler for a dark net site might
    # Be significantly different, so I don't think it would run off the same template
    scraper_name = "rechem"
    scraper = current_app.scrapers[scraper_name]
    market = Market.query.filter_by(name="rechem_real").first()  # TODO: replace with "scraper_name"
    page = request.args.get('page', 1, type=int)

    if market:
        pages = market.latest_pages().paginate(page, 50, False)
        next_url = url_for('scraping.rechem', page=pages.next_num) \
            if pages.has_next else None
        prev_url = url_for('scraping.rechem', page=pages.prev_num) \
            if pages.has_prev else None
        pages = pages.items
    else:
        pages = []
        next_url = None
        prev_url = None

    # TODO: include a button to run a task to re-check all listings on rechem
    if scraper.is_running():
        status_url = url_for("scraping.check_status", scraper_name=scraper_name)  # signals that task is running
    else:
        status_url = None  # signals that there is no task running

    return render_template('rechem.html', status_url=status_url, pages=pages,
                           prev_url=prev_url, next_url=next_url)


@bp.route('/starttask', methods=['POST'])
@login_required
def starttesttask():
    scraper_name = request.form.get('scraper_name', None)
    scraper = current_app.scrapers[scraper_name]
    if scraper.is_running():
        status_url = url_for("scraping.check_status", scraper_name=scraper_name)  # signals that task is running
        return jsonify({}), 202, {'Location': status_url}
    else:
        status_url = None  # also works signal that indicates there is no task running
        response = scraper.start_task()
        return response

@bp.route('/kill_task', methods=['POST'])
@login_required
def kill_task():
    scraper_name = request.form.get('scraper_name', None)
    scraper = current_app.scrapers[scraper_name]
    if scraper.is_running():
        scraper.kill_task()
        response = "task killed"
    else:
        response = "no task found"
    return jsonify({'response': response}), 202


@bp.route('/check_status/<scraper_name>', methods=['GET'])
@login_required
def check_status(scraper_name):
    try:
        scraper = current_app.scrapers[scraper_name]
    except:
        return jsonify({'state': "Scraper not found"})
    return jsonify(scraper.status())



####################################
######### MOCK DATA ROUTES #########
####################################
# Some may be outdated
@bp.route('/create_mock_data/market/<market_id>', methods=['GET', 'POST'])
@login_required
def create_mock_data(market_id):
    form = CreateMockDataForm()
    market = Market.query.filter_by(id=market_id).first()
    if form.validate_on_submit():
        if not market:
            flash("market not found")
            return redirect(url_for('main.index'))

        total_pages = form.number_of_cases.data
        min_price = form.min_price.data
        max_price = form.max_price.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        # sellers = list(range(1, 10)) if form.seller.data else []
        # origins = Country.query.all() if form.origin.data else []

        listings = market.listings
        pages_per_listing = int(total_pages/listings.count())
        spread = int(pages_per_listing * 0.4)
        spread = 1 if spread == 0 else spread
        base = pages_per_listing - spread
        base = 0 if base < 0 else base

        listings_and_pages = []
        for listing in listings:
            pages = randint(base, pages_per_listing + spread)
            listings_and_pages.append([listing, pages])

        pre_total = sum([lp[1] for lp in listings_and_pages])

        difference = total_pages - pre_total
        for i in range(abs(difference)):
            if difference > 0:
                listings_and_pages[randint(0, len(listings_and_pages)) - 1][1] += 1
            else:
                idx = randint(0, len(listings_and_pages)) - 1
                while True:
                    if listings_and_pages[idx][1] > 0:
                        listings_and_pages[idx][1] -= 1
                        break
                    else:
                        idx += 1 if idx < len(listings_and_pages) - 1 else 0

        pages = []
        for lp in listings_and_pages:
            for i in range(lp[1]):
                delta = end_date - start_date
                int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
                random_delta = randrange(int_delta)
                date = start_date + timedelta(seconds=random_delta)
                price = np.random.randint(min_price, max_price)
                page = Page(name="mock data sample", listing=lp[0], html="mock data sample",timestamp=date,price=price)
                pages.append(page)

        db.session.add_all(pages)
        db.session.commit()



        # # create one listing for each drug, or a couple if sellers are used
        # for drug in drugs:
        #     rand_sellers = sample(population=sellers, k=randint(1, 3)) if sellers else None
        #     rand_origins = sample(population=origins, k=len(rand_sellers)) if origins else None
        #     while True:
        #         seller = rand_sellers.pop() if rand_sellers else ''
        #         origin = rand_origins.pop() if rand_origins else None
        #         if seller:
        #             url = "https://{}.com/mock_data{}/drug={}".format(
        #                     market.name,
        #                     "/seller={}".format(seller) if seller else '',
        #                     drug)
        #             listings.append(Listing(market=market, drug=drug, url=url, seller=seller, origin=origin))
        #         if not rand_sellers:
        #             break
        # db.session.add_all(listings)
        # db.session.commit()



        return redirect(url_for('main.index'))
    return render_template('create_mock_data.html', form=form, market_name=market.name)


@bp.route('/seed_database/', methods=['GET', 'POST'])
@login_required
def seed_database():
    '''add in Drugs, Countries, and a few markets'''
    drugs = []
    for d in mock_data.drugs:
        q = Drug.query.filter_by(name=d).first()
        if q is None:
            drug = Drug(name=d)
            drugs.append(drug)
    db.session.add_all(drugs)
    db.session.commit()

    countries = []
    for c in mock_data.all_countries:
        q = Country.query.filter_by(name=c[0]).first()
        if q is None:
            country = Country(name=c[0], c2=c[1])
            countries.append(country)
    db.session.add_all(countries)
    db.session.commit()
    ms = ["Rechem", "DN1", "DN2"]
    markets = []
    for m in ms:
        q = Market.query.filter_by(name=m).first()
        if q is None:
            market = Market(name=m)
            markets.append(market)
    db.session.add_all(markets)
    db.session.commit()
    return '', 204

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


@bp.route('/add_mock_listings', methods=['GET', 'POST'])
@login_required
def add_mock_listings():
    market = Market.query.filter_by(id=request.form['market_id']).first()
    drugs = request.form.getlist('drugs[]')
    listings = []
    for d in drugs:
        drug = Drug.query.filter_by(name=d).first()
        url = "www.{}.com/mock_data/{}".format(market.name, drug.name)
        listings.append(Listing(drug=drug, market=market, url=url))
    db.session.add_all(listings)
    db.session.commit()

    drugs = Drug.query.all()
    drugs_not_in_market = [drug for drug in drugs if not Listing.query.filter_by(market=market, drug=drug).first()]
    return render_template('_unused_drug_multi_select.html', drugs=drugs_not_in_market)


@bp.route('/create_mock_listings/market/<market_id>', methods=['GET', 'POST'])
@login_required
def create_mock_listings(market_id):
    market = Market.query.filter_by(id=market_id).first()

    if not market:
        flash("market not found")
        return redirect(url_for('main.index'))

    drugs = Drug.query.all()
    drugs_not_in_market = [drug for drug in drugs if not Listing.query.filter_by(market=market, drug=drug).first()]
    return render_template('create_mock_listings.html', market=market, drugs=drugs_not_in_market)


@bp.route("/sf4fefffdsf")
@login_required
def sf4fefffdsf():
    c = sqlite3.connect('app.db')

    countries = pd.read_sql_query("SELECT * FROM country", c)
    new_countries = []
    for i, row in countries.iterrows():
        country = Country(name=row['name'], c2=row['c2'])
        if not Country.query.filter_by(name=country.name).first():
            new_countries.append(country)
    db.session.add_all(new_countries)
    db.session.commit()

    drugs = pd.read_sql_query("SELECT * FROM drug", c)
    new_drugs = []
    for i, row in drugs.iterrows():
        drug = Drug(name=row['name'])
        if not Drug.query.filter_by(name=drug.name).first():
            new_drugs.append(drug)
    db.session.add_all(new_drugs)
    db.session.commit()

    markets = pd.read_sql_query("SELECT * FROM market", c)
    new_markets = []
    for i, row in markets.iterrows():
        market = Market(name=row['name'])
        if not Market.query.filter_by(name=market.name).first():
            new_markets.append(market)
    db.session.add_all(new_markets)
    db.session.commit()

    listings = pd.read_sql_query("SELECT * FROM listing", c)
    rechem_listings = listings[listings['market_id'] == '4']

    new_listings = []
    for i, row in rechem_listings.iterrows():
        market_name = markets[markets['id'] == int(row['market_id'])]['name'].item()
        new_market_id = Market.query.filter_by(name=market_name).first().id

        drug_name = drugs[drugs['id'] == row['drug_id']]['name'].item()
        new_drug_id = Drug.query.filter_by(name=drug_name).first().id

        listing = Listing(url=row['url'], seller=None, timestamp=row['timestamp'],
                          market_id=new_market_id, drug_id=new_drug_id, origin_id=None)
        if not Listing.query.filter_by(url=listing.url).first():
            new_listings.append(listing)
    db.session.add_all(new_listings)
    db.session.commit()

    # Get all pages with a listing id that is from the rechem market
    pages = pd.read_sql_query("SELECT * FROM page", c)
    rechem_pages = pages[pages['listing_id'].isin(rechem_listings['id'])]

    new_pages = []
    for i, row in rechem_pages.iterrows():
        listing_url = listings[listings['id'] == int(row['listing_id'])]['url'].item()
        new_listing_id = Listing.query.filter_by(url=listing_url).first().id
        page = Page(name=row['name'], html=row['html'], timestamp=row['timestamp'], listing_id=new_listing_id)
        if not Page.query.filter_by(listing_id=page.listing_id, timestamp=page.timestamp).first():
            new_pages.append(page)
        else:
            print("page already found:")
    db.session.add_all(new_pages)
    db.session.commit()
    return "data successfully added"

# @bp.route('/import_rechem_data/', methods=['GET', 'POST'])
# @login_required
# def import_rechem_data():
#     c = sqlite3.connect('rechem_listings.db')
#     with open('rechem_drug_titles', 'r') as f:
#         s = f.read()
#         drug_title_dict = ast.literal_eval(s)
#
#
#     rechem_pages = pd.read_sql_query("SELECT * FROM Listings", c)
#     rechem_listings = pd.read_sql_query("SELECT * FROM Listing_index", c)
#
#     for i, row in rechem_listings.iterrows():
#         rechem_listings.loc[i, 'drug'] = drug_title_dict[row['title']]
#
#     m = Market.query.filter_by(name="rechem_real").first()
#     if not m:
#         m = Market(name="rechem_real")
#         db.session.add(m)
#         db.session.commit()
#         print("market added")
#
#     # delete existing data
#     # m.pages() needs to be deleted one at a time, as far as I can tell, whereas m.listings can be deleted all at once
#     # There is probably a way to delete m.pages() all at once, but it doesn't seem worth figuring out
#     # pages = m.pages()
#     # [db.session.delete(p) for p in pages]
#     # listings = m.listings
#     # listings.delete()
#     # db.session.commit()
#
#     print("{} listings and {} pages remaining".format(m.listings.count(), m.pages().count()))
#
#     listings = []
#     for i, row in rechem_listings.iterrows():
#         drug = Drug.query.filter_by(name=row['drug']).first()
#         if not drug:
#             db.session.add(Drug(name=row['drug']))
#             db.session.commit()
#         # check if listing for this url exists. if not, add it.
#         listing = Listing.query.filter_by(url=row['url']).first()
#         if not listing:
#             listings.append(Listing(url=row['url'], market=m, drug=drug))
#     if listings:
#         db.session.add_all(listings)
#         db.session.commit()
#         print("Listings added")
#
#     pages = []
#     for i, row in rechem_pages.iterrows():
#         original_listing = rechem_listings[rechem_listings['id'] == row['listing_index_id']]
#         url = original_listing['url'].item()
#         listing_name = original_listing['title'].item()
#
#         listing = Listing.query.filter_by(url=url).first()
#         # check if a page exsits for this time/listing. If not, add it.
#         timestamp = datetime.strptime(row['scraped_time'], "%Y-%m-%d %H:%M:%S")
#         page = Page.query.filter_by(listing=listing, timestamp=timestamp).first()
#         if not page:
#             pages.append(Page(html=row['page_text'], timestamp=timestamp, name=listing_name, listing=listing))
#
#     if pages:
#         db.session.add_all(pages)
#         db.session.commit()
#         print("Pages added")
#         return '', 204

