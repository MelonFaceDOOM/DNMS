from hashlib import md5
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
from app.search import add_to_index, remove_from_index, query_index
from sqlalchemy.orm import validates
import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    c2 = db.Column(db.String(128), index=True)
    __table_args__ = (db.UniqueConstraint('name'),
                      )

    @validates('c2')
    def validate_c2(self, key, c2) -> str:  # todo - confirm purpose of 'key'
        if len(c2) != 2:
            raise ValueError('c2 must be two characters')
        return c2

    def drugs(self):
        DN1 = DN1_listing.query.filter_by(origin_id=self.id).all()
        DN2 = DN2_listing.query.filter_by(origin_id=self.id).all()

        return DN1 + DN2

class Drug(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    rechem_listings = db.relationship('Rechem_listing', backref='drug', lazy='dynamic')
    DN1_listings = db.relationship('DN1_listing', backref='drug', lazy='dynamic')
    DN2_listings = db.relationship('DN2_listing', backref='drug', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('name'),
                      )


class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    rechem_listings = db.relationship('Rechem_listing', backref='market', lazy='dynamic')
    dn1_listings = db.relationship('DN1_listing', backref='market', lazy='dynamic')
    dn2_listings = db.relationship('DN2_listing', backref='market', lazy='dynamic')


class Rechem_listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.String(128), db.ForeignKey('market.id'))
    drug_id = db.Column(db.Integer, db.ForeignKey('drug.id'))
    price = db.Column(db.Float)
    date = db.Column(db.DateTime, index=True)
    date_entered = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)


class DN1_listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.String(128), db.ForeignKey('market.id'))
    drug_id = db.Column(db.Integer, db.ForeignKey('drug.id'))
    price = db.Column(db.Float)
    date = db.Column(db.DateTime, index=True)
    seller = db.Column(db.String(128), index=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    date_entered = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)


class DN2_listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.String(128), db.ForeignKey('market.id'))
    drug_id = db.Column(db.Integer, db.ForeignKey('drug.id'))
    price = db.Column(db.Float)
    date = db.Column(db.DateTime, index=True)
    seller = db.Column(db.String(128), index=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    date_entered = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
