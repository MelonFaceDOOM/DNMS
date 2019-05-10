from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, current_app, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import User, Country, Drug, Listing, Market
from app.main import bp
from app.main.forms import (EditProfileForm, SearchForm)
from app.main.graphs import create_plot
import mock_data

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()


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
    bar = create_plot(dates,prices)
    if drug is None or market is None:
        title = "N/A"
    else:
        title = "{} - {}".format(market.name, drug.name)
    return render_template('drug.html', plot=bar, title=title)

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




# disabled to avoid accidentally create more data
# # todo - modify to make an actual page with controls and stuff to allow the user to generate data if they wish
# @bp.route('/create_mock_data')
# @login_required
# def create_mock_data():
#
#     drugs = []
#     for d in mock_data.drugs:
#         q = Drug.query.filter_by(name=d).first()
#         if q is None:
#             drug = Drug(name=d)
#             drugs.append(drug)
#     db.session.add_all(drugs)
#     db.session.commit()
#
#     countries = []
#     for c in mock_data.all_countries:
#         q = Country.query.filter_by(name=c[0]).first()
#         if q is None:
#             country = Country(name=c[0], c2=c[1])
#             countries.append(country)
#     db.session.add_all(countries)
#     db.session.commit()
#
#     ms = ["Rechem", "DN1", "DN2"]
#     markets = []
#     for m in ms:
#         q = Market.query.filter_by(name=m).first()
#         if q is None:
#             market = Market(name=m)
#             markets.append(market)
#     db.session.add_all(markets)
#     db.session.commit()
#
#     rechem_listings = mock_data.gen_rechem_listings()
#     dn1_listings = mock_data.gen_dn1_listings()
#     dn2_listings = mock_data.gen_dn2_listings()
#
#     listings = []
#     market = Market.query.filter_by(name="Rechem").first()
#     for l in rechem_listings[1:]:
#         name = l[0]
#         drug = Drug.query.filter_by(name=name).first()
#         price = l[1]
#         date = l[2].astype(datetime)
#         listing = Listing(drug=drug, price=price, date=date, market=market)
#         listings.append(listing)
#     db.session.add_all(listings)
#     db.session.commit()
#
#     listings = []
#     market = Market.query.filter_by(name="DN1").first()
#     for l in dn1_listings[1:]:
#         name = l[0]
#         drug = Drug.query.filter_by(name=name).first()
#         price = l[1]
#         date = l[2].astype(datetime)
#         seller = l[3]
#         origin = Country.query.filter_by(name=l[4]).first()
#         listing = Listing(drug=drug, price=price, date=date, seller=seller, origin_id=origin.id, market=market)
#         listings.append(listing)
#     db.session.add_all(listings)
#     db.session.commit()
#
#     listings = []
#     market = Market.query.filter_by(name="DN2").first()
#     for l in dn2_listings[1:]:
#         name = l[0]
#         drug = Drug.query.filter_by(name=name).first()
#         price = l[1]
#         date = l[2].astype(datetime)
#         seller = l[3]
#         origin = Country.query.filter_by(name=l[4]).first()
#         listing = Listing(drug=drug, price=price, date=date, seller=seller, origin_id=origin.id, market=market)
#         listings.append(listing)
#     db.session.add_all(listings)
#     db.session.commit()
#
#     return ('', 204)