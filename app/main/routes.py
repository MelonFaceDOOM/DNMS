from flask import render_template, flash, redirect, url_for, request, g, current_app, jsonify, send_from_directory
from flask_login import current_user, login_required
from app import db
from app.models import User, Drug, Listing, Market
from app.main import bp
from app.main.forms import EditProfileForm, SearchForm
from app.main.graphs import create_plot
import os


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()


@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@bp.route('/')
@bp.route('/index')
@bp.route('/data_summary')
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
def drugs():
    drugs = Drug.query.all()
    markets = Market.query.all()
    return render_template('drugs.html', drugs=drugs, markets=markets, title="Drugs")

@bp.route('/drug')
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
    return '', 204

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