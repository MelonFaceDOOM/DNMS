from flask import render_template, flash, redirect, url_for, request, g, current_app, jsonify, send_from_directory
from flask_login import current_user, login_required
from app import db
from app.models import User, Country, Drug, Listing, Market
from app.main import bp
from app.main.forms import EditProfileForm, SearchForm, CreateMockDataForm
from app.main.graphs import create_plot
import numpy as np
import os
from random import randrange, randint
from datetime import datetime, timedelta
import time

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
@login_required
def index():
    # drugs = Drug.query.all()
    # listings = Rechem_listing.query.filter_by(drug=drugs[0]).all()
    return render_template('index.html', title="Home")


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
    listings = Listing.query.filter_by(market=market, drug=drug).all()
    prices = [listing.price for listing in listings]
    dates = [listing.date for listing in listings]
    bar = create_plot(dates, prices)
    if drug is None or market is None:
        title = "N/A"
    else:
        title = "{} - {}".format(market.name, drug.name)
    return render_template('drug.html', plot=bar, title=title)


@bp.route('/data_summary')
@login_required
def data_summary():
    markets = Market.query.all()
    return render_template('data_summary.html', markets=markets)

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


def generate_random_listing(drugs, market, min_price, max_price, start_date, end_date, sellers=[], origins=[]):
    delta = end_date - start_date
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_delta = randrange(int_delta)
    date = start_date + timedelta(seconds=random_delta)
    price = np.random.randint(min_price, max_price)
    drug = drugs[np.random.randint(0, len(drugs) - 1)]
    if origins:
        origin = origins[np.random.randint(0, len(origins) - 1)]
    if sellers:
        seller = sellers[np.random.randint(0, len(sellers) - 1)]
    listing = Listing(market=market, drug=drug, price=price, country=origin, seller=seller, date=date)
    return listing

# disabled to avoid accidentally create more data
# todo - modify to make an actual page with controls and stuff to allow the user to generate data if they wish
@bp.route('/create_mock_data/market/<market_id>', methods=['GET', 'POST'])
@login_required
def create_mock_data(market_id):
    form = CreateMockDataForm()
    market = Market.query.filter_by(id=market_id).first()
    if form.validate_on_submit():
        if not market:
            flash("market not found")
            return redirect(url_for('main.data_summary'))

        drugs = Drug.query.all()
        number_of_cases = form.number_of_cases.data
        min_price = form.min_price.data
        max_price = form.max_price.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        sellers = list(range(1, 10)) if form.seller.data else []
        origins = Country.query.all() if form.origin.data else []

        listings = []
        for i in range(number_of_cases):
            listing = generate_random_listing(drugs, market, min_price, max_price, start_date, end_date,
                                              sellers=sellers, origins=origins)
            listings.append(listing)
        db.session.add_all(listings)
        db.session.commit()

        return redirect(url_for('main.data_summary'))
    return render_template('create_mock_data.html', form=form, market_name=market.name)

@current_app.celery.task(bind=True)
def test_task(self, market_id):
    drugs = Drug.query.all()
    market = Market.query.filter_by(id=market_id).first()
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

@bp.route('/celery_test', methods=['GET', 'POST'])
def celery_test():
    return render_template('celery_test.html')

@bp.route('/testtask', methods=['POST'])
def testtask():
    market_id = 2 # TODO: replace with user input
    task = test_task(market_id=market_id)
    return jsonify({}), 202, {'Location': url_for('main.taskstatus', task_id=task.id)}

@bp.route('/status/<task_id>')
def taskstatus(task_id):
    task = test_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
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
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)