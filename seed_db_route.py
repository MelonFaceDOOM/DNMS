from flask_login import login_required
from app import db
from app.models import Country, Drug, Listing, Market
from app.main import bp
from datetime import datetime
import mock_data
@bp.route('/seed_database/', methods=['GET', 'POST'])
@login_required
def seed_database():
    drugs = []
    for d in mock_data.drugs:
        q = Drug.query.filter_by(name=drugs).first()
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


    rechem_listings = mock_data.gen_rechem_listings()
    dn1_listings = mock_data.gen_dn1_listings()
    dn2_listings = mock_data.gen_dn2_listings()

    listings = []
    market = Market.query.filter_by(name="Rechem").first()
    for l in rechem_listings[1:]:
        name = l[0]
        drug = Drug.query.filter_by(name=name).first()
        price = l[1]
        date = l[2].astype(datetime)
        listing = Listing(drug=drug, price=price, date=date, market=market)
        listings.append(listing)
    db.session.add_all(listings)
    db.session.commit()

    listings = []
    market = Market.query.filter_by(name="DN1").first()
    for l in dn1_listings[1:]:
        name = l[0]
        drug = Drug.query.filter_by(name=name).first()
        price = l[1]
        date = l[2].astype(datetime)
        seller = l[3]
        origin = Country.query.filter_by(name=l[4]).first()
        listing = Listing(drug=drug, price=price, date=date, seller=seller, origin_id=origin.id, market=market)
        listings.append(listing)
    db.session.add_all(listings)
    db.session.commit()

    listings = []
    market = Market.query.filter_by(name="DN2").first()
    for l in dn2_listings[1:]:
        name = l[0]
        drug = Drug.query.filter_by(name=name).first()
        price = l[1]
        date = l[2].astype(datetime)
        seller = l[3]
        origin = Country.query.filter_by(name=l[4]).first()
        listing = Listing(drug=drug, price=price, date=date, seller=seller, origin_id=origin.id, market=market)
        listings.append(listing)
    db.session.add_all(listings)
    db.session.commit()

    return ('', 204)