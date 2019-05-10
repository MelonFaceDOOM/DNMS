"""first

Revision ID: d091994ae7eb
Revises: 
Create Date: 2019-05-09 17:00:48.921822

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd091994ae7eb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('country',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('c2', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_country_c2'), 'country', ['c2'], unique=False)
    op.create_index(op.f('ix_country_name'), 'country', ['name'], unique=False)
    op.create_table('drug',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_drug_name'), 'drug', ['name'], unique=False)
    op.create_table('market',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_market_name'), 'market', ['name'], unique=False)
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('listing',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('market_id', sa.String(length=128), nullable=True),
    sa.Column('drug_id', sa.Integer(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('seller', sa.String(length=128), nullable=True),
    sa.Column('origin_id', sa.Integer(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('date_entered', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['drug_id'], ['drug.id'], ),
    sa.ForeignKeyConstraint(['market_id'], ['market.id'], ),
    sa.ForeignKeyConstraint(['origin_id'], ['country.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_listing_date'), 'listing', ['date'], unique=False)
    op.create_index(op.f('ix_listing_date_entered'), 'listing', ['date_entered'], unique=False)
    op.create_index(op.f('ix_listing_seller'), 'listing', ['seller'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_listing_seller'), table_name='listing')
    op.drop_index(op.f('ix_listing_date_entered'), table_name='listing')
    op.drop_index(op.f('ix_listing_date'), table_name='listing')
    op.drop_table('listing')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_market_name'), table_name='market')
    op.drop_table('market')
    op.drop_index(op.f('ix_drug_name'), table_name='drug')
    op.drop_table('drug')
    op.drop_index(op.f('ix_country_name'), table_name='country')
    op.drop_index(op.f('ix_country_c2'), table_name='country')
    op.drop_table('country')
    # ### end Alembic commands ###
