# Multi-Floor Plan Detection System

## Overview

This system enables Gemini AI to detect and analyze floor plans that contain multiple floors in a single image (common for 3-story homes with basement, main floor, and second floor shown together).

## Files Created

### 1. **Jupyter Notebook Analysis**
- **Location**: `notebooks/05_multi_floor_plan_detection.ipynb`
- **Contents**:
  - Floor plan presentation types (single vs multi-floor)
  - Floor level identification guide (basement, main, second, third, attic)
  - Comprehensive Gemini prompt
  - Example JSON responses
  - Integration guide

### 2. **Gemini Prompt**
- **Location**: `prompts/multi_floor_detection_prompt.txt`
- **Purpose**: Ready-to-use prompt for Gemini Vision API
- **Features**:
  - Detects single vs multi-floor images
  - Identifies floor levels using labels and room types
  - Extracts separate room data for each floor
  - Returns structured JSON with floors array

## Floor Numbering System

| Floor Type | Floor Number | Common Labels |
|------------|--------------|---------------|
| Basement | 0 | BASEMENT, LOWER LEVEL, LL, BSMT |
| Main Floor | 1 | MAIN FLOOR, FIRST FLOOR, GROUND FLOOR |
| Second Floor | 2 | SECOND FLOOR, 2ND FLOOR, UPPER LEVEL |
| Third Floor | 3 | THIRD FLOOR, 3RD FLOOR |
| Attic | 99 | ATTIC, LOFT |

## Detection Strategy

### Multi-Floor Detection Clues
1. **Text Labels**: "BASEMENT", "MAIN FLOOR", "SECOND FLOOR" visible in image
2. **Layout Patterns**: Multiple distinct room layouts in same image
3. **Dividing Lines**: Horizontal or vertical lines separating floor sections
4. **Repeated Elements**: Stairs appearing in multiple sections
5. **Room Configurations**: Different room types in each section

### Floor Level Identification

#### Basement (Floor 0)
- **Primary Indicators**: Utility rooms, mechanical rooms, storage
- **Typical Rooms**: Recreation room, laundry, workshop, storage
- **Characteristics**: Fewer windows, lower ceilings, unfinished areas

#### Main Floor (Floor 1)
- **Primary Indicator**: Kitchen present
- **Typical Rooms**: Kitchen, living room, dining room, foyer, powder room
- **Characteristics**: Main entrance, public spaces, garage connection

#### Second Floor (Floor 2)
- **Primary Indicator**: Multiple bedrooms
- **Typical Rooms**: Bedrooms, master suite, bathrooms, closets
- **Characteristics**: Private spaces, hallway connecting rooms

#### Third Floor (Floor 3)
- **Primary Indicator**: Bonus rooms, additional bedrooms
- **Typical Rooms**: Bedrooms, loft, office, playroom
- **Characteristics**: Smaller footprint, sloped ceilings possible

#### Attic (Floor 99)
- **Primary Indicator**: Sloped ceilings, smallest footprint
- **Typical Rooms**: Storage, bonus room, office
- **Characteristics**: Angled ceilings, dormer windows

## JSON Output Structure

```json
{
  "floor_plan_type": "single_floor" | "multi_floor",
  "total_floors_detected": 3,
  "floors": [
    {
      "floor_number": 0,
      "floor_name": "Basement",
      "floor_type": "basement",
      "label_detected": "BASEMENT",
      "detection_confidence": 0.98,
      "detection_reasoning": "Clear label and utility rooms present",
      "detected_rooms": [...],
      "doors": [...],
      "windows": [...],
      "stairs": [...],
      "floor_analysis": {
        "total_area_sqft": 1200,
        "room_count": 4,
        "layout_type": "traditional",
        "ceiling_height_ft": 8
      }
    },
    {
      "floor_number": 1,
      "floor_name": "Main Floor",
      ...
    },
    {
      "floor_number": 2,
      "floor_name": "Second Floor",
      ...
    }
  ],
  "overall_analysis": {
    "total_area_all_floors_sqft": 4700,
    "total_rooms_all_floors": 17,
    "home_style": "three_story",
    "has_basement": true,
    "has_attic": false
  }
}
```

## Key Features

### 1. **Automatic Floor Detection**
- Analyzes image for multiple floor sections
- Identifies floor levels using labels and room types
- Handles both labeled and unlabeled floor plans

### 2. **Separate Room Extraction**
- Extracts room data for each floor independently
- Assigns rooms to correct floor_number
- Maintains spatial relationships within each floor

### 3. **Confidence Scoring**
- Overall confidence for multi-floor detection
- Per-floor detection confidence
- Per-room detection confidence

### 4. **Spatial Data**
- Position coordinates (x, y) for each room
- Bounding boxes for visualization
- Relative to each floor section

### 5. **Stair Tracking**
- Identifies stairs on each floor
- Notes which floors they connect
- Direction (up, down, both)

## Usage Example

### In FloorPlanAnalysisAgent

```python
# Load the prompt
with open('prompts/multi_floor_detection_prompt.txt', 'r') as f:
    prompt = f.read()

# Analyze floor plan
response = await gemini_client.analyze_image(
    image=floor_plan_image_path,
    prompt=prompt,
    temperature=0.3
)

# Parse response
data = json.loads(response)

# Check if multi-floor
if data['floor_plan_type'] == 'multi_floor':
    print(f"Detected {data['total_floors_detected']} floors")
    
    # Process each floor
    for floor in data['floors']:
        print(f"\nFloor {floor['floor_number']}: {floor['floor_name']}")
        print(f"  Rooms: {floor['floor_analysis']['room_count']}")
        print(f"  Area: {floor['floor_analysis']['total_area_sqft']} sqft")
        
        # Create Floor record
        floor_record = Floor(
            home_id=home_id,
            floor_number=floor['floor_number'],
            floor_name=floor['floor_name'],
            floor_type=floor['floor_type'],
            total_area=floor['floor_analysis']['total_area_sqft']
        )
        
        # Create Room records linked to this floor
        for room_data in floor['detected_rooms']:
            room = Room(
                home_id=home_id,
                floor_id=floor_record.id,
                floor_level=floor['floor_number'],
                room_type=room_data['room_type'],
                name=room_data['name'],
                area=room_data['dimensions']['area_sqft']
            )
```

## Integration Steps

### 1. Update FloorPlanAnalysisAgent
- Replace current prompt with multi-floor detection prompt
- Update response parsing to handle floors array
- Extract floor-level metadata

### 2. Update DigitalTwinService
- Create Floor records for each detected floor
- Link rooms to appropriate floor_id
- Store floor-specific analysis data

### 3. Update Database Schema
- Ensure Floor table exists with proper fields
- Add floor_id foreign key to rooms table
- Add floor_id to room_images table

### 4. Test with Multi-Floor Plans
- Upload 3-story floor plan images
- Verify correct floor detection
- Check room assignments to floors
- Validate floor_number values

## Benefits

### For Users
- Upload single image with all floors
- Automatic floor detection and separation
- Accurate room-to-floor assignment
- Better organization of multi-story homes

### For System
- Handles both single and multi-floor plans
- Robust floor level identification
- Structured data for each floor
- Enables floor-specific visualizations

### For Digital Twin
- Proper multi-floor representation
- Floor-by-floor navigation
- Accurate spatial relationships
- Support for isometric 3D views

## Edge Cases Handled

1. **Unlabeled Multi-Floor Plans**
   - Uses room types to infer floor levels
   - Kitchen → Main floor
   - Multiple bedrooms → Upper floor
   - Utility rooms → Basement

2. **Single Floor Plans**
   - Still works with single_floor type
   - Infers floor level from room types
   - Returns single floor in array

3. **Partial Floor Plans**
   - Handles basement-only plans
   - Handles upper-floors-only plans
   - Detects available floors only

4. **Split-Level Homes**
   - May require manual floor_level adjustment
   - Can detect multiple levels
   - Notes in detection_reasoning

## Next Steps

1. ✅ Create comprehensive prompt
2. ✅ Document floor detection strategy
3. ✅ Provide example responses
4. ⏳ Implement in FloorPlanAnalysisAgent
5. ⏳ Update DigitalTwinService
6. ⏳ Test with real multi-floor plans
7. ⏳ Refine based on results

## Related Files

- `notebooks/01_floor_plan_analysis.ipynb` - Floor plan data structure analysis
- `notebooks/02_image_tagging_analysis.ipynb` - Image-to-room matching
- `notebooks/03_comprehensive_schema_design.ipynb` - Database schema
- `notebooks/04_schema_summary_and_recommendations.ipynb` - Implementation roadmap
- `notebooks/05_multi_floor_plan_detection.ipynb` - This system's analysis
- `backend/agents/digital_twin/floor_plan_agent.py` - Current agent implementation
- `backend/services/digital_twin_service.py` - Service layer
- `backend/models/home.py` - Database models

## Support

For questions or issues with multi-floor detection:
1. Review the Jupyter notebook for detailed analysis
2. Check example responses in notebook
3. Verify prompt is being used correctly
4. Test with labeled floor plans first
5. Check confidence scores in response

