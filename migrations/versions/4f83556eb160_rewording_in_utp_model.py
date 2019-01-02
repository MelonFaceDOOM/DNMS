"""rewording in utp model

Revision ID: 4f83556eb160
Revises: ab8fc3c1c701
Create Date: 2018-12-21 15:26:07.090614

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f83556eb160'
down_revision = 'ab8fc3c1c701'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user__thread__position', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_post_viewed', sa.Integer(), nullable=True))
        batch_op.drop_column('last_post_read')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user__thread__position', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_post_read', sa.INTEGER(), nullable=True))
        batch_op.drop_column('last_post_viewed')

    # ### end Alembic commands ###