"""empty message

Revision ID: 7d9cf9d4337c
Revises: 11597b0662d3
Create Date: 2019-04-11 13:08:11.570425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d9cf9d4337c'
down_revision = '11597b0662d3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_report_sticker_set_name'), 'report', ['sticker_set_name'], unique=False)
    op.create_index(op.f('ix_report_user_id'), 'report', ['user_id'], unique=False)
    op.drop_index('ix_vote_ban_sticker_set_name', table_name='report')
    op.drop_index('ix_vote_ban_user_id', table_name='report')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_vote_ban_user_id', 'report', ['user_id'], unique=False)
    op.create_index('ix_vote_ban_sticker_set_name', 'report', ['sticker_set_name'], unique=False)
    op.drop_index(op.f('ix_report_user_id'), table_name='report')
    op.drop_index(op.f('ix_report_sticker_set_name'), table_name='report')
    # ### end Alembic commands ###