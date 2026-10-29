"""Add source_url, author, distributions columns to workflow_cost_evidence table."""

from alembic import op
import sqlalchemy as sa


revision = "093_add_source_url_to_workflow_cost_evidence"
down_revision = "092_workflow_cost_evidence"
branch_labels = None
depends_on = None


def upgrade():
    # Add source_url column
    op.add_column('workflow_cost_evidence', sa.Column('source_url', sa.String(512), nullable=True))
    
    # Add author column
    op.add_column('workflow_cost_evidence', sa.Column('author', sa.String(80), nullable=True))
    
    # Add distributions column
    op.add_column('workflow_cost_evidence', sa.Column('distributions', sa.JSONB(), nullable=True))


def downgrade():
    # Remove columns in reverse order
    op.drop_column('workflow_cost_evidence', 'distributions')
    op.drop_column('workflow_cost_evidence', 'author')
    op.drop_column('workflow_cost_evidence', 'source_url')
