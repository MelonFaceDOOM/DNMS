from flask_login import login_required
from app import db
from app.models import Country, Drug, Listing, Market, Page
from app.main import bp
import ast
import sqlite3
import pandas as pd
import mock_data

@bp.route('/seed_database/', methods=['GET', 'POST'])
@login_required
def seed_database():
    drugs = []
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


@bp.route('/import_rechem_data/', methods=['GET', 'POST'])
@login_required
def import_rechem_data():
    c = sqlite3.connect('rechem_listings.db')
    with open('rechem_drug_titles', 'r') as f:
        s = f.read()
        drug_title_dict = ast.literal_eval(s)

    rechem_pages = pd.read_sql_query("SELECT * FROM Listings", c)
    rechem_listings = pd.read_sql_query("SELECT * FROM Listing_index", c)

    for i, row in rechem_listings.iterrows():
        rechem_listings.loc[i, 'drug'] = drug_title_dict[row['title']]

    m = Market(name="rechem_real")
    db.session.add(m)
    db.session.commit()
    print("market added")

    listings = []
    for i, row in rechem_listings.iterrows():
        drug = Drug.query.filter_by(name=row['drug']).first()
        if not drug:
            db.session.add(Drug(name=row['drug']))
            db.session.commit()
        listings.append(Listing(url=row['url'], market=m, drug=drug))

    db.session.add_all(listings)
    db.session.commit()
    print("Listings added")

    pages = []
    for i, row in rechem_pages.iterrows():
        listing = rechem_listings[rechem_listings['id'] == row['listing_index_id']]
        listing_drug = listing['drug'].item()
        listing_name = listing['title'].item()
        listing = Listing.query.filter_by(name=listing_drug).first()
        pages.append(Page(html=row['page_text'], timestamp=row['scraped_time'], name=listing_name, listing=listing))

    db.session.add_all(pages)
    db.session.commit()
    print("Pages added")