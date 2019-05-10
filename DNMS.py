from app import create_app, db
from app.models import User, Country, Drug, Listing, Market

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 'User': User, 'Country': Country, 'Drug': Drug, 'Listing': Listing, 'Market': Market
    }
