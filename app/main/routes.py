from flask import render_template, flash, redirect, url_for, request, g, current_app, jsonify, send_from_directory
from flask_login import current_user, login_required
from app import db
from app.models import User, Country, Drug, Listing, Market, Page
from app.main import bp
from app.main.forms import EditProfileForm, SearchForm, CreateMockDataForm
from app.main.graphs import create_plot
import numpy as np
import os
from random import randrange, randint, random, sample
from datetime import datetime, timedelta
import time
import mock_data
from ..tasks import rechem_routine_task

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@bp.route('/data_summary')
@login_required
def index():
    markets = Market.query.all()
    return render_template('data_summary.html', markets=markets)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    return render_template('search.html', title='Search')

@bp.route('/drugs')
@login_required
def drugs():
    drugs = Drug.query.all()
    markets = Market.query.all()
    return render_template('drugs.html', drugs=drugs, markets=markets, title="Drugs")

@bp.route('/drug')
@login_required
def drug():
    market_id = request.args.get('market_id', None)
    drug_id = request.args.get('drug_id', None)
    market = Market.query.filter_by(id=market_id).first()
    drug = Drug.query.filter_by(id=drug_id).first()
    pages = market.pages()
    prices = [page.price for page in pages]
    dates = [page.timestamp for page in pages]
    bar = create_plot(dates, prices)
    if drug is None or market is None:
        title = "N/A"
    else:
        title = "{} - {}".format(market.name, drug.name)
    return render_template('drug.html', plot=bar, title=title)

@bp.route('/rename_market', methods=['GET', 'POST'])
@login_required
def rename_market():
    market = Market.query.filter_by(id=request.form['market_id']).first()
    new_name = request.form['new_name']
    if market:
        market.name = new_name
    return ('', 204)

@bp.route('/delete_market', methods=['GET', 'POST'])
@login_required
def delete_market():
    market = Market.query.filter_by(id=request.form['market_id']).first()
    if market:
        db.session.delete(market)
        db.session.commit()
    markets = Market.query.all()
    # TODO: may be better to return ('', 204) for this. We may want to delete through this route in the future on
    # TODO: a different page and not return the table. Create a separate route to get markets and render table
    return render_template('_data_summary_table.html', markets=markets)

@bp.route('/create_market', methods=['GET', 'POST'])
@login_required
def create_market():
    name = request.form['name']
    market = Market.query.filter_by(name=name).first()
    if market:
        flash('{} is already a market. Use a different name.'.format(name))
    else:
        market = Market(name=name)
        db.session.add(market)
        db.session.commit()
    markets = Market.query.all()
    # TODO: may be better to return ('', 204) for this. We may want to delete through this route in the future on
    # TODO: a different page and not return the table. Create a separate route to get markets and render table
    return render_template('_data_summary_table.html', markets=markets)


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


# @bp.route('/drugs')
# @login_required
# def drugs():
#     c_tuples = DN1_listing.query.with_entities(DN1_listing.origin_id).distinct().all() # returns unique ids in tuples
#     c_tuples += DN2_listing.query.with_entities(DN2_listing.origin_id).distinct().all()
#     countries = []
#     for c in c_tuples:
#         country = Country.query.filter_by(name=c[0]).first()
#         if country is not None:
#             countries.append(country)
#
#     rechem_listings = Rechem_listing.query.all()
#
# @bp.route('/drugs/<country_id>')
# @login_required
# def country(country_id):
#     country = Country.query.filter_by(id=country_id).first()


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
    return ('', 204)

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


# @bp.route('/celery_test', methods=['GET', 'POST'])
# def celery_test():
#     return render_template('celery_test.html')
#
#
# @bp.route('/testtask', methods=['POST'])
# def testtask():
#     market_id = 2  # TODO: replace with user input
#     task = test_task.apply_async()
#     return jsonify({}), 202, {'Location': url_for('main.taskstatus', task_id=task.id)}
#
#
# @bp.route('/status/<task_id>')
# def taskstatus(task_id):
#     task = test_task.AsyncResult(task_id)
#     if task.state == 'PENDING':
#         response = {
#             'state': task.state,
#             'current': 0,
#             'total': 1,
#             'status': 'Pending...'
#         }
#     elif task.state != 'FAILURE':
#         response = {
#             'state': task.state,
#             'current': task.info.get('current', 0),
#             'total': task.info.get('total', 1),
#             'status': task.info.get('status', '')
#         }
#         if 'result' in task.info:
#             response['result'] = task.info['result']
#     else:
#         # something went wrong in the background job
#         response = {
#             'state': task.state,
#             'current': 1,
#             'total': 1,
#             'status': str(task.info),  # this is the exception raised
#         }
#     return jsonify(response)

@bp.route('/rechem_routine_check', methods=['GET', 'POST'])
def rechem_routine_check():
    return render_template('rechem_routine_check.html')


@bp.route('/rechemroutinetask', methods=['POST'])
def rechemroutinetask():
    task = rechem_routine_task.apply_async()
    return jsonify({}), 202, {'Location': url_for('main.taskstatus', task_id=task.id)}


@bp.route('/status/<task_id>')
def taskstatus(task_id):
    task = rechem_routine_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'sleeptime': 0,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'sleeptime': task.info.get('sleeptime', 0),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'sleeptime': 0,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)
