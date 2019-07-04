from flask import Blueprint

bp = Blueprint('scraping', __name__)

from app.scraping import routes, scraper