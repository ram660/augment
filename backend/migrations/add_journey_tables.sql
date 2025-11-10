-- Migration: Add journey tables for tracking user progress through home improvement projects
-- Date: 2025-11-10

-- Create journey status enum
CREATE TYPE journey_status AS ENUM (
    'not_started',
    'in_progress',
    'completed',
    'abandoned',
    'paused'
);

-- Create step status enum
CREATE TYPE step_status AS ENUM (
    'not_started',
    'in_progress',
    'completed',
    'skipped',
    'blocked',
    'needs_attention'
);

-- Create journeys table
CREATE TABLE IF NOT EXISTS journeys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    home_id UUID REFERENCES homes(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    
    -- Journey identification
    template_id VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Status
    status journey_status NOT NULL DEFAULT 'not_started',
    current_step_id VARCHAR(100),
    
    -- Progress tracking
    completed_steps INTEGER NOT NULL DEFAULT 0,
    total_steps INTEGER NOT NULL DEFAULT 0,
    progress_percentage FLOAT NOT NULL DEFAULT 0.0,
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    estimated_completion_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Metadata
    journey_metadata JSONB DEFAULT '{}',
    collected_data JSONB DEFAULT '{}'
);

-- Create journey_steps table
CREATE TABLE IF NOT EXISTS journey_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    
    -- Step identification
    step_id VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Step configuration
    required BOOLEAN NOT NULL DEFAULT TRUE,
    estimated_duration_minutes INTEGER NOT NULL DEFAULT 10,
    
    -- Dependencies
    depends_on JSONB DEFAULT '[]',
    required_actions JSONB DEFAULT '[]',
    
    -- Status
    status step_status NOT NULL DEFAULT 'not_started',
    progress_percentage FLOAT NOT NULL DEFAULT 0.0,
    
    -- Timestamps
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Data
    step_data JSONB DEFAULT '{}',
    sub_steps JSONB DEFAULT '[]'
);

-- Create journey_images table
CREATE TABLE IF NOT EXISTS journey_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journey_id UUID NOT NULL REFERENCES journeys(id) ON DELETE CASCADE,
    step_id UUID NOT NULL REFERENCES journey_steps(id) ON DELETE CASCADE,
    
    -- Image storage
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    
    -- File metadata
    content_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    
    -- Image type
    is_generated BOOLEAN NOT NULL DEFAULT FALSE,
    image_type VARCHAR(50),
    
    -- AI Analysis
    analysis JSONB DEFAULT '{}',
    
    -- User annotations
    label VARCHAR(255),
    notes TEXT,
    tags JSONB DEFAULT '[]',
    
    -- Relationships
    related_image_ids JSONB DEFAULT '[]',
    replaced_by_id UUID,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for journeys
CREATE INDEX IF NOT EXISTS idx_journeys_user_id ON journeys(user_id);
CREATE INDEX IF NOT EXISTS idx_journeys_home_id ON journeys(home_id);
CREATE INDEX IF NOT EXISTS idx_journeys_conversation_id ON journeys(conversation_id);
CREATE INDEX IF NOT EXISTS idx_journeys_status ON journeys(status);
CREATE INDEX IF NOT EXISTS idx_journeys_template_id ON journeys(template_id);
CREATE INDEX IF NOT EXISTS idx_journeys_user_status ON journeys(user_id, status);

-- Create indexes for journey_steps
CREATE INDEX IF NOT EXISTS idx_journey_steps_journey_id ON journey_steps(journey_id);
CREATE INDEX IF NOT EXISTS idx_journey_steps_status ON journey_steps(status);
CREATE INDEX IF NOT EXISTS idx_journey_steps_journey_number ON journey_steps(journey_id, step_number);

-- Create indexes for journey_images
CREATE INDEX IF NOT EXISTS idx_journey_images_journey_id ON journey_images(journey_id);
CREATE INDEX IF NOT EXISTS idx_journey_images_step_id ON journey_images(step_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_journeys_updated_at BEFORE UPDATE ON journeys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_journey_steps_updated_at BEFORE UPDATE ON journey_steps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_journey_images_updated_at BEFORE UPDATE ON journey_images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE journeys IS 'User journey instances tracking progress through home improvement projects';
COMMENT ON TABLE journey_steps IS 'Individual steps in a journey with state and data';
COMMENT ON TABLE journey_images IS 'Images attached to journey steps with AI analysis and annotations';

COMMENT ON COLUMN journeys.template_id IS 'Journey template ID (e.g., kitchen_renovation, diy_project)';
COMMENT ON COLUMN journeys.collected_data IS 'Aggregated data from all steps (images, decisions, budget, etc.)';
COMMENT ON COLUMN journey_steps.depends_on IS 'Array of step_ids that must be completed first';
COMMENT ON COLUMN journey_steps.required_actions IS 'Array of actions required to complete step';
COMMENT ON COLUMN journey_images.analysis IS 'AI analysis results (materials, fixtures, style, condition)';
COMMENT ON COLUMN journey_images.related_image_ids IS 'Array of related image IDs (before/after pairs)';

