-- Migration: Add display_order to journey_images table
-- Purpose: Enable image reordering within journey steps
-- Date: 2025-11-10

-- Add display_order column (nullable initially)
ALTER TABLE journey_images ADD COLUMN display_order INTEGER;

-- Set default display_order based on created_at (chronological order)
UPDATE journey_images
SET display_order = subquery.row_num
FROM (
    SELECT id, 
           ROW_NUMBER() OVER (PARTITION BY step_id ORDER BY created_at) as row_num
    FROM journey_images
) AS subquery
WHERE journey_images.id = subquery.id;

-- Make display_order non-nullable now that all rows have values
ALTER TABLE journey_images ALTER COLUMN display_order SET NOT NULL;

-- Add index for efficient ordering queries
CREATE INDEX ix_journey_images_step_order ON journey_images(step_id, display_order);

-- Add comment
COMMENT ON COLUMN journey_images.display_order IS 'Display order of image within step (1-based)';

