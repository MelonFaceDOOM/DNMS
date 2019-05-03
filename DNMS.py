from app import create_app, db
from app.models import User, Country, Drug, Rechem_listing, DN1_listing, DN2_listing

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 'User': User, 'Country': Country, 'Drug': Drug, 'Rechem_listing': Rechem_listing,
        'DN1_listing': DN1_listing, 'DN2_listing': DN2_listing
    }
