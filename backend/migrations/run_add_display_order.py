"""
Run migration to add display_order column to journey_images table.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Run the display_order migration."""

    # Create async engine
    engine = create_async_engine("sqlite+aiosqlite:///./homevision.db", echo=False)

    async with engine.begin() as conn:
        logger.info("Starting migration: add display_order to journey_images")
        
        # Check if column already exists
        result = await conn.execute(text("PRAGMA table_info(journey_images)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'display_order' in columns:
            logger.info("Column display_order already exists, skipping migration")
            return
        
        # Add display_order column (nullable initially)
        logger.info("Adding display_order column...")
        await conn.execute(text(
            "ALTER TABLE journey_images ADD COLUMN display_order INTEGER"
        ))
        
        # Set default display_order based on created_at (chronological order)
        logger.info("Setting default display_order values...")
        await conn.execute(text("""
            UPDATE journey_images
            SET display_order = (
                SELECT COUNT(*) + 1
                FROM journey_images AS ji2
                WHERE ji2.step_id = journey_images.step_id
                AND ji2.created_at < journey_images.created_at
            )
        """))
        
        # Set display_order to 1 for any NULL values (shouldn't happen but just in case)
        await conn.execute(text("""
            UPDATE journey_images
            SET display_order = 1
            WHERE display_order IS NULL
        """))
        
        # Note: SQLite doesn't support ALTER COLUMN to add NOT NULL constraint
        # The model will enforce NOT NULL for new records
        
        # Create index for efficient ordering queries
        logger.info("Creating index...")
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_journey_images_step_order "
            "ON journey_images(step_id, display_order)"
        ))
        
        logger.info("Migration completed successfully!")

    # Close engine
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())

