"""Add transformation models

Revision ID: 003
Revises: 002
Create Date: 2025-01-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create transformation_type enum
    transformation_type_enum = postgresql.ENUM(
        'paint', 'flooring', 'cabinets', 'countertops', 'backsplash', 
        'lighting', 'furniture', 'multi',
        name='transformationtype'
    )
    transformation_type_enum.create(op.get_bind())
    
    # Create transformation_status enum
    transformation_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed', 'cancelled',
        name='transformationstatus'
    )
    transformation_status_enum.create(op.get_bind())
    
    # Create transformations table
    op.create_table(
        'transformations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_image_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('room_images.id'), nullable=False),
        sa.Column('transformation_type', transformation_type_enum, nullable=False),
        sa.Column('status', transformation_status_enum, nullable=False),
        sa.Column('parameters', postgresql.JSON, nullable=False),
        sa.Column('num_variations', sa.Integer, default=4, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_message', sa.String, nullable=True),
        sa.Column('processing_time_seconds', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_transformations_room_image_id', 'transformations', ['room_image_id'])
    op.create_index('ix_transformations_user_id', 'transformations', ['user_id'])
    op.create_index('ix_transformations_status', 'transformations', ['status'])
    op.create_index('ix_transformations_type', 'transformations', ['transformation_type'])
    
    # Create transformation_images table
    op.create_table(
        'transformation_images',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('transformation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transformations.id'), nullable=False),
        sa.Column('image_url', sa.String, nullable=False),
        sa.Column('variation_number', sa.Integer, nullable=False),
        sa.Column('is_selected', sa.Boolean, default=False),
        sa.Column('is_applied', sa.Boolean, default=False),
        sa.Column('width', sa.Integer, nullable=True),
        sa.Column('height', sa.Integer, nullable=True),
        sa.Column('file_size_bytes', sa.Integer, nullable=True),
        sa.Column('quality_score', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_transformation_images_transformation_id', 'transformation_images', ['transformation_id'])
    op.create_index('ix_transformation_images_is_selected', 'transformation_images', ['is_selected'])
    
    # Create transformation_feedback table
    op.create_table(
        'transformation_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('transformation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transformations.id'), nullable=False),
        sa.Column('transformation_image_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transformation_images.id'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('accuracy_score', sa.Integer, nullable=True),
        sa.Column('preservation_score', sa.Integer, nullable=True),
        sa.Column('realism_score', sa.Integer, nullable=True),
        sa.Column('comment', sa.String, nullable=True),
        sa.Column('changed_wrong_elements', sa.Boolean, default=False),
        sa.Column('unrealistic_result', sa.Boolean, default=False),
        sa.Column('poor_quality', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_transformation_feedback_transformation_id', 'transformation_feedback', ['transformation_id'])
    op.create_index('ix_transformation_feedback_rating', 'transformation_feedback', ['rating'])
    
    # Create transformation_templates table
    op.create_table(
        'transformation_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.String, nullable=True),
        sa.Column('applicable_room_types', postgresql.JSON, nullable=False),
        sa.Column('transformation_steps', postgresql.JSON, nullable=False),
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('average_rating', sa.Integer, nullable=True),
        sa.Column('is_public', sa.Boolean, default=True),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_transformation_templates_is_public', 'transformation_templates', ['is_public'])
    op.create_index('ix_transformation_templates_is_featured', 'transformation_templates', ['is_featured'])


def downgrade():
    # Drop tables
    op.drop_table('transformation_templates')
    op.drop_table('transformation_feedback')
    op.drop_table('transformation_images')
    op.drop_table('transformations')
    
    # Drop enums
    op.execute('DROP TYPE transformationstatus')
    op.execute('DROP TYPE transformationtype')

