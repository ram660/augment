# 🎯 HomeVision Studio - Universal Prompt Engineering Guide

## Overview
This comprehensive guide provides prompt structures, patterns, and instructions for handling ALL home improvement scenarios across any room type, design style, and transformation category. This is the foundation for the universal HomeVision Studio system.

---

## Table of Contents
1. [Core Prompt Structure](#core-prompt-structure)
2. [Room Types & Configurations](#room-types--configurations)
3. [Transformation Categories](#transformation-categories)
   - [Paint & Wall Treatments](#paint--wall-treatments)
   - [Flooring Systems](#flooring-systems)
   - [Cabinetry & Built-ins](#cabinetry--built-ins)
   - [Furniture & Fixtures](#furniture--fixtures)
   - [Lighting & Atmosphere](#lighting--atmosphere)
   - [Color Schemes & Palettes](#color-schemes--palettes)
   - [Architectural Elements](#architectural-elements)
   - [Outdoor & Exteriors](#outdoor--exteriors)
4. [Design Styles Library](#design-styles-library)
5. [Advanced Multi-Element Transformations](#advanced-multi-element-transformations)
6. [Prompt Patterns & Best Practices](#prompt-patterns--best-practices)
7. [Universal Prompt Template Engine](#universal-prompt-template-engine)
8. [Quality Control & Validation](#quality-control--validation)

---

## Core Prompt Structure

### General Pattern
All successful prompts follow this structure:

```
TASK: [Clear, specific action to perform]

CRITICAL REQUIREMENTS:
1. [Primary transformation specification]
2. [Detail requirements]
3. [Preservation requirements - what NOT to change]
4. [Quality requirements]
5. [Additional constraints]

OUTPUT: [Exact format expected]
```

### Key Components
- **Task Declaration**: Single sentence describing the goal
- **Critical Requirements**: Numbered, specific instructions
- **Preservation Rules**: Explicit instructions on what to keep unchanged
- **Quality Standards**: Photorealism, lighting, edge quality
- **Output Specification**: Clear expectation of result format

---

## Paint Color Prompts

### Structure from `02_paint_color_testing.ipynb`

```python
prompt = f"""TASK: Repaint the walls of this room.

CRITICAL REQUIREMENTS:
1. **Wall Color**: Apply '{color_name} ({color_code})' to ALL wall surfaces. 
   The color is a {color_description}.
2. **Finish**: The paint finish should be '{finish_type}'.
3. **Preserve**: Do NOT change the floor, ceiling, furniture, windows, doors, 
   or any other objects. Only the wall color should change.
4. **Quality**: The result must be photorealistic. Maintain all original shadows, 
   lighting, and textures on the walls. Edges must be clean.

OUTPUT: Return only the image of the room with the new wall color."""
```

### Key Elements
- **Specificity**: Exact color name and code
- **Scope**: "ALL wall surfaces"
- **Finish Type**: Matte, Eggshell, Satin, Semi-Gloss
- **Preservation**: Comprehensive list of elements to preserve
- **Quality**: Photorealism + shadows + lighting + textures

### Variables Used
- `{color_name}`: e.g., "Naval", "Agreeable Gray"
- `{color_code}`: e.g., "SW 6244", "HC-172"
- `{color_description}`: e.g., "Deep navy blue", "Warm greige"
- `{finish_type}`: e.g., "Eggshell", "Semi-Gloss"

### Variations Tested
1. **Different Colors**: Navy, Gray, White, Charcoal
2. **Different Finishes**: Matte, Eggshell, Satin, Semi-Gloss
3. **Different Brands**: Sherwin-Williams, Benjamin Moore, Behr

---

## Flooring Replacement Prompts

### Structure from `04_flooring_replacement.ipynb`

```python
prompt = f"""TASK: Replace the flooring in this room.

CRITICAL REQUIREMENTS:
1. **Flooring Type**: Install new flooring: {flooring_name}.
2. **Description**: The new flooring is {flooring_description}.
3. **Pattern**: The pattern should be {flooring_pattern}.
4. **Preserve**: Do NOT change the walls, ceiling, furniture, windows, or doors. 
   Only the floor should change.
5. **Quality**: The result must be photorealistic. The new floor must have correct 
   perspective, lighting, and shadows. Edges must be clean where the floor meets 
   the walls and other objects.

OUTPUT: Return only the image of the room with the new flooring."""
```

### Key Elements
- **Material Specification**: Type and description
- **Pattern Details**: Plank width, tile size, layout
- **Perspective**: Floor must follow room geometry
- **Edge Treatment**: Clean transitions to walls/furniture
- **Lighting Integration**: Reflections and shadows

### Variables Used
- `{flooring_name}`: e.g., "Natural Oak Hardwood", "Carrara Marble Tile"
- `{flooring_description}`: Detailed texture and color
- `{flooring_pattern}`: e.g., "3-inch wide planks", "12x24 inch tiles in brick pattern"

### Material Types Tested
1. **Hardwood**: Oak (light), Walnut (dark)
2. **Tile**: Marble, Porcelain
3. **Carpet**: Plush, Neutral
4. **Luxury Vinyl**: Wood-look planks

---

## Cabinet/Furniture Prompts

### Structure from `05_cabinet_furniture_replacement.ipynb`

```python
prompt = f"""TASK: Replace the kitchen cabinets in this image.

CRITICAL REQUIREMENTS:
1. **Cabinet Style**: Replace all existing kitchen cabinets (both upper and lower) 
   with '{cabinet_name}'.
2. **Description**: The new cabinets are {cabinet_description}.
3. **Hardware**: The hardware should be {cabinet_hardware}.
4. **Preserve**: Do NOT change the walls, floor, ceiling, countertops, backsplash, 
   appliances, or windows. Only the cabinets should be replaced.
5. **Quality**: The result must be photorealistic, with clean edges and natural 
   lighting. The new cabinets must look professionally installed.

OUTPUT: Return only the image of the kitchen with the new cabinets."""
```

### Key Elements
- **Complete Replacement**: Both upper and lower cabinets
- **Style Specification**: Shaker, Flat-panel, Traditional
- **Hardware Details**: Knobs, pulls, finish
- **Professional Installation**: Clean edges, proper alignment
- **Context Preservation**: Counters, appliances, backsplash unchanged

### Variables Used
- `{cabinet_name}`: e.g., "White Shaker Cabinets", "Navy Blue Shaker Cabinets"
- `{cabinet_description}`: Full style and color details
- `{cabinet_hardware}`: e.g., "brushed nickel knobs", "brass bar pulls"
- `{cabinet_finish}`: e.g., "painted matte", "semi-gloss"

### Cabinet Styles Tested
1. **Shaker**: White, Navy, Gray
2. **Flat-Panel/Slab**: Modern, minimalist
3. **Traditional**: Raised panel, ornate

---

## Lighting Scenario Prompts

### Structure from `06_lighting_scenarios.ipynb`

```python
prompt = f"""TASK: Change the lighting of this room.

CRITICAL REQUIREMENTS:
1. **Lighting Scenario**: Apply '{lighting_name}'.
2. **Description**: The lighting should be {lighting_description}.
3. **Preserve**: Do NOT change any objects, furniture, colors, or textures in the room. 
   Only the lighting, shadows, and overall color temperature should change.
4. **Quality**: The result must be photorealistic and physically accurate.

OUTPUT: Return only the image of the room with the new lighting."""
```

### Key Elements
- **Lighting Type**: Natural vs Artificial
- **Time of Day**: Morning, Midday, Evening, Night
- **Color Temperature**: Warm (2700K) to Cool (6500K)
- **Shadow Behavior**: Soft, crisp, multiple sources
- **Intensity**: Bright, moderate, dim

### Variables Used
- `{lighting_name}`: e.g., "Bright Natural Daylight", "Warm Evening"
- `{lighting_description}`: Full atmospheric description
- `{lighting_time}`: Time of day context
- `{color_temperature}`: Kelvin temperature specification
- `{shadow_type}`: Shadow characteristics

### Lighting Scenarios Tested
1. **Bright Daylight**: 5500K, crisp shadows
2. **Golden Hour**: 3500K, warm, soft shadows
3. **Warm Evening**: 2700K, multiple sources
4. **Cool Overcast**: 6500K, diffused, soft shadows

---

## Color Scheme Prompts

### Structure from `07_color_scheme_testing.ipynb`

```python
prompt = f"""TASK: Apply a new color scheme to this room.

CRITICAL REQUIREMENTS:
1. **Scheme Name**: '{scheme_name}'.
2. **Wall Color**: Repaint the walls to be {wall_color_specification}.
3. **Accent Colors**: Introduce accent colors like {accent_color_list} through 
   small decor items like pillows, throws, or vases.
4. **Mood**: The overall mood should be {target_mood}.
5. **Preserve**: Keep the main furniture, flooring, and room architecture the same 
   unless it clashes heavily with the new scheme.
6. **Quality**: Photorealistic result with natural integration of colors.

OUTPUT: Return only the image of the room with the new color scheme."""
```

### Key Elements
- **Coordinated Palette**: Wall + accent colors
- **Mood Creation**: Specific atmosphere target
- **Subtle Integration**: Accents via decor, not major changes
- **Architecture Preservation**: Structure remains intact
- **Natural Color Integration**: Realistic color relationships

### Variables Used
- `{scheme_name}`: e.g., "Coastal Calm", "Modern Monochrome"
- `{wall_color_specification}`: Full color description
- `{accent_color_list}`: Array of complementary colors
- `{target_mood}`: e.g., "relaxing, breezy", "dramatic, modern"

### Color Schemes Tested
1. **Coastal Calm**: Blue-green + sandy beige + coral
2. **Modern Monochrome**: White + black + charcoal + brass
3. **Earthy Warmth**: Beige + terracotta + olive + brown

---

## Advanced Multi-Element Prompts

### Structure from `08_advanced_transformations.ipynb`

```python
prompt = f"""TASK: Complete kitchen transformation with coordinated design elements.

CRITICAL REQUIREMENTS:
1. WALL TRANSFORMATION:
   - Paint ALL walls: {wall_color}
   - Color: {wall_description}
   - Finish: {wall_finish}

2. FLOORING TRANSFORMATION:
   - Replace floor: {floor_description}
   - Material: {floor_material}
   - Pattern: {floor_pattern}

3. CABINET TRANSFORMATION:
   - Replace ALL cabinets (upper and lower)
   - Style: {cabinet_style}
   - Color: {cabinet_color}
   - Hardware: {cabinet_hardware}
   - Finish: {cabinet_finish}
   - Cabinets MUST be clearly this color and style

4. DESIGN COORDINATION:
   - Style: {overall_style}
   - Overall look: {design_description}
   - Mood: {target_mood}
   - All elements must work together harmoniously

5. PRESERVE:
   - Countertops: EXACT same
   - Appliances: EXACT same
   - Backsplash: EXACT same
   - Windows: EXACT same
   - Fixtures/hardware only on cabinets changes
   - Room layout: EXACT same

6. QUALITY:
   - Photorealistic kitchen design
   - Professional cabinet installation look
   - Natural lighting and shadows
   - Clean edges and corners
   - No AI artifacts
   - Sharp detail throughout

7. LIGHTING (Optional):
   - Apply lighting: {lighting_description}
   - Time: {lighting_time}
   - Temperature: {color_temperature}
   - Intensity: {intensity_level}
   - Shadows: {shadow_type}

OUTPUT: Return the kitchen with ALL THREE elements transformed (walls + floor + cabinets)."""
```

### Key Elements
- **Multi-Element Coordination**: 3+ simultaneous changes
- **Hierarchical Structure**: Numbered sections for clarity
- **Explicit Preservation**: Detailed list of unchangeable elements
- **Design Cohesion**: Style consistency requirements
- **Optional Lighting**: Conditional section for lighting overlay

### Advanced Patterns
1. **Complete Kitchen**: Walls + Floors + Cabinets
2. **Lighting Variations**: Same design, different times of day
3. **Seasonal Palettes**: Summer bright vs Winter cozy
4. **Room-Specific**: Kitchen, Living Room, Bedroom optimizations

---

## Seasonal Palette Prompts

### Structure from `08_advanced_transformations.ipynb`

```python
prompt = f"""TASK: Transform this room with a {season} color palette.

CRITICAL REQUIREMENTS:
1. SEASONAL PALETTE:
   - Season: {season}
   - Description: {seasonal_description}
   - Target mood: {seasonal_mood}

2. WALLS:
   - Color: {wall_color}
   - Description: {wall_description}
   - Finish: {wall_finish}

3. FLOORING:
   - Material: {floor_material}
   - Description: {floor_description}
   - Pattern: {floor_pattern}

4. SEASONAL FEELING:
   - Colors must evoke {season} feeling
   - Accent colors reflect: {seasonal_accent_colors}
   - Overall atmosphere: {seasonal_mood}

5. PRESERVE:
   - Furniture: EXACT same
   - Architecture: EXACT same
   - Windows: EXACT same
   - Only walls and floors change

6. QUALITY:
   - Photorealistic
   - Natural lighting
   - No artifacts
   - Professional finish

OUTPUT: Return room with {season} palette applied."""
```

### Seasonal Variations
- **Summer**: Bright, airy, blue-green, coral, yellow
- **Winter**: Warm, cozy, taupe-gray, burgundy, forest green

---

## Prompt Patterns & Best Practices

### 1. **Directive Language**
- ✅ "Paint ALL walls"
- ✅ "Replace ALL cabinets"
- ✅ "MUST remain EXACT same"
- ❌ "Try to paint walls"
- ❌ "Ideally change cabinets"

### 2. **Explicit Scope**
- ✅ "Both upper and lower cabinets"
- ✅ "ALL wall surfaces visible"
- ✅ "Every floor tile"
- ❌ "Change cabinets"
- ❌ "Update walls"

### 3. **Preservation Clarity**
- ✅ Specific list: "Countertops, appliances, backsplash, windows"
- ✅ "Do NOT change X, Y, Z"
- ✅ "Only [element] should change"
- ❌ "Keep other things the same"
- ❌ "Don't change too much"

### 4. **Quality Requirements**
- ✅ "Photorealistic"
- ✅ "Professional installation look"
- ✅ "Clean edges and corners"
- ✅ "Natural lighting and shadows"
- ✅ "No AI artifacts"

### 5. **Technical Specifications**
- ✅ Include color codes: "SW 6244", "HC-172"
- ✅ Include materials: "3-inch oak planks", "12x24 marble tiles"
- ✅ Include finishes: "Eggshell", "Semi-gloss"
- ✅ Include color temperature: "2700K", "5500K"

### 6. **Output Specification**
- ✅ "Return only the image of..."
- ✅ Clear expectation of what the output should be
- ✅ Single, focused result

### 7. **Hierarchical Organization**
- ✅ Use numbered sections (1, 2, 3...)
- ✅ Use sub-bullets for details
- ✅ Group related requirements
- ✅ Separate transformation from preservation

---

## Universal Prompt Template

### Base Template Structure

```python
def generate_universal_prompt(
    task_type: str,  # 'paint', 'flooring', 'cabinets', 'lighting', 'complete'
    room_type: str,  # 'kitchen', 'living_room', 'bedroom', 'bathroom'
    transformations: dict,  # Specific transformation parameters
    preservation: list,  # Elements to preserve
    style: str,  # 'modern', 'traditional', 'scandinavian', etc.
    quality_level: str = 'photorealistic'
):
    """
    Universal prompt generator for all room transformations.
    
    transformations = {
        'walls': {'color': '...', 'finish': '...'},
        'flooring': {'material': '...', 'pattern': '...'},
        'cabinets': {'style': '...', 'color': '...', 'hardware': '...'},
        'lighting': {'scenario': '...', 'temperature': '...'}
    }
    """
    
    # Build prompt sections dynamically
    prompt_sections = []
    
    # 1. Task declaration
    task_declaration = f"TASK: {get_task_description(task_type, room_type)}"
    prompt_sections.append(task_declaration)
    
    # 2. Critical requirements header
    prompt_sections.append("\nCRITICAL REQUIREMENTS:")
    
    # 3. Transformation sections (dynamic based on what's being changed)
    req_number = 1
    for element, details in transformations.items():
        section = build_transformation_section(req_number, element, details)
        prompt_sections.append(section)
        req_number += 1
    
    # 4. Style coordination (if multiple elements)
    if len(transformations) > 1:
        coordination_section = f"""
{req_number}. DESIGN COORDINATION:
   - Overall style: {style}
   - All elements must work together harmoniously
   - Maintain consistent design language throughout"""
        prompt_sections.append(coordination_section)
        req_number += 1
    
    # 5. Preservation requirements
    preservation_section = f"""
{req_number}. PRESERVE:"""
    for item in preservation:
        preservation_section += f"\n   - {item}: EXACT same"
    preservation_section += f"\n   - Room layout and architecture: EXACT same"
    prompt_sections.append(preservation_section)
    req_number += 1
    
    # 6. Quality requirements
    quality_section = f"""
{req_number}. QUALITY:
   - {quality_level.capitalize()} result
   - Professional installation appearance
   - Natural lighting and shadows
   - Clean edges and smooth transitions
   - No AI artifacts or distortions
   - Sharp detail throughout"""
    prompt_sections.append(quality_section)
    
    # 7. Output specification
    output_spec = f"\nOUTPUT: Return the {room_type} with {get_transformation_summary(transformations)} transformed."
    prompt_sections.append(output_spec)
    
    return '\n'.join(prompt_sections)
```

### Helper Functions

```python
def get_task_description(task_type: str, room_type: str) -> str:
    """Generate task description based on transformation type."""
    task_map = {
        'paint': f"Repaint the walls in this {room_type}.",
        'flooring': f"Replace the flooring in this {room_type}.",
        'cabinets': f"Replace the cabinets in this {room_type}.",
        'lighting': f"Change the lighting in this {room_type}.",
        'complete': f"Complete transformation of this {room_type} with coordinated design elements."
    }
    return task_map.get(task_type, f"Transform this {room_type}.")

def build_transformation_section(number: int, element: str, details: dict) -> str:
    """Build a transformation section dynamically."""
    section_templates = {
        'walls': f"""
{number}. WALL TRANSFORMATION:
   - Paint ALL walls: {details.get('color', 'specified color')}
   - Color description: {details.get('description', '')}
   - Finish: {details.get('finish', 'Eggshell')}""",
        
        'flooring': f"""
{number}. FLOORING TRANSFORMATION:
   - Replace entire floor: {details.get('material', 'specified material')}
   - Description: {details.get('description', '')}
   - Pattern: {details.get('pattern', '')}
   - Ensure correct perspective and geometry""",
        
        'cabinets': f"""
{number}. CABINET TRANSFORMATION:
   - Replace ALL cabinets (upper and lower)
   - Style: {details.get('style', '')}
   - Color: {details.get('color', '')}
   - Hardware: {details.get('hardware', '')}
   - Finish: {details.get('finish', '')}""",
        
        'lighting': f"""
{number}. LIGHTING:
   - Scenario: {details.get('scenario', '')}
   - Description: {details.get('description', '')}
   - Color temperature: {details.get('temperature', '')}
   - Intensity: {details.get('intensity', '')}
   - Shadow style: {details.get('shadows', '')}"""
    }
    return section_templates.get(element, f"{number}. {element.upper()}: {details}")

def get_transformation_summary(transformations: dict) -> str:
    """Generate a summary of what's being transformed."""
    elements = list(transformations.keys())
    if len(elements) == 1:
        return elements[0]
    elif len(elements) == 2:
        return f"{elements[0]} and {elements[1]}"
    else:
        return ', '.join(elements[:-1]) + f", and {elements[-1]}"
```

### Room-Specific Preservation Lists

```python
ROOM_PRESERVATION_MAPS = {
    'kitchen': [
        'Countertops',
        'Appliances (refrigerator, stove, dishwasher)',
        'Backsplash',
        'Sink and faucet',
        'Windows',
        'Light fixtures (unless changing lighting)'
    ],
    'living_room': [
        'Furniture (sofas, chairs, tables)',
        'Windows and window treatments',
        'Architectural details (moldings, fireplace)',
        'Decorative items',
        'Media equipment'
    ],
    'bedroom': [
        'Bed and bedding',
        'Furniture (dressers, nightstands)',
        'Windows',
        'Closet doors',
        'Decorative items'
    ],
    'bathroom': [
        'Bathtub/shower',
        'Toilet',
        'Sink and vanity (unless replacing)',
        'Mirrors',
        'Fixtures',
        'Windows'
    ]
}
```

### Usage Example

```python
# Example 1: Simple paint change
prompt = generate_universal_prompt(
    task_type='paint',
    room_type='living_room',
    transformations={
        'walls': {
            'color': 'Naval (SW 6244)',
            'description': 'deep navy blue',
            'finish': 'Eggshell'
        }
    },
    preservation=ROOM_PRESERVATION_MAPS['living_room'],
    style='Modern'
)

# Example 2: Complete kitchen transformation
prompt = generate_universal_prompt(
    task_type='complete',
    room_type='kitchen',
    transformations={
        'walls': {
            'color': 'Pure White (SW 7005)',
            'description': 'crisp bright white',
            'finish': 'Satin'
        },
        'flooring': {
            'material': 'dark walnut hardwood',
            'description': 'rich chocolate brown hardwood planks',
            'pattern': '5-inch wide planks'
        },
        'cabinets': {
            'style': 'Shaker',
            'color': 'Naval (SW 6244) - deep navy blue',
            'hardware': 'brushed brass handles and knobs',
            'finish': 'Semi-gloss'
        }
    },
    preservation=ROOM_PRESERVATION_MAPS['kitchen'],
    style='Modern/Contemporary'
)
```

---

## Lessons Learned

### What Works Well
1. **Explicit Color Codes**: Including brand codes (SW, HC) improves accuracy
2. **Material Details**: Specific patterns and dimensions yield better results
3. **Preservation Lists**: Comprehensive lists prevent unwanted changes
4. **Quality Keywords**: "Photorealistic", "professional", "clean edges" improve output
5. **Hierarchical Structure**: Numbered sections help model follow complex instructions

### What Doesn't Work
1. **Vague Language**: "Try to..." or "Ideally..." reduces compliance
2. **Implicit Assumptions**: Model needs explicit instructions for everything
3. **Too Much Flexibility**: "Unless it clashes" creates inconsistent results
4. **Complex Conditionals**: Keep logic simple and direct

### Model-Specific Insights
- **gemini-2.5-flash-image**: Best for image transformations
- **gemini-2.5-flash**: Best for text generation
- **Temperature**: 0.4-0.7 works well (lower = more consistent, higher = more creative)

---

## Next Steps: Universal System

### Phase 1: Template Engine
- Build dynamic prompt generator
- Create room-type configurations
- Develop style libraries

### Phase 2: Validation System
- Automated quality checks
- Consistency verification
- Before/after comparison metrics

### Phase 3: Production API
- RESTful endpoint for transformations
- Batch processing capabilities
- Client presentation automation

### Phase 4: AI-Assisted Design
- Multi-room coordination
- Style recommendation engine
- Cost estimation integration

---

## Appendix: Complete Prompt Examples

### Example 1: Paint Only
```
TASK: Repaint the walls of this living room.

CRITICAL REQUIREMENTS:
1. **Wall Color**: Apply 'Naval (SW 6244)' to ALL wall surfaces. The color is a deep navy blue.
2. **Finish**: The paint finish should be 'Eggshell'.
3. **Preserve**: Do NOT change the floor, ceiling, furniture, windows, doors, or any other objects. Only the wall color should change.
4. **Quality**: The result must be photorealistic. Maintain all original shadows, lighting, and textures on the walls. Edges must be clean.

OUTPUT: Return only the image of the room with the new wall color.
```

### Example 2: Flooring Only
```
TASK: Replace the flooring in this kitchen.

CRITICAL REQUIREMENTS:
1. **Flooring Type**: Install new flooring: Dark Walnut Hardwood.
2. **Description**: The new flooring is rich dark walnut hardwood with deep chocolate brown tones and dramatic grain.
3. **Pattern**: The pattern should be 5-inch wide planks running lengthwise.
4. **Preserve**: Do NOT change the walls, ceiling, furniture, windows, or doors. Only the floor should change.
5. **Quality**: The result must be photorealistic. The new floor must have correct perspective, lighting, and shadows. Edges must be clean where the floor meets the walls and other objects.

OUTPUT: Return only the image of the room with the new flooring.
```

### Example 3: Complete Kitchen
```
TASK: Complete kitchen transformation with coordinated design elements.

CRITICAL REQUIREMENTS:
1. WALL TRANSFORMATION:
   - Paint ALL walls: Pure White (SW 7005)
   - Color: crisp bright white
   - Finish: Satin

2. FLOORING TRANSFORMATION:
   - Replace floor: rich chocolate brown hardwood planks
   - Material: dark walnut hardwood
   - Pattern: 5-inch wide planks

3. CABINET TRANSFORMATION:
   - Replace ALL cabinets (upper and lower)
   - Style: Shaker
   - Color: Naval (SW 6244) - deep navy blue
   - Hardware: brushed brass handles and knobs
   - Finish: Semi-gloss

4. DESIGN COORDINATION:
   - Style: Modern/Contemporary
   - Overall look: Sleek contemporary kitchen
   - Mood: sophisticated, clean, timeless
   - All elements must work together harmoniously

5. PRESERVE:
   - Countertops: EXACT same
   - Appliances: EXACT same
   - Backsplash: EXACT same
   - Windows: EXACT same
   - Room layout: EXACT same

6. QUALITY:
   - Photorealistic kitchen design
   - Professional cabinet installation look
   - Natural lighting and shadows
   - Clean edges and corners
   - No AI artifacts

OUTPUT: Return the kitchen with ALL THREE elements transformed (walls + floor + cabinets).
```

---

## Room Types & Configurations

### Comprehensive Room Database

#### INTERIOR SPACES

**Kitchen Types**
- Traditional Kitchen (single-wall, galley, L-shape, U-shape, island)
- Modern Kitchen (open-concept, minimalist, chef's kitchen)
- Small Apartment Kitchen (compact, efficient)
- Outdoor Kitchen (patio, deck-mounted)

**Living Spaces**
- Living Room (formal, casual, open-concept)
- Family Room (entertainment-focused, kid-friendly)
- Great Room (combined living/dining)
- Den/Study (home office, library)
- Sunroom/Conservatory (glass-walled, three-season)

**Bedrooms**
- Master/Primary Bedroom (en-suite, walk-in closet)
- Guest Bedroom (versatile, neutral)
- Children's Bedroom (playful, functional)
- Nursery (soft, calming)
- Teen Bedroom (modern, personal)

**Bathrooms**
- Master Bathroom (spa-like, dual vanity)
- Guest Bathroom (powder room, half-bath)
- Family Bathroom (full bath, tub/shower)
- En-Suite Bathroom (attached to bedroom)
- Wet Room (fully tiled, barrier-free)

**Utility & Service**
- Laundry Room (mudroom combo, dedicated)
- Mudroom (entry, storage)
- Pantry (walk-in, butler's)
- Closet (walk-in, reach-in, linen)
- Garage (attached, detached, workshop)

**Entertainment & Special**
- Home Theater (media room, screening room)
- Game Room (billiards, arcade)
- Wine Cellar (temperature-controlled, display)
- Home Gym (cardio, weights, yoga)
- Craft Room/Studio (art, sewing, hobby)

**Commercial/Public Spaces**
- Restaurant Dining Room
- Office Space (corporate, home office)
- Retail Store (boutique, showroom)
- Hotel Lobby/Room
- Medical Office (waiting room, exam room)

#### EXTERIOR SPACES

**Outdoor Living**
- Patio (covered, uncovered, screened)
- Deck (wood, composite, multi-level)
- Porch (front, back, wrap-around)
- Balcony (apartment, condo, high-rise)
- Gazebo/Pavilion

**Landscape Features**
- Front Yard (curb appeal, entry)
- Backyard (entertaining, play area)
- Garden (vegetable, flower, zen)
- Pool Area (in-ground, above-ground)
- Outdoor Kitchen/Bar

**Architectural Exteriors**
- House Facade (front elevation)
- Siding (vinyl, wood, brick, stone)
- Roofing (shingles, metal, tile)
- Windows & Doors (entry, garage)
- Fence & Gates

### Room-Specific Preservation Maps

```python
ROOM_PRESERVATION_MAPS = {
    'kitchen': {
        'always_preserve': ['countertops', 'appliances', 'sink', 'faucet', 'backsplash'],
        'by_task': {
            'paint': ['floor', 'ceiling', 'cabinets', 'windows', 'doors', 'trim'],
            'flooring': ['walls', 'ceiling', 'cabinets', 'windows', 'doors'],
            'cabinets': ['walls', 'floor', 'ceiling', 'windows', 'doors'],
            'lighting': ['walls', 'floor', 'ceiling', 'cabinets'],
            'backsplash': ['walls', 'floor', 'ceiling', 'cabinets', 'windows', 'doors'],
        },
        'room_elements': ['island', 'breakfast bar', 'range hood', 'pendant lights']
    },
    
    'living_room': {
        'always_preserve': ['windows', 'doors', 'trim', 'molding'],
        'by_task': {
            'paint': ['floor', 'ceiling', 'furniture', 'fireplace', 'built-ins'],
            'flooring': ['walls', 'ceiling', 'furniture', 'fireplace', 'built-ins'],
            'furniture': ['walls', 'floor', 'ceiling', 'fireplace', 'windows'],
            'lighting': ['walls', 'floor', 'furniture'],
        },
        'room_elements': ['fireplace', 'entertainment center', 'built-in shelves', 'crown molding']
    },
    
    'bedroom': {
        'always_preserve': ['windows', 'doors', 'closet doors'],
        'by_task': {
            'paint': ['floor', 'ceiling', 'furniture', 'bedding', 'closet'],
            'flooring': ['walls', 'ceiling', 'furniture', 'bedding', 'closet'],
            'furniture': ['walls', 'floor', 'ceiling', 'windows', 'closet'],
            'bedding': ['walls', 'floor', 'ceiling', 'furniture', 'windows'],
        },
        'room_elements': ['bed frame', 'nightstands', 'dresser', 'ceiling fan']
    },
    
    'bathroom': {
        'always_preserve': ['toilet', 'sink', 'faucets', 'mirrors', 'shower/tub'],
        'by_task': {
            'paint': ['floor', 'ceiling', 'vanity', 'tile', 'fixtures'],
            'flooring': ['walls', 'ceiling', 'vanity', 'wall tile', 'fixtures'],
            'vanity': ['walls', 'floor', 'ceiling', 'tile', 'fixtures'],
            'tile': ['floor', 'ceiling', 'vanity', 'fixtures'],
        },
        'room_elements': ['vanity cabinet', 'medicine cabinet', 'towel bars', 'lighting']
    },
    
    'dining_room': {
        'always_preserve': ['windows', 'doors', 'chandelier/lighting'],
        'by_task': {
            'paint': ['floor', 'ceiling', 'furniture', 'built-ins', 'wainscoting'],
            'flooring': ['walls', 'ceiling', 'furniture', 'built-ins', 'wainscoting'],
            'furniture': ['walls', 'floor', 'ceiling', 'built-ins', 'windows'],
        },
        'room_elements': ['dining table', 'chairs', 'buffet/sideboard', 'china cabinet']
    },
    
    'home_office': {
        'always_preserve': ['windows', 'doors', 'desk', 'shelving'],
        'by_task': {
            'paint': ['floor', 'ceiling', 'furniture', 'built-ins', 'trim'],
            'flooring': ['walls', 'ceiling', 'furniture', 'built-ins', 'desk'],
            'furniture': ['walls', 'floor', 'ceiling', 'windows'],
        },
        'room_elements': ['desk', 'office chair', 'bookcases', 'file cabinets']
    },
    
    'patio_outdoor': {
        'always_preserve': ['house structure', 'roof overhang', 'railings'],
        'by_task': {
            'flooring': ['furniture', 'walls', 'ceiling', 'plants', 'decor'],
            'furniture': ['flooring', 'walls', 'ceiling', 'plants'],
            'lighting': ['flooring', 'furniture', 'walls', 'plants'],
        },
        'room_elements': ['outdoor furniture', 'planters', 'grill', 'fire pit']
    },
    
    'exterior_facade': {
        'always_preserve': ['roof', 'windows', 'doors', 'foundation'],
        'by_task': {
            'siding': ['roof', 'windows', 'doors', 'trim', 'landscaping'],
            'paint': ['roof', 'windows', 'doors', 'landscaping'],
            'trim': ['roof', 'windows', 'doors', 'siding', 'landscaping'],
            'windows': ['roof', 'siding', 'doors', 'trim', 'landscaping'],
        },
        'room_elements': ['shutters', 'porch', 'columns', 'garage door']
    }
}
```

---

## Transformation Categories

### Paint & Wall Treatments

#### Standard Paint Application
```python
PAINT_PROMPT = f"""TASK: Apply {finish_type} {color_name} paint to the {surface_area} in this {room_type}.

CRITICAL REQUIREMENTS:
1. **Color Application**: Paint {surface_area} with '{color_name} ({color_code})'
   - Color description: {color_description}
   - Coverage: {coverage_instruction} (e.g., "ALL wall surfaces", "accent wall only", "upper walls only")
   
2. **Finish Type**: {finish_type}
   - Sheen level: {sheen_description}
   - Appropriate for: {room_type}
   
3. **Surface Quality**:
   - Smooth, even application
   - No brush marks or roller texture visible
   - Clean edges at trim, ceiling, and corners
   - Maintain existing wall texture (smooth/textured)
   
4. **Lighting Integration**:
   - Color must respond naturally to existing lighting
   - Preserve all shadows and highlights
   - Account for {lighting_condition} (e.g., "natural daylight", "warm artificial")
   
5. **Preserve**: Do NOT change {preservation_list}

OUTPUT: Photorealistic image with professionally painted {surface_area}.
"""
```

#### Accent Walls & Feature Walls
```python
ACCENT_WALL_PROMPT = f"""TASK: Create an accent wall in this {room_type}.

CRITICAL REQUIREMENTS:
1. **Accent Wall Selection**: Paint {wall_location} wall as accent
   - Location: {wall_description} (e.g., "wall behind the bed", "fireplace wall")
   - Color: {accent_color} ({color_code})
   - Contrast: Should {contrast_instruction}
   
2. **Remaining Walls**: Paint other walls {base_color}
   - Creates balanced contrast
   - Highlights the accent wall
   
3. **Design Harmony**:
   - Accent wall complements {existing_elements}
   - Enhances room focal point
   - Appropriate for {design_style} style
   
4. **Preserve**: {preservation_list}

OUTPUT: Room with clearly defined accent wall and harmonious color balance.
"""
```

#### Decorative Wall Treatments
```python
WALL_TREATMENT_OPTIONS = {
    'wainscoting': {
        'prompt_section': """
        - Install wainscoting: {height} height (typically 32-36 inches)
        - Style: {style} (board and batten, raised panel, flat panel, beadboard)
        - Color: {color} on wainscoting, {wall_color} above
        - Include chair rail cap
        """,
        'styles': ['board_and_batten', 'raised_panel', 'flat_panel', 'beadboard', 'shiplap']
    },
    
    'wallpaper': {
        'prompt_section': """
        - Apply wallpaper: {pattern_description}
        - Pattern: {pattern_type} (floral, geometric, striped, textured, mural)
        - Scale: {pattern_scale} (small, medium, large, oversized)
        - Color palette: {colors}
        - Application: {coverage} (full wall, accent wall, ceiling)
        """,
        'patterns': ['floral', 'geometric', 'striped', 'damask', 'tropical', 'abstract', 'mural']
    },
    
    'textured_walls': {
        'prompt_section': """
        - Apply texture: {texture_type}
        - Texture style: {description} (skip trowel, knockdown, orange peel, venetian plaster)
        - Depth: {texture_depth} (light, medium, heavy)
        - Paint color: {color} over texture
        """,
        'textures': ['skip_trowel', 'knockdown', 'orange_peel', 'venetian_plaster', 'sand_finish']
    },
    
    'shiplap': {
        'prompt_section': """
        - Install shiplap: {orientation} (horizontal, vertical, diagonal)
        - Board width: {width} (typically 6-8 inches)
        - Coverage: {coverage_area}
        - Finish: {color} with {sheen} sheen
        - Gap reveal: {gap_size} between boards
        """,
        'orientations': ['horizontal', 'vertical', 'diagonal', 'herringbone']
    }
}
```

### Flooring Systems

#### Comprehensive Flooring Database
```python
FLOORING_CATEGORIES = {
    'hardwood': {
        'species': ['oak', 'maple', 'walnut', 'cherry', 'hickory', 'ash', 'birch', 'bamboo', 'teak'],
        'colors': ['natural', 'honey', 'medium', 'dark', 'ebony', 'gray', 'whitewashed'],
        'finishes': ['matte', 'satin', 'semi-gloss', 'high-gloss', 'hand-scraped', 'wire-brushed'],
        'patterns': ['straight_plank', 'chevron', 'herringbone', 'parquet', 'diagonal'],
        'plank_widths': ['3_inch', '5_inch', '7_inch', 'mixed_width'],
        'prompt_template': """
        - Hardwood species: {species}
        - Color/stain: {color_description}
        - Plank width: {width}
        - Pattern: {pattern}
        - Finish: {finish} with {sheen_level} sheen
        - Grain: {grain_description}
        """
    },
    
    'tile': {
        'materials': ['ceramic', 'porcelain', 'natural_stone', 'marble', 'travertine', 'slate', 'limestone'],
        'sizes': ['12x12', '12x24', '18x18', '24x24', '6x24_plank', '8x8', 'mosaic', 'large_format'],
        'patterns': ['straight_lay', 'diagonal', 'herringbone', 'brick_offset', 'chevron', 'hexagon', 'basket_weave'],
        'finishes': ['matte', 'polished', 'honed', 'textured', 'glazed'],
        'grout_colors': ['white', 'gray', 'black', 'matching', 'contrasting'],
        'prompt_template': """
        - Tile material: {material}
        - Size: {tile_size}
        - Pattern: {pattern_layout}
        - Color: {tile_color}
        - Finish: {surface_finish}
        - Grout: {grout_color} grout, {grout_width} joints
        - Veining: {veining_description} (for stone/marble)
        """
    },
    
    'luxury_vinyl': {
        'styles': ['wood_look', 'stone_look', 'abstract', 'concrete_look'],
        'formats': ['plank', 'tile', 'sheet'],
        'textures': ['embossed', 'smooth', 'hand_scraped', 'wire_brushed'],
        'prompt_template': """
        - LVP/LVT style: {style} replicating {material_mimicked}
        - Format: {format_type}
        - Plank/tile size: {dimensions}
        - Texture: {texture_description}
        - Color: {color_palette}
        - Pattern: {installation_pattern}
        """
    },
    
    'carpet': {
        'styles': ['plush', 'textured', 'frieze', 'berber', 'loop', 'cut_and_loop'],
        'fibers': ['nylon', 'polyester', 'wool', 'triexta', 'olefin'],
        'colors': ['neutral', 'warm', 'cool', 'patterned'],
        'pile_heights': ['low', 'medium', 'high'],
        'prompt_template': """
        - Carpet style: {style}
        - Fiber: {fiber_type}
        - Color: {color_description}
        - Pile height: {pile_height}
        - Texture: {texture_detail}
        - Pattern: {pattern_if_any}
        """
    },
    
    'specialty': {
        'types': ['concrete_polished', 'epoxy', 'terrazzo', 'cork', 'rubber', 'brick', 'cobblestone'],
        'applications': ['residential', 'commercial', 'industrial', 'outdoor'],
        'prompt_template': """
        - Specialty flooring: {flooring_type}
        - Finish: {finish_description}
        - Color/pattern: {appearance}
        - Texture: {surface_texture}
        - Suitable for: {application_area}
        """
    }
}
```

#### Flooring Prompt Structure
```python
FLOORING_PROMPT = f"""TASK: Replace the flooring in this {room_type}.

CRITICAL REQUIREMENTS:
1. **Flooring Installation**: Install {flooring_type}
   - Material: {material_description}
   - Color/Finish: {color_and_finish}
   - Pattern: {pattern_layout}
   - Size/Width: {dimensions}
   
2. **Installation Quality**:
   - Professional installation appearance
   - Proper alignment and pattern flow
   - Clean transitions at doorways and edges
   - Correct perspective throughout room
   
3. **Material Characteristics**:
   - Authentic {material} appearance
   - Appropriate texture and grain
   - Realistic lighting reflections
   - Natural color variation
   
4. **Room Integration**:
   - Flooring works with existing {room_elements}
   - Appropriate for {room_function}
   - Maintains room proportions
   - Enhances {design_style} aesthetic
   
5. **Preserve**: {preservation_list}

OUTPUT: Room with professionally installed {flooring_type} that maintains photorealism.
"""
```

### Cabinetry & Built-ins

#### Cabinet Systems Database
```python
CABINET_SYSTEMS = {
    'kitchen_cabinets': {
        'door_styles': {
            'shaker': 'Five-piece door with recessed center panel and clean lines',
            'flat_panel': 'Modern slab door with no ornamentation',
            'raised_panel': 'Traditional door with raised center panel',
            'glass_front': 'Frame with glass inserts for display',
            'louvered': 'Horizontal slats for ventilation and style',
            'beadboard': 'Vertical planks with decorative grooves',
            'distressed': 'Aged appearance with intentional wear'
        },
        
        'configurations': {
            'upper_cabinets': ['wall_mounted', 'floating', 'glass_door', 'open_shelving'],
            'lower_cabinets': ['base_cabinets', 'drawers', 'pull_out_shelves', 'lazy_susan'],
            'specialty': ['corner_cabinet', 'pantry', 'appliance_garage', 'wine_rack', 'island']
        },
        
        'colors': {
            'white': 'Pure White, Alabaster, Swiss Coffee, Linen White',
            'gray': 'Agreeable Gray, Repose Gray, Mindful Gray, Dorian Gray',
            'blue': 'Naval, Hale Navy, Blue Note, In the Midnight Hour',
            'green': 'Evergreen Fog, Retreat, Pewter Green, Rosemary',
            'wood_tones': 'Natural Oak, Walnut, Cherry, Maple, Hickory',
            'black': 'Tricorn Black, Iron Ore, Black Magic, Caviar'
        },
        
        'hardware': {
            'styles': ['modern_bar', 'traditional_knob', 'cup_pull', 'edge_pull', 'integrated', 'minimal'],
            'finishes': ['brushed_nickel', 'brass', 'black', 'chrome', 'oil_rubbed_bronze', 'gold']
        },
        
        'countertop_integration': ['overhang_details', 'backsplash_connection', 'appliance_cutouts']
    },
    
    'bathroom_vanity': {
        'styles': ['modern_floating', 'traditional_freestanding', 'farmhouse', 'contemporary', 'vintage'],
        'sink_integration': ['undermount', 'vessel', 'integrated', 'farmhouse'],
        'storage': ['drawers', 'cabinets', 'open_shelves', 'medicine_cabinet'],
        'sizes': ['single_24_30', 'single_36_48', 'double_60_72', 'custom']
    },
    
    'built_in_storage': {
        'types': ['bookcase', 'entertainment_center', 'window_seat', 'mudroom_lockers', 'closet_system'],
        'materials': ['wood', 'painted_mdf', 'laminate', 'metal_and_wood'],
        'features': ['adjustable_shelves', 'lighting', 'glass_doors', 'drawers', 'cubbies']
    }
}
```

#### Cabinet Replacement Prompt
```python
CABINET_PROMPT = f"""TASK: Replace {cabinet_scope} cabinets in this {room_type}.

CRITICAL REQUIREMENTS:
1. **Cabinet Specification**:
   - Remove existing cabinets: {existing_description}
   - Install new cabinets: {cabinet_scope} (upper only, lower only, or all)
   - Door style: {door_style}
   - Color/Finish: {color_name} ({color_code}) - {color_description}
   - Cabinet finish: {finish_type}
   
2. **Hardware Details**:
   - Style: {hardware_style}
   - Finish: {hardware_finish}
   - Placement: {hardware_placement}
   
3. **Installation Quality**:
   - Professional cabinet installation
   - Proper alignment and level appearance
   - Consistent door/drawer spacing
   - Clean integration with {countertops/walls}
   
4. **Configuration**:
   - Maintain existing cabinet layout
   - Same number of doors and drawers
   - Same cabinet heights and widths
   - Preserve functional elements (pull-outs, lazy susans)
   
5. **Design Integration**:
   - Cabinets complement {design_style} aesthetic
   - Work harmoniously with {existing_elements}
   - Appropriate for {room_function}
   
6. **Preserve**: {preservation_list}
   - EXACT countertops (material, color, edge)
   - EXACT appliances
   - EXACT backsplash
   - EXACT layout and room structure
   
7. **Quality Standards**:
   - Photorealistic cabinetry
   - Natural wood grain (if wood finish)
   - Proper lighting and shadows
   - Clean edges and professional finish

OUTPUT: Room with professionally installed {door_style} cabinets in {color_name}.
"""
```

### Furniture & Fixtures

#### Furniture Replacement/Styling
```python
FURNITURE_CATEGORIES = {
    'living_room': {
        'seating': ['sofa', 'loveseat', 'sectional', 'armchair', 'recliner', 'ottoman'],
        'tables': ['coffee_table', 'end_table', 'console_table', 'sofa_table'],
        'storage': ['bookcase', 'media_console', 'sideboard', 'display_cabinet'],
        'styles': ['modern', 'traditional', 'mid_century', 'industrial', 'coastal']
    },
    
    'bedroom': {
        'bed_sizes': ['twin', 'full', 'queen', 'king', 'california_king'],
        'bed_styles': ['platform', 'poster', 'upholstered', 'sleigh', 'canopy'],
        'storage': ['dresser', 'nightstand', 'chest', 'armoire', 'bench'],
        'bedding_styles': ['modern', 'traditional', 'farmhouse', 'luxury', 'minimalist']
    },
    
    'dining_room': {
        'table_shapes': ['rectangular', 'round', 'oval', 'square', 'extension'],
        'seating': ['dining_chairs', 'bench', 'upholstered_chairs', 'windsor_chairs'],
        'storage': ['buffet', 'china_cabinet', 'sideboard', 'wine_cabinet']
    },
    
    'outdoor': {
        'seating': ['sectional', 'lounge_chairs', 'dining_set', 'adirondack_chairs', 'swing'],
        'tables': ['dining_table', 'coffee_table', 'side_table', 'bar_cart'],
        'materials': ['wicker', 'teak', 'metal', 'all_weather_fabric', 'aluminum']
    }
}

FURNITURE_PROMPT = f"""TASK: Replace/update furniture in this {room_type}.

CRITICAL REQUIREMENTS:
1. **Furniture Specification**:
   - Item: {furniture_item}
   - Style: {furniture_style}
   - Material: {material_description}
   - Color: {color_palette}
   - Size: {dimensions} (appropriate for room scale)
   
2. **Design Harmony**:
   - Matches {design_style} aesthetic
   - Complements existing {room_elements}
   - Appropriate scale for room size
   - Creates balanced layout
   
3. **Placement & Layout**:
   - Maintain existing furniture arrangement
   - Proper spacing and traffic flow
   - Functional positioning
   - Visual balance in room
   
4. **Quality & Detail**:
   - Photorealistic furniture rendering
   - Accurate material textures
   - Proper shadows and lighting
   - Clean edges and proportions
   
5. **Preserve**: {preservation_list}

OUTPUT: Room with {furniture_item} professionally styled and integrated.
"""
```

### Lighting & Atmosphere

#### Lighting Scenarios
```python
LIGHTING_SCENARIOS = {
    'natural_daylight': {
        'time_of_day': 'Midday (10am-2pm)',
        'characteristics': 'Bright, even, neutral color temperature',
        'shadows': 'Moderate, well-defined',
        'mood': 'Energetic, clear, functional',
        'color_temp': '5500-6500K',
        'prompt_additions': [
            'Abundant natural light streaming through windows',
            'Bright, evenly lit space',
            'Crisp shadows and highlights',
            'True color representation'
        ]
    },
    
    'golden_hour': {
        'time_of_day': 'Late afternoon/early evening',
        'characteristics': 'Warm, directional, glowing',
        'shadows': 'Long, dramatic',
        'mood': 'Romantic, cozy, inviting',
        'color_temp': '2500-3500K',
        'prompt_additions': [
            'Warm golden sunlight',
            'Soft glowing ambiance',
            'Long dramatic shadows',
            'Warm color cast on surfaces'
        ]
    },
    
    'evening_ambient': {
        'time_of_day': 'Evening/night',
        'characteristics': 'Layered artificial lighting',
        'shadows': 'Soft, minimal',
        'mood': 'Intimate, relaxing, comfortable',
        'color_temp': '2700-3000K',
        'prompt_additions': [
            'Warm artificial lighting from fixtures',
            'Layered lighting (ambient + task + accent)',
            'Soft shadows',
            'Cozy evening atmosphere'
        ]
    },
    
    'dramatic_mood': {
        'time_of_day': 'Variable',
        'characteristics': 'High contrast, focused lighting',
        'shadows': 'Deep, dramatic',
        'mood': 'Sophisticated, theatrical, bold',
        'color_temp': 'Variable',
        'prompt_additions': [
            'Dramatic lighting with strong contrasts',
            'Focused spotlighting on key elements',
            'Deep shadows for depth',
            'Theatrical atmosphere'
        ]
    },
    
    'bright_commercial': {
        'time_of_day': 'N/A - artificial',
        'characteristics': 'Bright, even, clinical',
        'shadows': 'Minimal',
        'mood': 'Professional, functional, clean',
        'color_temp': '4000-5000K',
        'prompt_additions': [
            'Bright, evenly distributed lighting',
            'Minimal shadows',
            'Clean, professional appearance',
            'True color rendering'
        ]
    }
}

LIGHTING_PROMPT = f"""TASK: Adjust lighting and atmosphere in this {room_type}.

CRITICAL REQUIREMENTS:
1. **Lighting Scenario**: {scenario_name}
   - Time: {time_of_day}
   - Quality: {light_characteristics}
   - Color temperature: {color_temp}
   - Mood: {desired_mood}
   
2. **Light Sources**:
   {light_source_instructions}
   - Natural: {natural_light_description}
   - Artificial: {artificial_light_description}
   
3. **Shadows & Highlights**:
   - Shadow type: {shadow_description}
   - Highlights: {highlight_description}
   - Contrast level: {contrast_level}
   
4. **Atmospheric Effects**:
   - Overall mood: {mood_description}
   - Color cast: {color_cast}
   - Depth and dimension: {depth_description}
   
5. **Preserve**: ALL physical elements
   - Walls, floor, ceiling remain unchanged
   - Furniture and fixtures stay the same
   - Colors remain accurate under new lighting
   - Room layout and structure preserved
   
OUTPUT: Same room with {scenario_name} lighting that creates {desired_mood} atmosphere.
"""
```

#### Fixture Replacement
```python
LIGHTING_FIXTURES = {
    'kitchen': {
        'types': ['pendant', 'recessed', 'under_cabinet', 'track', 'chandelier'],
        'styles': ['modern', 'industrial', 'farmhouse', 'traditional', 'contemporary'],
        'placement': ['island', 'sink', 'general_ceiling', 'task_areas']
    },
    
    'dining_room': {
        'types': ['chandelier', 'pendant', 'linear_suspension', 'flush_mount'],
        'styles': ['crystal', 'modern', 'rustic', 'transitional', 'art_deco'],
        'size_guide': 'Diameter = (room_length + room_width) × 2.5 inches'
    },
    
    'bedroom': {
        'types': ['ceiling_fan', 'flush_mount', 'table_lamps', 'sconces', 'pendant'],
        'styles': ['modern', 'traditional', 'glam', 'minimalist'],
        'layers': ['ambient', 'task_reading', 'accent']
    },
    
    'bathroom': {
        'types': ['vanity_lights', 'sconces', 'recessed', 'pendant', 'ceiling'],
        'placement': ['above_mirror', 'beside_mirror', 'shower', 'general'],
        'requirements': 'Damp or wet-rated fixtures'
    }
}

FIXTURE_PROMPT = f"""TASK: Replace lighting fixture in this {room_type}.

CRITICAL REQUIREMENTS:
1. **Fixture Specification**:
   - Type: {fixture_type}
   - Style: {fixture_style}
   - Finish: {fixture_finish}
   - Size: {fixture_dimensions}
   - Number of lights: {bulb_count}
   
2. **Installation**:
   - Location: {mounting_location}
   - Height: {hanging_height} (if applicable)
   - Proper scale for room
   - Professional installation appearance
   
3. **Light Quality**:
   - Maintain existing lighting scenario
   - Appropriate light distribution
   - Shadows consistent with fixture style
   - Realistic glow from bulbs
   
4. **Design Integration**:
   - Matches {design_style}
   - Complements room finishes
   - Appropriate for room function
   - Serves as {focal_point/subtle_element}
   
5. **Preserve**: {preservation_list}

OUTPUT: Room with new {fixture_type} fixture professionally installed.
"""
```

---

## Design Styles Library

### Comprehensive Style Database
```python
DESIGN_STYLES = {
    'modern_contemporary': {
        'characteristics': [
            'Clean lines and minimal ornamentation',
            'Neutral color palette with bold accents',
            'Open floor plans and lots of natural light',
            'Mix of materials (metal, glass, wood)',
            'Functional and uncluttered spaces'
        ],
        'color_palettes': {
            'primary': ['white', 'gray', 'black', 'beige'],
            'accents': ['navy', 'emerald', 'mustard', 'terracotta']
        },
        'materials': ['polished_concrete', 'glass', 'steel', 'light_wood', 'quartz'],
        'furniture': 'Low-profile, geometric shapes, modular pieces',
        'lighting': 'Recessed, track, geometric pendants, LED strips'
    },
    
    'traditional_classic': {
        'characteristics': [
            'Timeless elegance and symmetry',
            'Rich, warm color palettes',
            'Detailed moldings and trim work',
            'Classic furniture pieces',
            'Layered textiles and patterns'
        ],
        'color_palettes': {
            'primary': ['cream', 'beige', 'brown', 'burgundy'],
            'accents': ['gold', 'hunter_green', 'deep_red', 'navy']
        },
        'materials': ['hardwood', 'marble', 'brass', 'damask_fabrics', 'oriental_rugs'],
        'furniture': 'Ornate, carved details, wingback chairs, roll-arm sofas',
        'lighting': 'Chandeliers, sconces, table lamps with shades'
    },
    
    'scandinavian': {
        'characteristics': [
            'Minimalist and functional design',
            'Light, airy spaces with white walls',
            'Natural materials and textures',
            'Hygge-inspired coziness',
            'Emphasis on natural light'
        ],
        'color_palettes': {
            'primary': ['white', 'light_gray', 'soft_beige', 'pale_blue'],
            'accents': ['black', 'natural_wood', 'sage_green', 'soft_pink']
        },
        'materials': ['light_wood', 'wool', 'linen', 'leather', 'concrete'],
        'furniture': 'Simple lines, functional, wooden legs, low-profile',
        'lighting': 'Pendant lights, floor lamps, candles, natural light'
    },
    
    'industrial': {
        'characteristics': [
            'Exposed structural elements',
            'Raw, unfinished materials',
            'High ceilings and open spaces',
            'Vintage and repurposed items',
            'Urban loft aesthetic'
        ],
        'color_palettes': {
            'primary': ['gray', 'black', 'brown', 'rust'],
            'accents': ['orange', 'yellow', 'red', 'copper']
        },
        'materials': ['exposed_brick', 'concrete', 'metal', 'reclaimed_wood', 'steel'],
        'furniture': 'Metal frames, leather, vintage factory pieces',
        'lighting': 'Edison bulbs, metal pendants, cage lights, track lighting'
    },
    
    'farmhouse_rustic': {
        'characteristics': [
            'Cozy, lived-in comfort',
            'Vintage and antique pieces',
            'Natural wood and stone',
            'Shiplap and barn doors',
            'Mix of old and new'
        ],
        'color_palettes': {
            'primary': ['white', 'cream', 'gray', 'wood_tones'],
            'accents': ['navy', 'forest_green', 'brick_red', 'mustard']
        },
        'materials': ['reclaimed_wood', 'shiplap', 'subway_tile', 'farmhouse_sink', 'butcher_block'],
        'furniture': 'Distressed wood, upholstered pieces, vintage finds',
        'lighting': 'Lanterns, mason jar fixtures, wrought iron, chandeliers'
    },
    
    'coastal_beach': {
        'characteristics': [
            'Light, breezy atmosphere',
            'Ocean-inspired color palette',
            'Natural textures (rope, jute, rattan)',
            'Casual, relaxed vibe',
            'Indoor-outdoor flow'
        ],
        'color_palettes': {
            'primary': ['white', 'sand', 'light_blue', 'seafoam'],
            'accents': ['navy', 'coral', 'turquoise', 'driftwood_gray']
        },
        'materials': ['whitewashed_wood', 'rattan', 'jute', 'linen', 'sea_glass'],
        'furniture': 'Slipcovered sofas, wicker, weathered wood',
        'lighting': 'Rope pendants, nautical fixtures, natural light'
    },
    
    'mid_century_modern': {
        'characteristics': [
            'Iconic 1950s-1960s design',
            'Organic and geometric forms',
            'Integration with nature',
            'Functionality meets style',
            'Bold patterns and colors'
        ],
        'color_palettes': {
            'primary': ['walnut', 'teak', 'white', 'gray'],
            'accents': ['orange', 'teal', 'mustard', 'olive']
        },
        'materials': ['teak_wood', 'walnut', 'molded_plywood', 'formica', 'vinyl'],
        'furniture': 'Eames, Saarinen, tapered legs, low-profile',
        'lighting': 'Sputnik chandeliers, arc lamps, geometric pendants'
    },
    
    'bohemian_eclectic': {
        'characteristics': [
            'Mix of patterns and colors',
            'Global-inspired textiles',
            'Layered and collected look',
            'Personal and artistic',
            'Plants and natural elements'
        ],
        'color_palettes': {
            'primary': ['jewel_tones', 'earth_tones', 'warm_neutrals'],
            'accents': ['purple', 'orange', 'turquoise', 'magenta']
        },
        'materials': ['macrame', 'colorful_textiles', 'vintage_rugs', 'natural_fibers', 'brass'],
        'furniture': 'Mix of vintage and global, low seating, poufs',
        'lighting': 'String lights, moroccan lanterns, colorful pendants'
    },
    
    'minimalist_japanese': {
        'characteristics': [
            'Extreme simplicity and restraint',
            'Neutral, monochromatic palette',
            'Clutter-free spaces',
            'Quality over quantity',
            'Zen-like tranquility'
        ],
        'color_palettes': {
            'primary': ['white', 'black', 'gray', 'beige'],
            'accents': ['soft_green', 'muted_blue', 'warm_wood']
        },
        'materials': ['natural_wood', 'stone', 'paper', 'bamboo', 'concrete'],
        'furniture': 'Low-profile, simple forms, multi-functional',
        'lighting': 'Soft, diffused, paper lanterns, minimal fixtures'
    },
    
    'art_deco_glamorous': {
        'characteristics': [
            '1920s-1930s luxury',
            'Bold geometric patterns',
            'Rich colors and metallics',
            'High contrast and drama',
            'Opulent materials'
        ],
        'color_palettes': {
            'primary': ['black', 'white', 'gold', 'navy'],
            'accents': ['emerald', 'sapphire', 'ruby_red', 'silver']
        },
        'materials': ['marble', 'brass', 'mirror', 'velvet', 'lacquer'],
        'furniture': 'Geometric shapes, mirrored surfaces, velvet upholstery',
        'lighting': 'Crystal chandeliers, geometric sconces, gold fixtures'
    },
    
    'transitional': {
        'characteristics': [
            'Bridge between traditional and contemporary',
            'Balanced and versatile',
            'Clean lines with classic touches',
            'Neutral palette with texture',
            'Timeless appeal'
        ],
        'color_palettes': {
            'primary': ['gray', 'beige', 'taupe', 'white'],
            'accents': ['blue', 'green', 'warm_metallics']
        },
        'materials': ['wood', 'fabric', 'metal', 'glass', 'stone'],
        'furniture': 'Clean-lined traditional pieces, updated classics',
        'lighting': 'Simple chandeliers, updated traditional fixtures'
    }
}
```

### Style-Specific Prompt Modifiers
```python
def get_style_prompt_section(style_name):
    """Generate style-specific prompt section"""
    style = DESIGN_STYLES[style_name]
    
    return f"""
**DESIGN STYLE: {style_name.replace('_', ' ').title()}**
- Aesthetic: {', '.join(style['characteristics'][:3])}
- Color approach: {', '.join(style['color_palettes']['primary'])}
- Key materials: {', '.join(style['materials'][:3])}
- Overall mood: {get_style_mood(style_name)}
- Design principle: {get_style_principle(style_name)}
"""

STYLE_MOODS = {
    'modern_contemporary': 'sleek, sophisticated, uncluttered',
    'traditional_classic': 'elegant, timeless, comfortable',
    'scandinavian': 'cozy, airy, serene',
    'industrial': 'edgy, urban, raw',
    'farmhouse_rustic': 'warm, inviting, nostalgic',
    'coastal_beach': 'relaxed, breezy, fresh',
    'mid_century_modern': 'retro-cool, functional, stylish',
    'bohemian_eclectic': 'artistic, personal, vibrant',
    'minimalist_japanese': 'tranquil, refined, contemplative',
    'art_deco_glamorous': 'luxurious, dramatic, bold',
    'transitional': 'balanced, sophisticated, versatile'
}
```

---

## Advanced Multi-Element Transformations

### Complete Room Makeovers
```python
COMPLETE_ROOM_PROMPT = f"""TASK: Complete {room_type} transformation with {num_elements} coordinated elements.

CRITICAL REQUIREMENTS:

1. WALLS:
   - Color: {wall_color} ({wall_code})
   - Description: {wall_description}
   - Finish: {wall_finish}
   - Treatment: {wall_treatment} (if any - wainscoting, wallpaper, etc.)

2. FLOORING:
   - Type: {flooring_type}
   - Material: {flooring_material}
   - Color/Finish: {flooring_color}
   - Pattern: {flooring_pattern}
   - Size: {flooring_dimensions}

3. {ELEMENT_3_CATEGORY}: (Cabinets, Furniture, Fixtures, etc.)
   - Specific requirements for element 3
   - {element_3_details}

4. {ELEMENT_4_CATEGORY}: (if applicable)
   - Specific requirements for element 4
   - {element_4_details}

5. LIGHTING & ATMOSPHERE:
   - Lighting condition: {lighting_type}
   - Time of day: {time_of_day}
   - Mood: {desired_mood}
   - Atmosphere: {atmosphere_description}

6. DESIGN COORDINATION:
   - Overall style: {design_style}
   - Color harmony: {color_scheme_description}
   - Material cohesion: All materials work together
   - Focal points: {focal_point_elements}
   - Balance: {balance_description}

7. PRESERVE (CRITICAL):
   {generate_preservation_list(room_type, transformation_elements)}

8. QUALITY REQUIREMENTS:
   - Photorealistic result
   - Professional installation quality for ALL elements
   - Natural lighting and shadows
   - Proper material textures
   - Clean edges and transitions
   - No AI artifacts or distortions
   - Maintains room proportions and perspective

OUTPUT: Complete {room_type} with ALL {num_elements} elements professionally transformed and harmoniously coordinated.
"""
```

### Seasonal & Themed Transformations
```python
SEASONAL_THEMES = {
    'spring_refresh': {
        'colors': ['soft_pastels', 'fresh_greens', 'light_blues', 'warm_whites'],
        'materials': ['linen', 'cotton', 'light_wood', 'glass'],
        'accessories': ['fresh_flowers', 'light_curtains', 'botanical_prints'],
        'mood': 'Fresh, airy, renewed, optimistic'
    },
    
    'summer_coastal': {
        'colors': ['whites', 'blues', 'sandy_beiges', 'seafoam'],
        'materials': ['rattan', 'jute', 'whitewashed_wood', 'linen'],
        'accessories': ['nautical_elements', 'stripes', 'natural_textures'],
        'mood': 'Breezy, relaxed, vacation-like, bright'
    },
    
    'fall_cozy': {
        'colors': ['warm_oranges', 'deep_reds', 'golden_yellows', 'chocolate_browns'],
        'materials': ['velvet', 'wool', 'dark_wood', 'copper'],
        'accessories': ['throws', 'pillows', 'candles', 'autumn_botanicals'],
        'mood': 'Warm, inviting, comfortable, harvest-inspired'
    },
    
    'winter_elegant': {
        'colors': ['deep_navy', 'forest_green', 'burgundy', 'silver', 'gold'],
        'materials': ['velvet', 'faux_fur', 'metallic_accents', 'rich_woods'],
        'accessories': ['layered_textiles', 'candles', 'metallic_decor'],
        'mood': 'Cozy, sophisticated, festive, intimate'
    }
}
```

### Before/After Renovation Scenarios
```python
RENOVATION_SCENARIOS = {
    'dated_to_modern': {
        'before_characteristics': ['oak_cabinets', 'laminate_counters', 'vinyl_floors', 'fluorescent_lights'],
        'after_vision': ['white_shaker_cabinets', 'quartz_counters', 'hardwood_floors', 'recessed_lighting'],
        'transformation_focus': 'Modernize and brighten dated space'
    },
    
    'rental_refresh': {
        'constraints': ['cannot_change_structure', 'temporary_updates', 'budget_friendly'],
        'focus_areas': ['paint', 'lighting', 'hardware', 'accessories'],
        'transformation_focus': 'Maximum impact with minimal permanent changes'
    },
    
    'luxury_upgrade': {
        'before_characteristics': ['builder_grade', 'standard_finishes', 'basic_fixtures'],
        'after_vision': ['custom_finishes', 'high_end_materials', 'designer_fixtures'],
        'transformation_focus': 'Elevate to high-end luxury finish'
    },
    
    'open_concept': {
        'before_characteristics': ['closed_off_rooms', 'dark_spaces', 'choppy_layout'],
        'after_vision': ['removed_walls', 'flowing_spaces', 'integrated_areas'],
        'transformation_focus': 'Create open, flowing floor plan'
    }
}
```

---

## Architectural Elements

### Doors & Windows
```python
ARCHITECTURAL_ELEMENTS = {
    'doors': {
        'interior_doors': {
            'styles': ['panel', 'flush', 'french', 'sliding_barn', 'pocket', 'bifold'],
            'materials': ['wood', 'mdf', 'glass', 'composite'],
            'finishes': ['painted', 'stained', 'natural_wood', 'white']
        },
        'exterior_doors': {
            'styles': ['single_entry', 'double_entry', 'dutch', 'sliding_glass', 'french_patio'],
            'materials': ['wood', 'fiberglass', 'steel', 'glass_and_metal'],
            'features': ['sidelights', 'transom', 'decorative_glass']
        }
    },
    
    'windows': {
        'types': ['double_hung', 'casement', 'sliding', 'bay', 'bow', 'picture', 'awning'],
        'treatments': ['curtains', 'blinds', 'shades', 'shutters', 'valances'],
        'styles': ['traditional_divided_light', 'modern_full_pane', 'craftsman', 'colonial']
    },
    
    'trim_molding': {
        'types': ['baseboards', 'crown_molding', 'chair_rail', 'picture_rail', 'window_casing', 'door_casing'],
        'styles': ['simple_colonial', 'ornate_victorian', 'minimal_modern', 'craftsman'],
        'heights': ['standard_3_inch', 'tall_5_inch', 'statement_7_plus_inch']
    },
    
    'ceiling_details': {
        'types': ['coffered', 'tray', 'vaulted', 'beamed', 'shiplap', 'tin_tile'],
        'treatments': ['painted', 'wood_stained', 'wallpapered', 'textured']
    },
    
    'fireplace': {
        'styles': ['traditional_brick', 'modern_linear', 'stone_surround', 'tile_surround'],
        'mantels': ['wood', 'stone', 'marble', 'minimal_contemporary'],
        'features': ['built_in_shelving', 'tv_above', 'seating_area']
    }
}
```

---

## Outdoor & Exteriors

### Exterior Transformations
```python
EXTERIOR_CATEGORIES = {
    'siding': {
        'materials': ['vinyl', 'fiber_cement', 'wood', 'brick', 'stone', 'stucco', 'metal'],
        'styles': ['horizontal_lap', 'vertical_board_batten', 'shingle', 'panel'],
        'colors': ['white', 'gray', 'beige', 'blue', 'green', 'natural_wood', 'brick_red']
    },
    
    'exterior_paint': {
        'surfaces': ['siding', 'trim', 'shutters', 'doors', 'garage_doors'],
        'color_schemes': {
            'classic': {'body': 'white/cream', 'trim': 'white', 'accent': 'black'},
            'modern': {'body': 'gray', 'trim': 'white', 'accent': 'black'},
            'craftsman': {'body': 'earth_tone', 'trim': 'cream', 'accent': 'forest_green'},
            'coastal': {'body': 'light_blue', 'trim': 'white', 'accent': 'navy'}
        }
    },
    
    'outdoor_spaces': {
        'patios': {
            'materials': ['concrete', 'pavers', 'flagstone', 'brick', 'stamped_concrete', 'tile'],
            'styles': ['traditional', 'modern', 'mediterranean', 'tropical']
        },
        'decks': {
            'materials': ['wood_cedar', 'wood_redwood', 'composite', 'pvc', 'aluminum'],
            'styles': ['single_level', 'multi_level', 'wraparound', 'rooftop'],
            'railings': ['wood', 'metal', 'glass', 'cable', 'composite']
        },
        'landscaping': {
            'hardscape': ['walkways', 'retaining_walls', 'borders', 'steps'],
            'softscape': ['lawn', 'flower_beds', 'shrubs', 'trees', 'mulch'],
            'features': ['water_fountain', 'fire_pit', 'outdoor_kitchen', 'pergola']
        }
    }
}

EXTERIOR_PROMPT = f"""TASK: Transform the exterior {element_type} of this home.

CRITICAL REQUIREMENTS:
1. **Element Transformation**: {transformation_description}
   - Type: {element_type}
   - Material: {material}
   - Color: {color_specification}
   - Style: {style_description}
   
2. **Installation Quality**:
   - Professional installation appearance
   - Proper alignment and proportions
   - Realistic material textures
   - Appropriate weathering (if applicable)
   
3. **Architectural Harmony**:
   - Complements home architectural style
   - Appropriate scale and proportion
   - Enhances curb appeal
   - Maintains design consistency
   
4. **Environmental Integration**:
   - Realistic outdoor lighting
   - Natural shadows and reflections
   - Weather-appropriate appearance
   - Landscape integration
   
5. **Preserve**: {preservation_list}

OUTPUT: Home exterior with professionally installed {element_type}.
"""
```

---

## Color Schemes & Palettes

### Comprehensive Color Theory
```python
COLOR_HARMONIES = {
    'monochromatic': {
        'definition': 'Single color with variations in shade, tint, and tone',
        'example': 'Various shades of blue from powder to navy',
        'mood': 'Calm, cohesive, sophisticated',
        'application': 'Walls, furniture, accents all in same color family'
    },
    
    'analogous': {
        'definition': 'Colors adjacent on color wheel',
        'example': 'Blue, blue-green, green',
        'mood': 'Harmonious, natural, serene',
        'application': 'Main color for walls, adjacent colors for accents'
    },
    
    'complementary': {
        'definition': 'Colors opposite on color wheel',
        'example': 'Blue and orange, red and green',
        'mood': 'Vibrant, energetic, bold',
        'application': 'One dominant, one accent for high contrast'
    },
    
    'split_complementary': {
        'definition': 'Base color plus two adjacent to its complement',
        'example': 'Blue with red-orange and yellow-orange',
        'mood': 'Dynamic yet balanced',
        'application': 'More nuanced than straight complementary'
    },
    
    'triadic': {
        'definition': 'Three colors evenly spaced on color wheel',
        'example': 'Red, yellow, blue or orange, green, purple',
        'mood': 'Vibrant, playful, balanced',
        'application': 'One dominant, two as accents'
    }
}

ROOM_COLOR_PSYCHOLOGY = {
    'kitchen': {
        'energizing': ['yellow', 'orange', 'warm_red'],
        'calming': ['soft_green', 'light_blue', 'warm_white'],
        'sophisticated': ['navy', 'charcoal', 'sage_green'],
        'best_practices': 'Avoid overly bright or dark colors that affect food appearance'
    },
    
    'bedroom': {
        'relaxing': ['soft_blue', 'lavender', 'sage_green', 'warm_gray'],
        'romantic': ['blush_pink', 'mauve', 'soft_peach'],
        'sophisticated': ['charcoal', 'navy', 'deep_green'],
        'best_practices': 'Choose colors that promote relaxation and sleep'
    },
    
    'living_room': {
        'welcoming': ['warm_beige', 'soft_yellow', 'terracotta'],
        'elegant': ['gray', 'taupe', 'cream_with_accents'],
        'bold': ['navy', 'emerald', 'charcoal'],
        'best_practices': 'Consider natural light and room size when choosing colors'
    },
    
    'bathroom': {
        'spa_like': ['soft_blue', 'seafoam', 'pale_gray', 'white'],
        'energizing': ['crisp_white', 'bright_blue', 'mint_green'],
        'dramatic': ['black', 'navy', 'deep_gray'],
        'best_practices': 'Light colors make small bathrooms feel larger'
    },
    
    'home_office': {
        'productive': ['blue', 'green', 'soft_yellow'],
        'creative': ['orange_accents', 'purple_accents', 'energizing_colors'],
        'calming': ['soft_gray', 'beige', 'muted_tones'],
        'best_practices': 'Avoid overly stimulating colors that cause distraction'
    }
}
```

---

## Universal Prompt Template Engine

### Complete Template System
```python
class UniversalPromptGenerator:
    """
    Comprehensive prompt generation system for all home improvement scenarios.
    """
    
    def __init__(self):
        self.room_configs = ROOM_PRESERVATION_MAPS
        self.design_styles = DESIGN_STYLES
        self.transformations = {
            'paint': self._paint_section,
            'flooring': self._flooring_section,
            'cabinets': self._cabinet_section,
            'furniture': self._furniture_section,
            'lighting': self._lighting_section,
            'fixtures': self._fixture_section,
            'architectural': self._architectural_section,
            'exterior': self._exterior_section
        }
    
    def generate(self, room_type, transformation_type, params, style='modern'):
        """
        Generate universal prompt for any transformation.
        
        Args:
            room_type: 'kitchen', 'living_room', 'bedroom', etc.
            transformation_type: 'paint', 'flooring', 'complete', etc.
            params: Dictionary of transformation parameters
            style: Design style to apply
            
        Returns:
            Complete formatted prompt string
        """
        prompt_parts = []
        
        # 1. Task Declaration
        prompt_parts.append(self._task_declaration(room_type, transformation_type, params))
        
        # 2. Critical Requirements
        prompt_parts.append("\nCRITICAL REQUIREMENTS:\n")
        
        # 3. Transformation Sections
        req_num = 1
        if transformation_type == 'complete':
            # Multiple transformations
            for trans_key, trans_data in params['transformations'].items():
                section = self.transformations[trans_key](req_num, trans_data, room_type)
                prompt_parts.append(section)
                req_num += 1
        else:
            # Single transformation
            section = self.transformations[transformation_type](req_num, params, room_type)
            prompt_parts.append(section)
            req_num += 1
        
        # 4. Style Coordination (if multi-element)
        if transformation_type == 'complete' or len(params.get('transformations', {})) > 1:
            prompt_parts.append(self._style_coordination(req_num, style))
            req_num += 1
        
        # 5. Preservation Requirements
        prompt_parts.append(self._preservation_section(req_num, room_type, transformation_type))
        req_num += 1
        
        # 6. Quality Standards
        prompt_parts.append(self._quality_section(req_num))
        
        # 7. Output Specification
        prompt_parts.append(self._output_spec(room_type, transformation_type, params))
        
        return '\n'.join(prompt_parts)
    
    def _task_declaration(self, room_type, trans_type, params):
        """Generate task declaration."""
        task_map = {
            'paint': f"TASK: Repaint the walls in this {room_type}.",
            'flooring': f"TASK: Replace the flooring in this {room_type}.",
            'cabinets': f"TASK: Replace the cabinets in this {room_type}.",
            'complete': f"TASK: Complete {room_type} transformation with coordinated design elements.",
            'lighting': f"TASK: Adjust lighting and atmosphere in this {room_type}.",
            'furniture': f"TASK: Replace/update furniture in this {room_type}.",
            'exterior': f"TASK: Transform the exterior of this home."
        }
        return task_map.get(trans_type, f"TASK: Transform this {room_type}.")
    
    def _paint_section(self, num, params, room_type):
        """Generate paint transformation section."""
        return f"""
{num}. WALL TRANSFORMATION:
   - Paint {params.get('coverage', 'ALL walls')}: {params['color']} ({params.get('code', '')})
   - Color description: {params.get('description', '')}
   - Finish: {params.get('finish', 'Eggshell')}
   - Surface quality: Smooth, even application with clean edges
   - Lighting integration: Color responds naturally to existing lighting"""
    
    def _flooring_section(self, num, params, room_type):
        """Generate flooring transformation section."""
        return f"""
{num}. FLOORING TRANSFORMATION:
   - Replace entire floor: {params['material']}
   - Description: {params.get('description', '')}
   - Pattern: {params.get('pattern', 'standard')}
   - Size: {params.get('dimensions', '')}
   - Installation: Professional appearance with proper alignment and perspective"""
    
    def _cabinet_section(self, num, params, room_type):
        """Generate cabinet transformation section."""
        return f"""
{num}. CABINET TRANSFORMATION:
   - Replace {params.get('scope', 'ALL')} cabinets
   - Door style: {params['style']}
   - Color/Finish: {params['color']} - {params.get('description', '')}
   - Hardware: {params.get('hardware', 'matching hardware')}
   - Cabinet finish: {params.get('finish', 'Semi-gloss')}
   - Installation: Professional, properly aligned with consistent spacing"""
    
    def _lighting_section(self, num, params, room_type):
        """Generate lighting transformation section."""
        return f"""
{num}. LIGHTING & ATMOSPHERE:
   - Scenario: {params['scenario']}
   - Description: {params.get('description', '')}
   - Color temperature: {params.get('temperature', '3000K')}
   - Mood: {params.get('mood', '')}
   - Shadow style: {params.get('shadows', 'natural')}"""
    
    def _furniture_section(self, num, params, room_type):
        """Generate furniture transformation section."""
        return f"""
{num}. FURNITURE:
   - Item: {params['item']}
   - Style: {params['style']}
   - Material: {params.get('material', '')}
   - Color: {params.get('color', '')}
   - Scale: Appropriate for room size with balanced layout"""
    
    def _fixture_section(self, num, params, room_type):
        """Generate fixture transformation section."""
        return f"""
{num}. LIGHTING FIXTURE:
   - Type: {params['type']}
   - Style: {params['style']}
   - Finish: {params.get('finish', '')}
   - Size: {params.get('size', 'appropriately scaled')}
   - Installation: Professional mounting at proper height"""
    
    def _architectural_section(self, num, params, room_type):
        """Generate architectural element section."""
        return f"""
{num}. ARCHITECTURAL ELEMENT:
   - Element: {params['element']}
   - Style: {params['style']}
   - Material: {params.get('material', '')}
   - Finish: {params.get('finish', '')}
   - Integration: Seamlessly integrated with existing architecture"""
    
    def _exterior_section(self, num, params, room_type):
        """Generate exterior transformation section."""
        return f"""
{num}. EXTERIOR TRANSFORMATION:
   - Element: {params['element']}
   - Material: {params['material']}
   - Color: {params.get('color', '')}
   - Style: {params['style']}
   - Installation: Professional appearance with realistic weathering"""
    
    def _style_coordination(self, num, style):
        """Generate style coordination section."""
        style_data = self.design_styles.get(style, {})
        return f"""
{num}. DESIGN COORDINATION:
   - Overall style: {style.replace('_', ' ').title()}
   - Aesthetic: {', '.join(style_data.get('characteristics', [])[:2])}
   - All elements must work together harmoniously
   - Maintain consistent design language throughout"""
    
    def _preservation_section(self, num, room_type, trans_type):
        """Generate preservation requirements."""
        config = self.room_configs.get(room_type, {})
        always_preserve = config.get('always_preserve', [])
        task_preserve = config.get('by_task', {}).get(trans_type, [])
        
        all_preserve = list(set(always_preserve + task_preserve))
        
        section = f"\n{num}. PRESERVE:"
        for item in all_preserve:
            section += f"\n   - {item.title()}: EXACT same"
        section += "\n   - Room layout and architecture: EXACT same"
        return section
    
    def _quality_section(self, num):
        """Generate quality requirements."""
        return f"""
{num}. QUALITY STANDARDS:
   - Photorealistic result
   - Professional installation quality
   - Natural lighting and shadows
   - Proper material textures
   - Clean edges and smooth transitions
   - No AI artifacts or distortions
   - Maintains room proportions and perspective"""
    
    def _output_spec(self, room_type, trans_type, params):
        """Generate output specification."""
        if trans_type == 'complete':
            elements = list(params.get('transformations', {}).keys())
            elem_str = ', '.join(elements[:-1]) + f", and {elements[-1]}" if len(elements) > 1 else elements[0]
            return f"\nOUTPUT: Complete {room_type} with {elem_str} professionally transformed."
        else:
            return f"\nOUTPUT: {room_type.title()} with professionally applied {trans_type} transformation."


# Usage Examples
generator = UniversalPromptGenerator()

# Example 1: Simple paint
prompt = generator.generate(
    room_type='living_room',
    transformation_type='paint',
    params={
        'color': 'Naval',
        'code': 'SW 6244',
        'description': 'deep navy blue',
        'finish': 'Eggshell',
        'coverage': 'ALL walls'
    },
    style='modern_contemporary'
)

# Example 2: Complete kitchen
prompt = generator.generate(
    room_type='kitchen',
    transformation_type='complete',
    params={
        'transformations': {
            'paint': {
                'color': 'Pure White',
                'code': 'SW 7005',
                'description': 'crisp bright white',
                'finish': 'Satin'
            },
            'flooring': {
                'material': 'dark walnut hardwood',
                'description': 'rich chocolate brown with dramatic grain',
                'pattern': '5-inch wide planks',
                'dimensions': '5" x random length'
            },
            'cabinets': {
                'scope': 'ALL',
                'style': 'Shaker',
                'color': 'Naval (SW 6244)',
                'description': 'deep navy blue',
                'hardware': 'brushed brass handles and knobs',
                'finish': 'Semi-gloss'
            }
        }
    },
    style='modern_contemporary'
)
```

---

## Quality Control & Validation

### Automated Quality Checks
```python
QUALITY_METRICS = {
    'preservation_check': {
        'description': 'Verify preserved elements remain unchanged',
        'method': 'SSIM comparison on masked regions',
        'threshold': 0.95,
        'action_if_fail': 'Regenerate with stronger preservation language'
    },
    
    'transformation_check': {
        'description': 'Verify intended transformations occurred',
        'method': 'Color histogram analysis for paint, edge detection for flooring',
        'threshold': 0.80,
        'action_if_fail': 'Regenerate with more explicit instructions'
    },
    
    'photorealism_check': {
        'description': 'Detect AI artifacts and unrealistic elements',
        'method': 'Visual quality assessment, edge consistency',
        'threshold': 0.85,
        'action_if_fail': 'Regenerate with quality emphasis'
    },
    
    'consistency_check': {
        'description': 'Ensure multi-element transformations are harmonious',
        'method': 'Color palette analysis, style consistency scoring',
        'threshold': 0.75,
        'action_if_fail': 'Adjust coordination language'
    }
}

def validate_transformation(original_image, transformed_image, params):
    """
    Validate transformation quality.
    
    Returns:
        dict: Validation results with pass/fail for each metric
    """
    results = {
        'overall_pass': True,
        'metrics': {}
    }
    
    # 1. Preservation Check
    if 'preserve_regions' in params:
        preservation_score = calculate_ssim_masked(
            original_image,
            transformed_image,
            params['preserve_regions']
        )
        results['metrics']['preservation'] = {
            'score': preservation_score,
            'pass': preservation_score >= 0.95,
            'threshold': 0.95
        }
        if not results['metrics']['preservation']['pass']:
            results['overall_pass'] = False
    
    # 2. Transformation Check
    transformation_score = verify_transformation_applied(
        original_image,
        transformed_image,
        params['transformation_type'],
        params['transformation_params']
    )
    results['metrics']['transformation'] = {
        'score': transformation_score,
        'pass': transformation_score >= 0.80,
        'threshold': 0.80
    }
    
    # 3. Photorealism Check
    quality_score = assess_photorealism(transformed_image)
    results['metrics']['photorealism'] = {
        'score': quality_score,
        'pass': quality_score >= 0.85,
        'threshold': 0.85
    }
    
    return results
```

### Best Practices Summary
```python
PROMPT_BEST_PRACTICES = {
    'language': {
        'do': [
            'Use directive language: "Paint ALL walls", "Replace ENTIRE floor"',
            'Include specific measurements and dimensions',
            'Reference exact color codes and material names',
            'Use numbered sections for clarity',
            'Specify finish types (matte, satin, semi-gloss)',
            'Include brand names when applicable (SW, HC, Behr)'
        ],
        'dont': [
            'Use tentative language: "try to", "ideally", "if possible"',
            'Leave specifications vague or ambiguous',
            'Rely on implicit understanding',
            'Mix multiple complex concepts in single requirement',
            'Use colloquial or informal language'
        ]
    },
    
    'structure': {
        'do': [
            'Start with clear TASK declaration',
            'Use CRITICAL REQUIREMENTS header',
            'Number all requirement sections',
            'Group related specifications together',
            'Separate transformation from preservation',
            'End with explicit OUTPUT specification'
        ],
        'dont': [
            'Mix requirements randomly without organization',
            'Omit section headers',
            'Create run-on paragraphs',
            'Bury important requirements in middle of text'
        ]
    },
    
    'preservation': {
        'do': [
            'List ALL elements to preserve explicitly',
            'Use "EXACT same" language for emphasis',
            'Include "Do NOT change" statements',
            'Specify both what changes AND what doesn\'t',
            'List room architecture separately (layout, structure)'
        ],
        'dont': [
            'Assume model knows what to preserve',
            'Use vague terms like "keep other things similar"',
            'Rely on conditional preservation ("unless it clashes")',
            'Omit preservation section for "simple" transformations'
        ]
    },
    
    'quality': {
        'do': [
            'Explicitly require "photorealistic" output',
            'Specify "professional installation" appearance',
            'Mention "clean edges" and "smooth transitions"',
            'Include lighting and shadow requirements',
            'Request "no AI artifacts"',
            'Specify material texture authenticity'
        ],
        'dont': [
            'Assume quality is implied',
            'Omit lighting considerations',
            'Forget to mention edge quality',
            'Overlook material authenticity'
        ]
    },
    
    'multi_element': {
        'do': [
            'Use hierarchical numbering (1.1, 1.2, 2.1, 2.2)',
            'Include DESIGN COORDINATION section',
            'Specify how elements should harmonize',
            'Mention overall style and mood',
            'List each transformation with full detail',
            'Include material cohesion requirements'
        ],
        'dont': [
            'Try to compress multiple transformations into one section',
            'Omit coordination requirements',
            'Assume model will balance elements automatically',
            'Skip style specification'
        ]
    }
}
```

---

## Implementation Roadmap

### Phase 1: Core System (Week 1-2)
- ✅ Prompt engineering patterns documented
- ✅ Universal template structure designed
- 🔄 UniversalPromptGenerator class implementation
- 🔄 Room configuration database
- 🔄 Design styles library
- 🔄 Transformation templates for all categories

### Phase 2: Validation & Quality (Week 3-4)
- ⏳ SSIM-based preservation verification
- ⏳ Transformation success detection
- ⏳ Photorealism assessment
- ⏳ Automated quality scoring
- ⏳ Feedback loop for prompt refinement

### Phase 3: Production API (Week 5-6)
- ⏳ RESTful API endpoint design
- ⏳ Batch processing capabilities
- ⏳ Queue management for multiple requests
- ⏳ Result caching and storage
- ⏳ Client presentation automation

### Phase 4: Advanced Features (Week 7-8)
- ⏳ Multi-room coordination
- ⏳ Style recommendation engine
- ⏳ Cost estimation integration
- ⏳ Material availability checking
- ⏳ AR preview integration
- ⏳ Before/after comparison tools

### Phase 5: Scale & Optimize (Week 9-10)
- ⏳ Performance optimization
- ⏳ Prompt caching strategies
- ⏳ Model fine-tuning with successful examples
- ⏳ A/B testing framework for prompt variations
- ⏳ Analytics and usage tracking

---

## Appendix: Quick Reference

### Common Transformations Quick Guide

**Paint Only**
```python
{
    'type': 'paint',
    'color': 'Color Name (Code)',
    'description': 'color description',
    'finish': 'Eggshell|Satin|Semi-Gloss|Matte',
    'coverage': 'ALL walls|accent wall only'
}
```

**Flooring Only**
```python
{
    'type': 'flooring',
    'material': 'hardwood|tile|carpet|vinyl',
    'description': 'detailed material description',
    'pattern': 'plank width, layout pattern',
    'dimensions': 'size specifications'
}
```

**Cabinets Only**
```python
{
    'type': 'cabinets',
    'scope': 'ALL|upper only|lower only',
    'style': 'Shaker|Flat Panel|Raised Panel',
    'color': 'Color Name (Code)',
    'hardware': 'style and finish',
    'finish': 'Semi-gloss|Satin|Matte'
}
```

**Complete Room**
```python
{
    'type': 'complete',
    'transformations': {
        'paint': {...},
        'flooring': {...},
        'cabinets': {...}
    },
    'style': 'modern|traditional|scandinavian|etc',
    'mood': 'sophisticated|cozy|bright|etc'
}
```

### Color Code Reference
- **Sherwin-Williams**: SW #### (e.g., SW 6244)
- **Benjamin Moore**: HC-### or #### (e.g., HC-172, 2123-10)
- **Behr**: PPU##-## or ####-# (e.g., PPU18-06)

### Finish Types
- **Matte/Flat**: No sheen, hides imperfections, not washable
- **Eggshell**: Slight sheen, most versatile for walls
- **Satin**: Soft sheen, easy to clean, good for high-traffic
- **Semi-Gloss**: Noticeable sheen, very durable, trim/cabinets
- **High-Gloss**: Maximum sheen, dramatic, doors/furniture

### Room Size Considerations
- **Small rooms (<150 sq ft)**: Light colors, minimal patterns
- **Medium rooms (150-300 sq ft)**: Versatile, most colors work
- **Large rooms (>300 sq ft)**: Can handle darker/bolder colors

---

**Document Version**: 2.0  
**Last Updated**: October 21, 2025  
**Author**: HomeVision Studio  
**Purpose**: Universal prompt engineering system for all home improvement scenarios

**Total Coverage**: 11 design styles, 8+ room types, 8 transformation categories, 100+ material options, complete validation framework
