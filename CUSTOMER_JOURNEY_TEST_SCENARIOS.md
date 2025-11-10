# HomeView AI - Customer Journey Test Scenarios

**Version:** 1.0  
**Date:** November 8, 2025  
**Purpose:** Comprehensive test scenarios for validating the chat interface across all user personas and home improvement use cases

---

## Table of Contents

1. [Overview](#overview)
2. [Test Methodology](#test-methodology)
3. [Persona Definitions](#persona-definitions)
4. [Journey 1: Homeowner Complete Kitchen Renovation](#journey-1-homeowner-complete-kitchen-renovation)
5. [Journey 2: lets als h](#journey-2-diy-weekend-bathroom-refresh)
6. [Journey 3: Multi-Floor Home Assessment](#journey-3-multi-floor-home-assessment)
7. [Journey 4: Contractor Project Scoping](#journey-4-contractor-project-scoping)
8. [Journey 5: Investment Property ROI Analysis](#journey-5-investment-property-roi-analysis)
9. [Edge Cases & Error Scenarios](#edge-cases--error-scenarios)
10. [API Validation Matrix](#api-validation-matrix)

---

## Overview

This document provides detailed, high-level customer journey test scenarios designed to comprehensively validate the HomeView AI chat interface. Each journey:

- Represents a realistic, complex use case
- Tests multiple system capabilities in sequence
- Includes expected system behaviors and responses
- Maps to specific API endpoints and agents
- Covers both happy paths and edge cases

**Key System Capabilities Being Tested:**
- Digital Twin creation and management
- Multi-modal AI (vision + language)
- Design transformation and visualization
- Material/product recommendations
- Cost estimation and budgeting
- RAG-powered contextual responses
- Document parsing and guide generation
- Contractor matching (future)
- Predictive maintenance (future)
- **Web search integration** (real-time pricing, trends, local data)
- **Image generation** (Imagen 3 for design concepts, comparisons, visualizations)
- **Video recommendations** (YouTube tutorials for DIY guidance)
- **Visual communication** (charts, diagrams, infographics for complex data)

---

## Advanced AI Tool Capabilities

HomeView AI uses multiple specialized tools to enhance customer assistance:

### 1. **Web Search Tool** 🔍
**Purpose:** Retrieve real-time information when internal data is insufficient

**Use Cases:**
- Current material pricing and availability
- Local contractor research and reviews
- Building code updates and permit requirements
- Design trend research
- Product recalls or safety notices
- Local market data for ROI calculations
- Energy efficiency rebate programs

**Example Query:** "Search for current quartz countertop prices in Seattle area"

---

### 2. **Image Generation Tool** 🎨
**Purpose:** Create visual concepts using Gemini Imagen 3

**Use Cases:**
- Before/after renovation mockups
- Design style comparisons (modern vs. traditional)
- Material visualization on actual room photos
- Color palette demonstrations
- Layout alternatives
- Product installation examples
- Problem area illustrations

**Example Prompt:** "Generate a kitchen with white shaker cabinets, quartz counters, and subway tile backsplash"

---

### 3. **YouTube Video Recommendation Tool** 📺
**Purpose:** Suggest relevant tutorial videos for DIY tasks

**Use Cases:**
- Step-by-step installation guides
- Technique demonstrations (tiling, painting, etc.)
- Tool usage tutorials
- Safety and best practices
- Troubleshooting common issues
- Professional tips and tricks

**Example Search:** "How to install subway tile backsplash for beginners"

---

### 4. **Visual Data Communication Tool** 📊
**Purpose:** Generate charts, diagrams, and infographics for complex information

**Use Cases:**
- Cost breakdown pie charts
- Timeline Gantt charts
- ROI comparison graphs
- Material quantity visualizations
- Energy savings projections
- Before/after cost-benefit analysis
- Decision matrices

**Example:** "Generate a cost comparison chart for granite vs. quartz vs. marble countertops"

---

### 5. **Contractor Search & Recommendation Tool** 🏗️
**Purpose:** Find, verify, and recommend local contractors using Gemini grounding

**Use Cases:**
- Local contractor search by specialty and location
- Real-time license verification via state databases
- Review aggregation from Google, Yelp, Houzz, BBB
- Budget range and project size matching
- Specialty filtering (kitchen, bathroom, basement, etc.)
- Availability checking
- RFP/project scope generation for contractor outreach
- Subcontractor recommendations for trade-specific work

**Example Query:** "Find top-rated licensed kitchen remodeling contractors in Seattle with 4+ star reviews in the $40-60K budget range"

**Key Features:**
- ✅ Real-time search via Gemini grounding (always current)
- ✅ License verification with expiration dates and bond amounts
- ✅ Multi-source review aggregation with recent reviews
- ✅ Match scoring based on specialty, budget, and ratings
- ✅ Detailed contractor profiles with contact info, experience, portfolio
- ✅ Vetting checklist for homeowners
- ✅ RFP document generation
- ✅ Contractor comparison visualization

---

### Tool Integration Guidelines

**When to Use Each Tool:**

| Situation | Recommended Tool | Example |
| Situation | Recommended Tool | Example |
|-----------|------------------|---------|
| User asks "how much does X cost right now?" | Web Search | Current lumber prices in user's region |
| User says "show me what that would look like" | Image Generation | Visualize painted cabinets in user's kitchen |
| User asks "how do I install this?" | YouTube Recommendation | Link to tile installation tutorial |
| User needs to compare options | Visual Data Tool | Chart comparing 3 countertop materials |
| **User asks "help me find a contractor"** | **Contractor Search** | **Licensed contractors in Seattle specializing in kitchens** |
| **User needs contractor for specific trade** | **Contractor Search** | **Find licensed electricians for panel upgrade** |
| User wants design inspiration | Image Generation | Generate 3 style variations |
| Complex ROI data | Visual Data Tool | Multi-year investment projection graph |
| **User ready to hire** | **Contractor Search + Document Gen** | **Search contractors, generate RFP, create comparison chart** |

---

## Test Methodology

### How to Use These Scenarios

1. **Sequential Testing**: Execute each conversation step in order
2. **Context Preservation**: Ensure conversation context is maintained throughout
3. **Response Validation**: Check for expected intents, actions, and data
4. **API Verification**: Confirm correct backend API calls are triggered
5. **Edge Case Testing**: Test both happy paths and error conditions

### Success Criteria

Each journey should demonstrate:
- ✅ Accurate intent classification
- ✅ Appropriate context retrieval from RAG
- ✅ Correct data extraction from Digital Twin
- ✅ Actionable recommendations
- ✅ Natural conversation flow
- ✅ Proper error handling
- ✅ Suggested follow-up actions

---

## Persona Definitions

### 1. **Homeowner** (Primary Persona)
- **Profile**: First-time renovator, 35-55 years old, budget-conscious
- **Goals**: Increase home value, improve living space, make informed decisions
- **Pain Points**: Overwhelming choices, cost uncertainty, **finding reliable contractors**
- **Tech Savvy**: Moderate - comfortable with apps, wants simple interfaces

### 2. **DIY Worker** (Secondary Persona)
- **Profile**: Weekend warrior, 25-45 years old, hands-on, budget-limited
- **Goals**: Save money, learn new skills, complete projects safely
- **Pain Points**: Lack of expertise, material calculations, tool requirements, **knowing when to hire pros**
- **Tech Savvy**: High - watches YouTube, reads forums, comfortable with detailed info

### 3. **Contractor** (Professional Persona)
- **Profile**: Licensed professional, 30-60 years old, efficiency-focused
- **Goals**: Accurate estimates, streamlined workflow, client satisfaction
- **Pain Points**: Time-consuming measurements, pricing fluctuations, client communication, **finding reliable subcontractors**
- **Tech Savvy**: Moderate-High - uses professional tools, wants mobile-friendly

### 4. **Property Investor** (Business Persona)
- **Profile**: Landlord/flipper, 35-65 years old, ROI-focused
- **Goals**: Maximize returns, minimize costs, prioritize high-impact improvements
- **Pain Points**: Multiple properties, data tracking, renovation priorities, **coordinating contractors across properties**
- **Tech Savvy**: High - uses analytics, wants data-driven insights

---

## Journey 1: Homeowner Complete Kitchen Renovation

**Persona:** Homeowner (Sarah, 42, suburban homeowner)  
**Context:** Outdated 1990s kitchen, wants modern update, $40-60K budget  
**Scenario Type:** `homeowner` persona, complex multi-step renovation  
**Complexity Level:** ⭐⭐⭐⭐⭐ (Most Complex)  
**Estimated Duration:** 30-45 minutes of conversation  
**System Features Tested:** Digital Twin, Design Transform, Cost Estimation, Product Matching, Document Upload

---

### Step 1: Initial Discovery & Digital Twin Creation

**User Message:**
```
Hi! I'm thinking about renovating my kitchen. It's pretty outdated and I'd like to get a sense of what's possible and how much it might cost. Where should I start?
```

**Expected AI Response:**
- Warm welcome and acknowledgment of renovation plans
- Ask clarifying questions: current kitchen condition, renovation goals, budget range
- Suggest uploading floor plan or room images to create Digital Twin
- Explain benefits of Digital Twin (accurate measurements, better recommendations)

**Intent Classification:** `discovery`, `onboarding`

**Suggested Actions:**
```json
[
  {
    "action": "upload_floor_plan",
    "label": "Upload Floor Plan",
    "description": "Upload your home's floor plan for accurate analysis"
  },
  {
    "action": "upload_room_images",
    "label": "Upload Kitchen Photos",
    "description": "Take photos of your current kitchen"
  }
]
```

**API Endpoints Tested:**
- `POST /api/v1/chat` (conversation initiation)
- Chat workflow intent classification

---

### Step 2: Floor Plan Upload & Analysis

**User Action:**
```
I have a floor plan! Let me upload it.
[User uploads floor plan PDF/image]
```

**Expected AI Response:**
- Confirm successful upload
- Provide analysis summary: detected rooms, floor levels, dimensions
- Specifically identify the kitchen location and dimensions
- Ask if the detected information is accurate

**Intent Classification:** `floor_plan_upload`, `digital_twin_creation`

**Expected Backend Processing:**
```
1. Parse floor plan using Gemini Vision
2. Extract room boundaries, dimensions, labels
3. Create Home and Room records in database
4. Calculate square footage and room count
5. Return structured data with confidence scores
```

**API Endpoints Tested:**
- `POST /api/digital-twin/homes/{home_id}/floor-plan` (multi-floor detection)
- Gemini Vision API for floor plan analysis
- Database: Home, Room creation

**Expected Response Data:**
```json
{
  "rooms_detected": 8,
  "kitchen_found": true,
  "kitchen_dimensions": {
    "length": 14.5,
    "width": 12.0,
    "area": 174.0
  },
  "floor_level": 1,
  "confidence": 0.92
}
```

---

### Step 3: Kitchen Image Upload & Material Detection

**User Message:**
```
Great! Here are some photos of my current kitchen.
[User uploads 3-4 kitchen photos: cabinets, countertops, appliances, overall view]
```

**Expected AI Response:**
- Confirm image upload and processing
- Provide detailed analysis of current materials:
  - Cabinet style, color, finish, condition
  - Countertop material (laminate/granite/quartz)
  - Flooring type and condition
  - Appliance brands and approximate age
  - Wall color and backsplash details
- Ask about specific pain points or desired changes

**Intent Classification:** `image_analysis`, `material_detection`

**Expected Backend Processing:**
```
1. Gemini Vision analyzes each image
2. Detects materials, fixtures, products
3. Creates Material, Fixture, Product records
4. Links to Room in Digital Twin
5. Calculates condition scores
6. Identifies style (e.g., "Traditional Oak, 1990s")
```

**API Endpoints Tested:**
- `POST /api/digital-twin/rooms/{room_id}/images`
- Gemini Vision for material detection
- Database: RoomImage, Material, Fixture, Product creation

**Expected Materials Detected:**
```json
{
  "materials": [
    {
      "category": "cabinetry",
      "material_type": "oak wood",
      "color": "honey oak",
      "finish": "stain",
      "condition": "fair",
      "era": "1990s"
    },
    {
      "category": "countertop",
      "material_type": "laminate",
      "color": "almond",
      "pattern": "solid",
      "condition": "worn"
    },
    {
      "category": "flooring",
      "material_type": "vinyl",
      "color": "beige",
      "condition": "fair"
    }
  ],
  "fixtures": [
    {
      "fixture_type": "sink",
      "material": "stainless steel",
      "style": "drop-in",
      "condition": "good"
    }
  ],
  "appliances": [
    {
      "type": "refrigerator",
      "brand": "unknown",
      "approximate_age": "10-15 years",
      "condition": "functional"
    }
  ]
}
```

---

### Step 4: Style Exploration & Design Visualization

**User Message:**
```
I love modern farmhouse style - white cabinets, butcher block counters, subway tile backsplash. Can you show me what that would look like in my kitchen?
```

**Expected AI Response:**
- Acknowledge style preference
- Explain design transformation capabilities
- **🎨 Generate visual mockups** using Imagen 3
- Offer to generate visualizations with specific material changes
- Provide 2-3 design options (conservative, moderate, bold)
- **🔍 Web search** for current design trends to validate choices
- Ask which elements to prioritize

**Intent Classification:** `design_request`, `style_visualization`

**Tool Usage:**
1. **Image Generation Tool** - Create 3 design variations:
   - Option A: Conservative (paint existing cabinets white)
   - Option B: Moderate (new white shaker cabinets)
   - Option C: Bold (floor-to-ceiling cabinets, statement hood)

2. **Web Search Tool** - Query: "modern farmhouse kitchen trends 2025"
   - Validate user's style choices are current
   - Find inspiration images
   - Identify popular color palettes

**Expected Backend Processing:**
```
1. Parse style preferences from natural language
2. Map to design parameters:
   - Cabinet color: white
   - Countertop: butcher block/wood
   - Backsplash: subway tile, white
   - Style: modern farmhouse
3. Trigger design transformation workflow
4. Generate images using Gemini Imagen 3 (3 variations)
5. Web search for trend validation
6. Return multiple variations with trend insights
```

**API Endpoints Tested:**
- `POST /api/v1/design/transform-paint` (cabinets)
- `POST /api/v1/design/transform-countertops`
- `POST /api/v1/design/comprehensive-redesign`
- `POST /api/v1/tools/web-search`
- `POST /api/v1/tools/generate-image`
- Gemini Imagen 3 for image generation

**Expected Generated Options:**
```json
{
  "design_variations": [
    {
      "option": "A - Conservative Budget",
      "generated_image_url": "/generated_images/kitchen_option_a_20251108.jpg",
      "image_prompt": "Kitchen interior with painted white cabinets, butcher block countertops, white subway tile backsplash, modern farmhouse style, warm lighting",
      "description": "Paint your existing cabinets white, add butcher block counters and subway tile",
      "estimated_cost": "$18,000-$22,000",
      "changes": ["Paint cabinets white", "Butcher block counters", "Subway tile backsplash", "Update hardware"]
    },
    {
      "option": "B - Moderate Transformation",
      "generated_image_url": "/generated_images/kitchen_option_b_20251108.jpg",
      "image_prompt": "Modern farmhouse kitchen with white shaker cabinets, natural butcher block countertops, white subway tile backsplash, pendant lighting, stainless appliances",
      "description": "New white shaker cabinets, butcher block counters, full subway tile wall",
      "estimated_cost": "$35,000-$42,000",
      "changes": ["New shaker cabinets", "Butcher block counters", "Full tile backsplash", "New lighting", "Hardware upgrade"]
    },
    {
      "option": "C - Bold Statement",
      "generated_image_url": "/generated_images/kitchen_option_c_20251108.jpg",
      "image_prompt": "Stunning modern farmhouse kitchen with floor-to-ceiling white shaker cabinets, thick butcher block island, full subway tile walls, statement range hood, open shelving, dramatic pendant lights",
      "description": "Floor-to-ceiling cabinets, large island, statement hood, professional-grade feel",
      "estimated_cost": "$55,000-$68,000",
      "changes": ["Floor-to-ceiling cabinets", "Large island", "Statement hood", "Open shelving accent", "Premium lighting"]
    }
  ],
  "web_search_insights": {
    "query": "modern farmhouse kitchen trends 2025",
    "top_trends": [
      "Warm white cabinets (not stark white)",
      "Mixed materials (wood + white)",
      "Black accents for contrast",
      "Open shelving (but less than 2020)",
      "Statement range hoods",
      "Large format tiles gaining popularity"
    ],
    "validation": "Your style choices align perfectly with current trends! Modern farmhouse remains popular in 2025.",
    "sources": [
      "Architectural Digest - Kitchen Trends 2025",
      "Houzz - Most Popular Kitchen Styles",
      "HGTV - Modern Farmhouse Design Guide"
    ]
  },
  "visual_comparison_chart": {
    "chart_type": "side_by_side_comparison",
    "chart_url": "/generated_images/options_comparison_chart.png",
    "description": "Visual comparison of 3 design options with cost, timeline, and impact ratings"
  }
}
```

**Conversational Follow-up:**
```
I've generated three design options for your modern farmhouse kitchen! 

🎨 **Option A - Conservative Budget** ($18-22K)
[Shows generated image]
Paint your existing cabinets white and add butcher block counters. Quick timeline (3-4 weeks) and significant visual impact without the cost of new cabinets.

🎨 **Option B - Moderate Transformation** ($35-42K) ⭐ RECOMMENDED
[Shows generated image]
New white shaker cabinets, butcher block counters, full subway tile backsplash. This is the most popular choice and delivers authentic modern farmhouse style.

🎨 **Option C - Bold Statement** ($55-68K)
[Shows generated image]
Floor-to-ceiling cabinets, large island, statement hood. This is showroom-quality and would be stunning!

📊 [Shows comparison chart with cost/time/impact]

💡 **Trend Check:** I searched current kitchen design trends, and modern farmhouse is still going strong in 2025! Your vision of white cabinets, butcher block, and subway tile is right on trend. The twist for 2025 is adding some black accents (maybe black hardware or faucet?) for contrast.

Which option resonates with you? We can also mix elements from different options!
```

---
    {
      "name": "Classic Farmhouse",
      "description": "Bright white shaker cabinets, natural butcher block, classic subway tile",
      "image_url": "/generated_images/kitchen_design_1.jpg",
      "style_tags": ["modern_farmhouse", "classic", "bright"]
    },
    {
      "name": "Warm Farmhouse",
      "description": "Soft white cabinets with open shelving, reclaimed wood counters, herringbone subway tile",
      "image_url": "/generated_images/kitchen_design_2.jpg",
      "style_tags": ["modern_farmhouse", "warm", "rustic"]
    },
    {
      "name": "Transitional Farmhouse",
      "description": "Two-tone cabinets (white + gray island), mixed counter materials, large format tile",
      "image_url": "/generated_images/kitchen_design_3.jpg",
      "style_tags": ["modern_farmhouse", "transitional", "bold"]
    }
  ]
}
```

---

### Step 5: Material Selection & Product Recommendations

**User Message:**
```
I love option 2! Can you help me find actual products and materials that match this look? I want quality but I'm watching my budget.
```

**Expected AI Response:**
- Confirm design selection
- Break down into specific product categories:
  - Cabinets (RTA vs. custom)
  - Countertops (butcher block options)
  - Backsplash tile
  - Hardware (knobs, pulls)
  - Lighting fixtures
- **🔍 Web search** for current product availability and pricing
- Provide product recommendations with:
  - Multiple price points (budget, mid-range, premium)
  - Dimensions verified against room size
  - Direct purchase links (if available)
  - Installation difficulty ratings
  - **Real-time price verification**

**Intent Classification:** `product_search`, `material_recommendation`

**Tool Usage:**
1. **Web Search Tool** - Multiple queries:
   - "IKEA white shaker cabinets price 2025"
   - "butcher block countertop cost per square foot"
   - "white subway tile 3x6 bulk pricing"
   - "Modern farmhouse cabinet hardware trending 2025"

2. **Visual Comparison Tool** - Generate product comparison chart with images, specs, prices

**Expected Backend Processing:**
```
1. Extract material requirements from selected design
2. Web search for current prices and availability
3. Query internal product catalog
4. Filter by room dimensions (will it fit?)
5. Filter by budget constraints
6. Match style compatibility
7. Verify current pricing via web search
8. Rank by overall fit score + price + availability
```

**API Endpoints Tested:**
- `POST /api/v1/products/match-to-room`
- `POST /api/intelligence/product-fit`
- `POST /api/v1/tools/web-search`
- `POST /api/v1/tools/generate-visual-comparison`
- Product matching agent
- External: Perplexity API for real-time product search

**Expected Product Recommendations:**
```json
{
  "category": "cabinets",
  "web_search_summary": {
    "query": "white shaker kitchen cabinets prices 2025",
    "findings": "Prices range from $100-$300 per linear foot. IKEA remains most budget-friendly. Supply chain issues resolved, normal lead times restored.",
    "price_trends": "Stable compared to 2024, slight 3% increase expected Q1 2025"
  },
  "recommendations": [
    {
      "product_name": "IKEA GRIMSLOV White Shaker Cabinets",
      "price_range": "$3,000-$5,000",
      "price_per_linear_foot": "$120-$150",
      "price_tier": "budget",
      "current_availability": "In stock - verified via web search",
      "lead_time": "1-2 weeks",
      "fit_score": 0.95,
      "style_score": 0.88,
      "will_fit": true,
      "pros": ["Affordable", "Quality construction", "Soft-close hinges", "In stock"],
      "cons": ["Assembly required", "Limited customization"],
      "link": "https://www.ikea.com/...",
      "recent_reviews": "4.5/5 stars (based on 2,341 reviews)",
      "image_url": "/products/ikea_grimslov_white.jpg"
    },
    {
      "product_name": "CliqStudios Shaker White Cabinets",
      "price_range": "$8,000-$12,000",
      "price_per_linear_foot": "$180-$220",
      "price_tier": "mid-range",
      "current_availability": "Made to order - 4-6 week lead time",
      "fit_score": 0.92,
      "style_score": 0.95,
      "will_fit": true,
      "pros": ["Semi-custom sizing", "Quality plywood", "Better warranty", "Professional look"],
      "cons": ["Higher cost", "Longer lead time"],
      "link": "https://www.cliqstudios.com/...",
      "recent_reviews": "4.7/5 stars (based on 892 reviews)",
      "image_url": "/products/cliqstudios_shaker.jpg"
    },
    {
      "product_name": "Home Depot Hampton Bay Designer Series White",
      "price_range": "$5,500-$7,500",
      "price_per_linear_foot": "$150-$180",
      "price_tier": "mid-budget",
      "current_availability": "In stock at local stores",
      "lead_time": "Immediate - 1 week",
      "fit_score": 0.89,
      "style_score": 0.85,
      "will_fit": true,
      "pros": ["Good quality", "Fast delivery", "Easy returns", "Physical stores"],
      "cons": ["Limited customization", "Standard sizes only"],
      "link": "https://www.homedepot.com/...",
      "recent_reviews": "4.3/5 stars (based on 1,556 reviews)",
      "image_url": "/products/hampton_bay_white.jpg"
    }
  ],
  "visual_comparison": {
    "chart_url": "/generated_images/cabinet_comparison_chart.png",
    "description": "Side-by-side comparison of 3 cabinet options with images, pricing, and key specs"
  }
}
```

**Conversational Response with Web Search Insights:**
```
Perfect choice! I've searched for current prices and availability for modern farmhouse materials. Here's what I found:

🗄️ **Cabinets - White Shaker Style**

📊 [Shows visual comparison chart with product images]

**Budget Option:** IKEA GRIMSLOV ($3-5K)
✅ In stock now, ships in 1-2 weeks
✅ Great reviews (4.5/5 from 2,341 customers)
⚠️ You'll need to assemble (or hire installer for $500-800)

**Mid-Range Option:** CliqStudios ($8-12K) ⭐ BEST VALUE
✅ Semi-custom sizing means perfect fit
✅ Excellent reviews (4.7/5)
⚠️ 4-6 week lead time - order soon!

**Quick Option:** Home Depot Hampton Bay ($5.5-7.5K)
✅ Available at your local store right now
✅ Can see/touch before buying

💡 **Price Trend Alert:** Cabinet prices are stable right now after 2023-2024 fluctuations. This is a good time to buy!

Would you like me to search for countertop and tile options next?
```

---

### Step 6: Material Quantity Calculations

**User Message:**
```
How much butcher block countertop will I need? And how many subway tiles for the backsplash?
```

**Expected AI Response:**
- Calculate precise quantities based on Digital Twin dimensions
- Include waste factor (typically 10-15%)
- Provide both square footage and typical product units
- Break down by area (main counter, island, etc.)
- Include installation tips

**Intent Classification:** `material_quantity`, `calculation_request`

**Expected Backend Processing:**
```
1. Retrieve room dimensions from Digital Twin
2. Calculate counter linear feet and sq ft
3. Calculate backsplash area (typically 18" height)
4. Apply waste factor
5. Convert to product units (tiles per box, slabs needed)
```

**API Endpoints Tested:**
- `POST /api/intelligence/material-quantity`
- Smart recommendations agent

**Expected Calculations:**
```json
{
  "countertops": {
    "material": "butcher block",
    "linear_feet": 22.5,
    "square_feet": 52.5,
    "with_waste": 60.4,
    "slabs_needed": 3,
    "typical_slab_size": "8ft x 25in",
    "notes": "Includes 15% waste factor for cuts and fitting"
  },
  "backsplash": {
    "material": "subway tile 3x6",
    "square_feet": 45.0,
    "with_waste": 51.8,
    "boxes_needed": 6,
    "typical_box_coverage": "9 sq ft per box",
    "tiles_per_box": 48,
    "notes": "Assumes 18-inch backsplash height on three walls"
  }
}
```

---

### Step 7: Comprehensive Cost Estimation

**User Message:**
```
Okay, this is looking great! What's the total cost going to be? I want to understand materials, labor, and timeline. My budget is around $50,000.
```

**Expected AI Response:**
- Comprehensive cost breakdown by category
- Separate materials vs. labor costs
- Timeline estimation (weeks)
- Budget analysis (under/over target)
- Suggest value engineering options if over budget
- Highlight cost drivers
- Include permit costs if applicable

**Intent Classification:** `cost_estimate`, `budget_analysis`

**Expected Backend Processing:**
```
1. Aggregate all selected materials and products
2. Calculate labor costs by category
3. Include markup factors
4. Add permit/inspection costs
5. Regional cost adjustments
6. Timeline estimation based on scope
7. Budget comparison and optimization
```

**API Endpoints Tested:**
- `POST /api/intelligence/cost-estimate`
- Cost intelligence agent
- Regional pricing database queries

**Expected Cost Breakdown:**
```json
{
  "renovation_scope": "moderate",
  "room_name": "Kitchen",
  "room_type": "kitchen",
  "cost_estimate": {
    "materials": {
      "cabinets": {"low": 8000, "high": 12000, "selected": 10000},
      "countertops": {"low": 2500, "high": 4000, "selected": 3200},
      "backsplash": {"low": 800, "high": 1500, "selected": 1100},
      "flooring": {"low": 2000, "high": 3500, "selected": 2800},
      "appliances": {"low": 5000, "high": 8000, "selected": 6500},
      "lighting": {"low": 800, "high": 1500, "selected": 1200},
      "hardware": {"low": 300, "high": 600, "selected": 450},
      "sink_faucet": {"low": 500, "high": 1200, "selected": 800}
    },
    "labor": {
      "demolition": {"hours": 16, "rate": 65, "total": 1040},
      "electrical": {"hours": 24, "rate": 95, "total": 2280},
      "plumbing": {"hours": 16, "rate": 90, "total": 1440},
      "cabinet_install": {"hours": 32, "rate": 75, "total": 2400},
      "countertop_install": {"hours": 8, "rate": 85, "total": 680},
      "tile_install": {"hours": 20, "rate": 70, "total": 1400},
      "flooring_install": {"hours": 16, "rate": 65, "total": 1040},
      "painting": {"hours": 16, "rate": 55, "total": 880}
    },
    "other": {
      "permits": 450,
      "disposal": 300,
      "inspection": 200,
      "contingency": 2500
    },
    "total_materials": 26050,
    "total_labor": 11160,
    "total_other": 3450,
    "subtotal": 40660,
    "total_range": {
      "low": 38500,
      "high": 52000,
      "best_estimate": 45300
    }
  },
  "timeline": {
    "demolition": "3-4 days",
    "rough_work": "1 week",
    "installation": "2-3 weeks",
    "finishing": "1 week",
    "total_weeks": "5-7 weeks",
    "notes": "Assumes no structural changes or permit delays"
  },
  "budget_analysis": {
    "target_budget": 50000,
    "estimated_cost": 45300,
    "variance": 4700,
    "status": "under_budget",
    "recommendation": "You're within budget! Consider upgrading lighting fixtures or adding a pot filler faucet."
  },
  "cost_drivers": [
    "Cabinet selection (22% of total)",
    "Appliances (14% of total)",
    "Labor costs (25% of total)"
  ],
  "value_engineering_options": [
    {
      "suggestion": "Choose IKEA cabinets instead of semi-custom",
      "savings": "$2,000-$4,000",
      "impact": "Low - IKEA quality is excellent for budget"
    },
    {
      "suggestion": "Keep one existing appliance if functional",
      "savings": "$800-$1,500",
      "impact": "Low - mismatched appliances may affect resale"
    }
  ]
}
```

---

### Step 8: Contractor Search & Recommendations

**User Message:**
```
This is perfect! How do I find a contractor to actually do this work? I need someone reliable and within my budget in the Seattle area.
```

**Expected AI Response:**
- **🔍 Use Gemini Grounding** to search for local contractors in real-time
- Provide 5-7 contractor recommendations with:
  - Business name and contact info
  - Ratings and review summaries
  - License verification info
  - Specializations
  - Estimated response time
- Generate project scope document/RFP
- Provide contractor vetting checklist
- Suggest 3-5 questions to ask during consultations

**Intent Classification:** `contractor_search`, `local_professional_search`, `project_planning`

**Tool Usage:**
1. **Web Search Tool (Gemini Grounding)** - Search for:
   - "Top-rated kitchen remodeling contractors in Seattle"
   - "Licensed general contractors Seattle kitchen renovation reviews"
   - "Best home improvement contractors Seattle 2025"

2. **Document Generation** - Create professional RFP/project scope

**Expected Backend Processing:**
```
1. Extract location from conversation (Seattle area)
2. Compile project details (kitchen reno, $45-50K, modern farmhouse)
3. Use Gemini grounding to search for contractors:
   - Filter by specialization (kitchen renovation)
   - Filter by ratings (4+ stars)
   - Verify licensing status
   - Check recent reviews (2023-2025)
4. Generate structured contractor list
5. Create downloadable project scope document
```

**API Endpoints Tested:**
- `POST /api/v1/tools/web-search` (Gemini grounding)
- `POST /api/v1/contractors/search-local`
- `POST /api/v1/documents/generate-project-plan`
- `POST /api/v1/documents/generate-rfp`

**Expected Contractor Search Results:**
```json
{
  "search_location": "Seattle, WA",
  "search_criteria": {
    "specialty": "kitchen renovation",
    "min_rating": 4.0,
    "budget_range": "$45,000-$50,000",
    "license_required": true
  },
  "contractors_found": 7,
  "recommendations": [
    {
      "rank": 1,
      "business_name": "Seattle Kitchen & Bath Remodeling",
      "contact": {
        "phone": "(206) 555-0123",
        "email": "info@seattlekitchenbath.com",
        "website": "https://seattlekitchenbath.com",
        "address": "1234 5th Ave, Seattle, WA 98101"
      },
      "ratings": {
        "google": 4.8,
        "google_reviews": 342,
        "yelp": 4.5,
        "yelp_reviews": 128,
        "houzz": 4.9,
        "houzz_reviews": 89,
        "average": 4.7
      },
      "licensing": {
        "license_number": "SEATKR*873JC",
        "verified": true,
        "status": "Active",
        "expires": "2026-03-15",
        "bond_amount": "$12,000"
      },
      "insurance": {
        "general_liability": "Verified - $2M coverage",
        "workers_comp": "Verified"
      },
      "specializations": [
        "Kitchen Remodeling",
        "Custom Cabinetry",
        "Modern Farmhouse Design",
        "Permit Management"
      ],
      "experience_years": 18,
      "projects_completed": "500+",
      "typical_project_size": "$30,000-$80,000",
      "review_summary": "Highly praised for quality craftsmanship, clear communication, and staying on schedule. Multiple reviews mention excellent project management and attention to detail. Recent clients love their modern farmhouse kitchen transformations.",
      "recent_reviews": [
        {
          "date": "2025-10-15",
          "rating": 5,
          "source": "Google",
          "excerpt": "Amazing work on our kitchen! They transformed our outdated 90s kitchen into a beautiful modern farmhouse space. Stayed within budget and timeline."
        },
        {
          "date": "2025-09-22",
          "rating": 5,
          "source": "Houzz",
          "excerpt": "Professional team from start to finish. Great communication, quality work, and they handled all permits seamlessly."
        }
      ],
      "estimated_response_time": "24-48 hours",
      "availability": "Currently booking 4-6 weeks out",
      "free_consultation": true,
      "portfolio_url": "https://seattlekitchenbath.com/portfolio",
      "match_score": 0.95,
      "why_recommended": "Top-rated specialist in modern farmhouse kitchens with verified licensing, extensive experience, and excellent recent reviews in your budget range."
    },
    {
      "rank": 2,
      "business_name": "Pacific Northwest Home Renovations",
      "contact": {
        "phone": "(206) 555-0456",
        "email": "contact@pnwhome.com",
        "website": "https://pnwhomerenovations.com"
      },
      "ratings": {
        "google": 4.6,
        "google_reviews": 289,
        "average": 4.6
      },
      "licensing": {
        "license_number": "PNWHR*456BC",
        "verified": true,
        "status": "Active"
      },
      "insurance": {
        "general_liability": "Verified - $1M coverage",
        "workers_comp": "Verified"
      },
      "specializations": [
        "Full Kitchen Remodels",
        "Electrical & Plumbing Updates",
        "Energy Efficient Upgrades"
      ],
      "experience_years": 12,
      "typical_project_size": "$25,000-$60,000",
      "review_summary": "Known for thorough project planning and clean work sites. Strong electrical and plumbing expertise. Good value for money.",
      "estimated_response_time": "48-72 hours",
      "availability": "Currently booking 3-4 weeks out",
      "free_consultation": true,
      "match_score": 0.88
    },
    {
      "rank": 3,
      "business_name": "Modern Living Contractors",
      "contact": {
        "phone": "(206) 555-0789",
        "website": "https://modernlivingcontractors.com"
      },
      "ratings": {
        "google": 4.7,
        "google_reviews": 156,
        "yelp": 4.4,
        "yelp_reviews": 92,
        "average": 4.55
      },
      "licensing": {
        "license_number": "MODLV*789DE",
        "verified": true,
        "status": "Active"
      },
      "specializations": [
        "Contemporary Kitchen Design",
        "Smart Home Integration",
        "Custom Solutions"
      ],
      "experience_years": 9,
      "typical_project_size": "$35,000-$75,000",
      "review_summary": "Excellent design sense and modern aesthetic. Slightly higher pricing but delivers premium results. Great for tech-savvy homeowners.",
      "estimated_response_time": "24-48 hours",
      "match_score": 0.82
    },
    {
      "rank": 4,
      "business_name": "Heritage Home Builders",
      "contact": {
        "phone": "(206) 555-0321"
      },
      "ratings": {
        "google": 4.5,
        "google_reviews": 203,
        "average": 4.5
      },
      "licensing": {
        "verified": true,
        "status": "Active"
      },
      "specializations": [
        "Kitchen & Bath Remodeling",
        "Historic Home Renovations"
      ],
      "experience_years": 22,
      "review_summary": "Old-school craftsmanship with attention to detail. Great for traditional and farmhouse styles.",
      "match_score": 0.79
    },
    {
      "rank": 5,
      "business_name": "Evergreen Construction Group",
      "contact": {
        "phone": "(206) 555-0654"
      },
      "ratings": {
        "google": 4.4,
        "google_reviews": 178,
        "average": 4.4
      },
      "licensing": {
        "verified": true,
        "status": "Active"
      },
      "specializations": [
        "Residential Remodeling",
        "Kitchen Renovations"
      ],
      "experience_years": 15,
      "review_summary": "Reliable and professional. Good communication and fair pricing.",
      "match_score": 0.75
    }
  ],
  "search_metadata": {
    "search_performed_at": "2025-11-08T14:32:00Z",
    "sources_consulted": [
      "Google Business Reviews",
      "Yelp",
      "Houzz",
      "Washington State Licensing Board",
      "Better Business Bureau"
    ],
    "data_freshness": "Real-time - November 2025"
  },
  "vetting_checklist": {
    "before_contact": [
      "✅ Verify license status on WA State website",
      "✅ Check Better Business Bureau rating",
      "✅ Read recent reviews (last 6 months)",
      "✅ View portfolio photos if available",
      "✅ Confirm they handle permits"
    ],
    "during_consultation": [
      "Ask for 3-5 recent references",
      "Request proof of insurance",
      "Discuss payment schedule (never pay 100% upfront)",
      "Get detailed written estimate",
      "Confirm warranty terms",
      "Discuss timeline and milestones",
      "Ask about subcontractor usage"
    ],
    "before_signing": [
      "Get at least 3 quotes for comparison",
      "Review contract with lawyer if needed",
      "Ensure permit responsibilities are clear",
      "Verify start date and substantial completion date",
      "Confirm dispute resolution process"
    ]
  }
}
```

**Expected Generated Document:**
```json
{
  "document_type": "project_scope_rfp",
  "title": "Kitchen Renovation - Modern Farmhouse Design - RFP",
  "for_contractors": true,
  "sections": [
    {
      "heading": "Project Overview",
      "content": "Complete kitchen renovation to modern farmhouse style in Seattle, WA. Homeowner seeking licensed, insured contractor for turnkey project."
    },
    {
      "heading": "Scope of Work",
      "items": [
        "Demo existing cabinets, countertops, backsplash",
        "Install new white shaker-style cabinets (IKEA GRIMSLOV or equivalent)",
        "Install butcher block countertops",
        "Install white subway tile backsplash",
        "Replace flooring with wide-plank vinyl",
        "Update electrical for under-cabinet lighting",
        "Install new sink and faucet",
        "All permits and inspections"
      ]
    },
    {
      "heading": "Materials",
      "content": "Homeowner has selected specific materials (list provided). Contractor to source or provide pricing for alternatives."
    },
    {
      "heading": "Budget",
      "content": "$45,000-$50,000 (materials + labor)"
    },
    {
      "heading": "Timeline",
      "content": "Target completion: 5-7 weeks from start. Flexible start date."
    },
    {
      "heading": "Requirements",
      "items": [
        "Licensed general contractor in WA state",
        "Proof of general liability insurance ($1M minimum)",
        "Workers compensation insurance",
        "3-5 references from recent kitchen projects",
        "Detailed written estimate with payment schedule",
        "Permit handling included",
        "Warranty on workmanship (minimum 1 year)"
      ]
    },
    {
      "heading": "Submission Instructions",
      "content": "Please provide detailed estimate by [date]. Include timeline, payment schedule, and references. Contact: [email/phone]"
    }
  ],
  "download_url": "/exports/project_plans/kitchen_reno_rfp_20251108.pdf"
}
```

**Conversational Response with Contractor Recommendations:**
```
Great question! I've searched for top-rated kitchen remodeling contractors in the Seattle area. Here are my recommendations:

🏆 **TOP PICK: Seattle Kitchen & Bath Remodeling**
⭐ 4.7/5 average (342 Google reviews, 128 Yelp, 89 Houzz)
📞 (206) 555-0123 | 🌐 seattlekitchenbath.com
✅ Licensed (SEATKR*873JC) & Insured ($2M coverage)
💼 18 years experience, 500+ kitchens completed

**Why I recommend them:**
- Specialists in modern farmhouse kitchens (your style!)
- Budget range: $30-80K (perfect fit for your $45-50K)
- Recent reviews specifically praise their modern farmhouse work
- Handle all permits and inspections
- Free consultation, typically respond in 24-48 hours

**Recent Review (Oct 2025):** "Amazing work on our kitchen! Transformed our outdated 90s kitchen into a beautiful modern farmhouse space. Stayed within budget and timeline." ⭐⭐⭐⭐⭐

---

🥈 **#2: Pacific Northwest Home Renovations**
⭐ 4.6/5 (289 Google reviews)
📞 (206) 555-0456
✅ Licensed & Insured
💼 12 years experience, $25-60K range

**Strengths:** Excellent electrical/plumbing work, clean work sites, good value

---

🥉 **#3: Modern Living Contractors**
⭐ 4.55/5 (156 Google, 92 Yelp)
📞 (206) 555-0789
💼 9 years experience, $35-75K range

**Strengths:** Contemporary design, smart home integration, premium results

---

**Also Worth Contacting:**
4️⃣ Heritage Home Builders (4.5/5, 22 years, farmhouse specialists)
5️⃣ Evergreen Construction Group (4.4/5, 15 years, reliable & fair pricing)

---

📋 **I've prepared an RFP document** with your project details that you can send to contractors:
[Download Project Scope & RFP] → `/exports/project_plans/kitchen_reno_rfp_20251108.pdf`

**Includes:**
- Complete scope of work
- Selected materials list
- Budget and timeline
- Required credentials
- Submission instructions

---

✅ **Before You Contact Them:**
1. Verify license on WA State Licensing website
2. Read recent reviews (I've provided links)
3. View their portfolio if available

💬 **Questions to Ask During Consultation:**
1. "Can you provide 3 references from modern farmhouse kitchen projects in the last year?"
2. "What's your typical payment schedule?" (Never pay 100% upfront!)
3. "Who handles permits and inspections?"
4. "What warranty do you provide on your work?"
5. "How do you handle unexpected issues or change orders?"

💡 **Pro Tip:** Get quotes from at least 3 contractors. The #1 and #2 options both offer free consultations and typically respond within 24-48 hours!

Would you like me to help you draft initial outreach emails to these contractors?
```

**Suggested Follow-up Actions:**
```json
[
  {
    "action": "generate_contractor_email",
    "label": "Draft Contractor Outreach Email",
    "description": "I'll help you write a professional email to send to contractors"
  },
  {
    "action": "download_rfp",
    "label": "Download RFP Document",
    "url": "/exports/project_plans/kitchen_reno_rfp_20251108.pdf"
  },
  {
    "action": "verify_licenses",
    "label": "Verify Contractor Licenses",
    "url": "https://fortress.wa.gov/lni/bbip/",
    "description": "Check license status on WA State website"
  },
  {
    "action": "view_portfolio",
    "label": "View #1 Contractor Portfolio",
    "url": "https://seattlekitchenbath.com/portfolio"
  }
]
```

---

### Step 9: DIY Guide Alternative

**User Message:**
```
Actually, I'm pretty handy. Could I do some of this work myself to save money? What parts are DIY-friendly?
```

**Expected AI Response:**
- Assess DIY feasibility by task
- Rate difficulty levels (easy/medium/hard)
- Identify tasks requiring licensed professionals
- Estimate time savings vs. labor cost savings
- **📺 Recommend YouTube tutorials** for each DIY task
- Provide safety warnings
- Offer to generate step-by-step DIY guides
- Recommend tools needed
- **🎨 Generate visual safety infographics**

**Intent Classification:** `diy_assessment`, `guide_request`

**Tool Usage:**
1. **YouTube Recommendation Tool** - Find top-rated tutorials for each DIY task
2. **Visual Tool** - Generate DIY difficulty comparison chart and safety infographic
3. **Web Search Tool** - Find current tool rental prices and safety equipment

**Expected Analysis:**
```json
{
  "diy_feasibility": {
    "recommended_diy": [
      {
        "task": "Demolition",
        "difficulty": "medium",
        "time_estimate": "2-3 days",
        "cost_savings": "$1,000",
        "safety_notes": "Wear protective gear, turn off utilities first",
        "required_tools": ["Sledgehammer", "Pry bar", "Reciprocating saw", "Safety goggles"],
        "youtube_tutorials": [
          {
            "title": "How to Demo a Kitchen Safely - Complete Guide",
            "channel": "Home RenoVision DIY",
            "duration": "18:45",
            "views": "2.1M",
            "rating": "98% positive",
            "url": "https://youtube.com/watch?v=..."
          }
        ]
      },
      {
        "task": "Painting",
        "difficulty": "easy",
        "time_estimate": "1-2 days",
        "cost_savings": "$800",
        "safety_notes": "Proper ventilation required",
        "required_tools": ["Roller", "Brushes", "Painter's tape", "Drop cloths"],
        "youtube_tutorials": [
          {
            "title": "How to Paint a Room Like a Pro",
            "channel": "The Paint People",
            "duration": "15:20",
            "views": "3.4M",
            "url": "https://youtube.com/watch?v=..."
          }
        ]
      },
      {
        "task": "Backsplash tile installation",
        "difficulty": "medium",
        "time_estimate": "2-3 days",
        "cost_savings": "$1,200",
        "safety_notes": "Tile saw safety, proper adhesive ventilation",
        "required_tools": ["Tile saw", "Trowel", "Spacers", "Grout float"],
        "youtube_tutorials": [
          {
            "title": "Subway Tile Backsplash Installation - Step by Step",
            "channel": "DIY Creators",
            "duration": "22:15",
            "views": "1.8M",
            "url": "https://youtube.com/watch?v=..."
          }
        ]
      }
    ],
    "hire_professional": [
      {
        "task": "Electrical work",
        "reason": "Code compliance, safety, permit requirements",
        "risk": "Fire hazard, electrical shock, insurance issues",
        "cannot_diy": true
      },
      {
        "task": "Plumbing rough-in",
        "reason": "Code compliance, leak risk, warranty concerns",
        "risk": "Water damage, mold, structural issues"
      },
      {
        "task": "Cabinet installation",
        "reason": "Precision required, heavy lifting, warranty considerations",
        "risk": "Poor alignment, damage to expensive materials"
      }
    ],
    "total_potential_savings": "$3,000-$5,000",
    "total_additional_time": "1-2 weeks",
    "recommendation": "Consider doing demo, painting, and backsplash yourself. Hire pros for electrical, plumbing, and cabinets.",
    "visual_aids": {
      "safety_guide_url": "/generated_images/diy_safety_infographic.png",
      "difficulty_chart_url": "/generated_images/diy_task_comparison.png"
    }
  }
}
```

**API Endpoints Tested:**
- `POST /api/v1/documents/generate-diy-guide`
- `POST /api/v1/tools/youtube-search`
- `POST /api/v1/tools/generate-visual`
- DIY guide generator (from notebooks)

---

### Step 10: Follow-up & Maintenance Guidance

**User Message:**
```
Once the renovation is done, how do I maintain everything? Especially the butcher block counters?
```

**Expected AI Response:**
- Provide maintenance schedules and tips
- Material-specific care instructions
- Preventive maintenance recommendations
- Add to Digital Twin maintenance calendar
- **📺 Recommend maintenance YouTube tutorials**
- Set up reminders (if feature available)
- **🎨 Generate visual maintenance calendar**

**Intent Classification:** `maintenance_guidance`, `digital_twin_update`

**Tool Usage:**
1. **YouTube Recommendation Tool** - Find tutorials for:
   - Butcher block oiling and maintenance
   - Cabinet care and touch-ups
   - Grout sealing techniques

2. **Visual Tool** - Generate yearly maintenance calendar infographic

**Expected Maintenance Guide:**
```json
{
  "maintenance_schedule": {
    "butcher_block_counters": {
      "daily": "Wipe with damp cloth, dry immediately",
      "weekly": "Clean with mild soap and water",
      "monthly": "Apply food-safe mineral oil",
      "quarterly": "Deep clean and re-oil",
      "annually": "Sand and refinish if needed",
      "warnings": ["Never leave standing water", "Avoid harsh chemicals", "Use cutting boards"],
      "youtube_tutorials": [
        {
          "title": "How to Care for Butcher Block Countertops",
          "channel": "Woodworkers Guild of America",
          "duration": "12:20",
          "views": "890K",
          "url": "https://youtube.com/watch?v=...",
          "covers": ["Daily care", "Oiling technique", "Stain removal", "Refinishing"]
        },
        {
          "title": "Butcher Block Maintenance - The Complete Guide",
          "channel": "This Old House",
          "duration": "8:45",
          "views": "1.2M",
          "url": "https://youtube.com/watch?v=..."
        }
      ]
    },
    "white_cabinets": {
      "weekly": "Wipe with microfiber cloth",
      "monthly": "Clean with gentle all-purpose cleaner",
      "quarterly": "Check hardware, tighten if loose",
      "annually": "Touch up paint/finish if needed",
      "youtube_tutorials": [
        {
          "title": "How to Clean White Kitchen Cabinets Without Damage",
          "channel": "Clean My Space",
          "duration": "6:30",
          "views": "654K",
          "url": "https://youtube.com/watch?v=..."
        }
      ]
    },
    "subway_tile_backsplash": {
      "daily": "Wipe cooking splashes",
      "weekly": "Clean with tile cleaner",
      "annually": "Re-seal grout",
      "warnings": ["Avoid abrasive cleaners on grout"],
      "youtube_tutorials": [
        {
          "title": "How to Seal Grout - DIY Tutorial",
          "channel": "Home Repair Tutor",
          "duration": "9:15",
          "views": "1.5M",
          "url": "https://youtube.com/watch?v=...",
          "note": "Watch this before your annual grout sealing"
        }
      ]
    }
  },
  "predictive_maintenance": {
    "next_service_dates": [
      {
        "item": "Butcher block oiling",
        "due_date": "2025-12-08",
        "priority": "medium"
      },
      {
        "item": "Grout sealing",
        "due_date": "2026-11-08",
        "priority": "low"
      }
    ]
  },
  "visual_calendar": {
    "calendar_url": "/generated_images/maintenance_calendar_2025.png",
    "description": "12-month maintenance calendar with all scheduled tasks and reminders"
  }
}
```

**Conversational Response:**
```
Great question! Proper maintenance will keep your kitchen looking amazing for years. Let me break this down:

📅 [Shows visual maintenance calendar for the year]

**Butcher Block Counters** (Most Important!)
Monthly: Oil with food-safe mineral oil (15 minutes)
📺 Watch: "How to Care for Butcher Block Countertops" by Woodworkers Guild (12 min)
   👉 890K views - Shows exactly how to oil and maintain

Daily: Just wipe with damp cloth and dry (no standing water!)
💡 Tip: Keep mineral oil under the sink, set phone reminder for 1st of each month

**White Cabinets**
Weekly: Quick wipe with microfiber cloth
📺 Watch: "How to Clean White Cabinets Without Damage" by Clean My Space (6 min)
💡 Tip: Use Magic Erasers sparingly - they can remove finish!

**Subway Tile Backsplash**
Daily: Wipe cooking splashes before they harden
Annual: Re-seal grout (once per year)
📺 Watch: "How to Seal Grout" by Home Repair Tutor (9 min) 
   👉 Save this video for November 2026!

🔔 Want me to set up maintenance reminders in your calendar?
```

---

### Journey 1 Summary

**Total Conversation Steps:** 10  
**System Features Validated:**
- ✅ Digital Twin creation (floor plan + images)
- ✅ Gemini Vision analysis (materials, fixtures, products)
- ✅ Design transformation (multiple variations)
- ✅ Product matching and recommendations
- ✅ Material quantity calculations
- ✅ Comprehensive cost estimation
- ✅ Timeline planning
- ✅ Document generation (RFP, DIY guides)
- ✅ DIY feasibility assessment
- ✅ Maintenance guidance

**API Endpoints Exercised:**
- Chat workflow (all steps)
- Digital Twin: floor plan, room images
- Design transformation: multiple endpoints
- Intelligence: cost estimate, material quantity, product fit
- Product matching
- Document generation

**Edge Cases to Test:**
- Missing floor plan (proceed with just photos)
- Poor quality images (request better images)
- Budget significantly under estimate (value engineering)
- Unrealistic timeline expectations (educate)
- Conflicting style preferences (clarify)

---

## Journey 2: DIY Weekend Bathroom Refresh

**Persona:** DIY Worker (Mike, 32, weekend warrior, renter with landlord permission)  
**Context:** Small 5x8 bathroom, wants to update paint/fixtures on $800 budget  
**Scenario Type:** `diy_worker` persona, budget-friendly quick project  
**Complexity Level:** ⭐⭐⭐ (Moderate)  
**Estimated Duration:** 15-20 minutes of conversation  
**System Features Tested:** Material calculations, Product search, DIY guides, Budget optimization

---

### Step 1: DIY Project Definition

**User Message:**
```
Hey! I want to refresh my small bathroom this weekend. I'm thinking new paint, maybe a new mirror and light fixture. I've got about $800 to spend. Is that realistic?
```

**Expected AI Response:**
- Enthusiastic support for DIY approach
- Confirm $800 is realistic for a refresh (not full renovation)
- Ask for current bathroom details: size, current condition, rental vs. owned
- Request photos to assess current state
- Set expectations: what's achievable in a weekend

**Intent Classification:** `diy_project_planning`, `budget_validation`

**Suggested Actions:**
```json
[
  {
    "action": "upload_room_images",
    "label": "Upload Bathroom Photos"
  },
  {
    "action": "specify_dimensions",
    "label": "Provide Room Dimensions"
  }
]
```

---

### Step 2: Room Analysis & Scope Refinement

**User Message:**
```
Here are some photos. It's about 5 feet by 8 feet. The vanity is okay but everything else looks dated.
[Uploads 2-3 bathroom photos]
```

**Expected AI Response:**
- Analyze current condition
- Identify what's staying vs. changing
- Confirm DIY skill level needed: beginner-friendly
- Break down realistic weekend scope:
  - ✅ Paint walls and ceiling
  - ✅ Replace light fixture
  - ✅ Replace mirror
  - ✅ Update hardware (towel bars, toilet paper holder)
  - ❌ Not enough time: vanity replacement, tile work
- Budget allocation suggestions

**Expected Material Detection:**
```json
{
  "room_dimensions": {
    "length": 8.0,
    "width": 5.0,
    "height": 8.0,
    "area": 40.0
  },
  "current_materials": {
    "walls": "painted drywall, beige, fair condition",
    "ceiling": "painted, yellowing",
    "vanity": "builder-grade oak, 36 inch, keeping",
    "mirror": "basic plate glass, 24x36",
    "lighting": "Hollywood style, 4-bulb, brass finish",
    "hardware": "chrome, mismatched"
  },
  "assessed_condition": "cosmetically dated, structurally sound"
}
```

**Intent Classification:** `scope_definition`, `image_analysis`

---

### Step 3: Material Quantity & Shopping List

**User Message:**
```
Perfect! What paint should I buy and how much? I like light blue or gray colors that feel spa-like.
```

**Expected AI Response:**
- Calculate paint quantity for 40 sq ft bathroom
- Account for ceiling + walls
- Recommend bathroom-specific paint (moisture-resistant)
- Provide 3-4 color suggestions with virtual samples
- Include primer if needed
- Complete shopping list with quantities

**Expected Calculations:**
```json
{
  "paint_calculation": {
    "wall_area": 208,
    "ceiling_area": 40,
    "total_area": 248,
    "coats_needed": 2,
    "coverage_per_gallon": 350,
    "gallons_needed": 1.42,
    "purchase_recommendation": "2 gallons (1 for walls, 1 for ceiling + walls coat 2)",
    "waste_factor_included": true
  },
  "paint_recommendations": [
    {
      "brand": "Behr Marquee",
      "color": "Atmospheric (PPU13-15)",
      "finish": "Satin (bathroom-rated)",
      "price_per_gallon": 45,
      "total_cost": 90,
      "pros": ["Mold-resistant", "One-coat coverage", "Primer included"],
      "where_to_buy": "Home Depot"
    },
    {
      "brand": "Benjamin Moore Aura Bath & Spa",
      "color": "Palladian Blue (HC-144)",
      "finish": "Satin",
      "price_per_gallon": 75,
      "total_cost": 150,
      "pros": ["Premium quality", "Superior mold resistance", "Low VOC"],
      "where_to_buy": "Benjamin Moore dealers"
    }
  ],
  "complete_shopping_list": {
    "paint_supplies": [
      {"item": "Bathroom paint", "quantity": "2 gallons", "cost": "$90-$150"},
      {"item": "Primer (if needed)", "quantity": "1 gallon", "cost": "$30"},
      {"item": "Paint roller kit", "quantity": "1", "cost": "$15"},
      {"item": "Angled brush 2-inch", "quantity": "1", "cost": "$8"},
      {"item": "Painter's tape", "quantity": "2 rolls", "cost": "$12"},
      {"item": "Drop cloth", "quantity": "1", "cost": "$10"}
    ],
    "fixtures": [
      {"item": "Modern light fixture", "quantity": "1", "cost": "$80-$120"},
      {"item": "Framed mirror", "quantity": "1", "cost": "$60-$100"},
      {"item": "Hardware set (brushed nickel)", "quantity": "1", "cost": "$40-$60"}
    ],
    "estimated_total": "$345-$505 (materials only)",
    "remaining_budget": "$295-$455"
  }
}
```

**API Endpoints Tested:**
- `POST /api/intelligence/material-quantity`
- Product catalog search

---

### Step 4: Product Recommendations

**User Message:**
```
I like the Behr Atmospheric color! Now help me pick a light fixture and mirror that'll look good together. Modern but not too trendy.
```

**Expected AI Response:**
- Style-matched product recommendations
- Verify dimensions fit the space
- Provide multiple price points
- Include installation difficulty ratings
- Direct purchase links

**Expected Product Matches:**
```json
{
  "light_fixtures": [
    {
      "name": "Progress Lighting Archie 3-Light Vanity",
      "price": 89,
      "style": "modern transitional",
      "finish": "chrome",
      "dimensions": "24W x 9H x 7D inches",
      "will_fit": true,
      "fit_explanation": "Ideal for 36-inch vanity",
      "diy_difficulty": "easy",
      "installation_notes": "Simple wire connection, 30-min install",
      "style_match_score": 0.92,
      "link": "https://homedepot.com/...",
      "image_url": "/products/archie_vanity.jpg"
    },
    {
      "name": "Kichler Barrington 4-Light Vanity",
      "price": 129,
      "style": "modern farmhouse",
      "finish": "brushed nickel",
      "dimensions": "30W x 9H x 8D inches",
      "will_fit": true,
      "diy_difficulty": "easy",
      "style_match_score": 0.88
    }
  ],
  "mirrors": [
    {
      "name": "Kate and Laurel Hutton Rectangle Mirror",
      "price": 79,
      "style": "modern",
      "frame": "matte black metal",
      "dimensions": "24W x 36H inches",
      "will_fit": true,
      "fit_explanation": "Proportional to vanity, leaves clearance",
      "diy_difficulty": "easy",
      "installation_notes": "D-ring hanging, 15-min install",
      "style_match_score": 0.95,
      "pairs_well_with": ["Archie light fixture"],
      "link": "https://amazon.com/..."
    }
  ],
  "hardware_sets": [
    {
      "name": "Delta Trinsic 3-Piece Accessory Set",
      "price": 54,
      "finish": "chrome",
      "includes": ["Towel bar", "Towel ring", "TP holder"],
      "style": "contemporary",
      "diy_difficulty": "easy",
      "installation_notes": "Drywall anchors included",
      "style_match_score": 0.90
    }
  ],
  "total_fixture_cost": 222,
  "remaining_budget": 578,
  "recommendation": "All selections fit well within budget. Consider upgrading to premium paint or adding decorative items."
}
```

**API Endpoints Tested:**
- `POST /api/v1/products/match-to-room`
- `POST /api/intelligence/product-fit`

---

### Step 5: Step-by-Step DIY Guide with Video Tutorials

**User Message:**
```
Awesome! I'm ready to start. Can you give me a step-by-step guide for this whole project? I want to do it right.
```

**Expected AI Response:**
- Generate comprehensive DIY guide
- Organized by task with time estimates
- **📺 Recommend specific YouTube tutorials** for each task
- **🎨 Generate visual step-by-step infographics**
- **🔍 Web search** for local tool rental prices (if needed)
- Include safety warnings
- Tool lists
- Pro tips
- Common mistakes to avoid
- Offer downloadable PDF version

**Tool Usage:**
1. **YouTube Recommendation Tool** - Find tutorials for:
   - Bathroom painting techniques
   - Vanity light installation
   - Mirror hanging methods
   - Hardware installation

2. **Image Generation Tool** - Create:
   - Visual color mockup showing "before" vs "after"
   - Step-by-step infographic for the weekend timeline

3. **Web Search Tool** - Query:
   - "tool rental prices near me" (if user needs specialized tools)
   - "bathroom paint color trends 2025" (validate color choice)

**Intent Classification:** `diy_guide_request`, `step_by_step_instructions`, `video_tutorial_request`

**Expected DIY Guide:**
```markdown
# DIY Bathroom Refresh Guide
## Spa-Blue Modern Bathroom Makeover

**Project Duration:** 2-3 days (weekend project)
**Difficulty:** Beginner-Intermediate
**Budget:** $500-$650

🎨 **[Visual Preview]** - Generated mockup showing your bathroom transformation:
- Image URL: `/generated_images/bathroom_before_after_mockup.jpg`
- Shows current beige → new spa blue transformation

📅 **[Visual Timeline]** - Weekend project infographic:
- Image URL: `/generated_images/bathroom_refresh_timeline.png`

---

### 📺 **WATCH FIRST - Essential Tutorials**

Before you begin, watch these videos (total 45 minutes):

1. **"Bathroom Painting Complete Guide"** by Home RenoVision DIY (18 min)
   - 📺 https://youtube.com/watch?v=...
   - ⭐ 2.3M views, 98% positive
   - Covers prep, technique, and moisture-resistant paint tips

2. **"How to Install a Vanity Light Fixture"** by This Old House (12 min)
   - 📺 https://youtube.com/watch?v=...
   - ⭐ 1.5M views, 97% positive
   - **IMPORTANT:** Watch wire connection close-ups at 6:30

3. **"How to Hang a Heavy Mirror Safely"** by Home Repair Tutor (8 min)
   - 📺 https://youtube.com/watch?v=...
   - ⭐ 890K views
   - Shows stud finding and proper anchor techniques

4. **"Installing Bathroom Hardware - Pro Tips"** by DIY Creators (7 min)
   - 📺 https://youtube.com/watch?v=...
   - Shows exact placement measurements

---

### Pre-Project Preparation (1 hour)

**Before You Start:**
- ⚠️ **Safety First**: Turn off electricity at breaker for light fixture work
- Test circuit is off before touching any wires
- Ensure good ventilation for painting
- Protect flooring and fixtures with drop cloths

**🔍 Web Search Insight:**
I searched "bathroom paint trends 2025" - Your spa-blue choice aligns perfectly with current trends! Calming colors are replacing gray as the most popular bathroom choice.

**Tools Needed:**
- Ladder or step stool
- Screwdriver set (Phillips and flathead)
- Drill with bits
- Paint roller and tray
- 2-inch angled brush
- Wire stripper (for light fixture)
- Voltage tester (ESSENTIAL - $10-15)
- Level
- Stud finder ($20-30, or rent for $8/day)
- Measuring tape

💡 **Tool Rental Tip:** If you don't own a stud finder, Home Depot rents them for $8/day. Or use your smartphone - there are free stud finder apps!

**Materials Checklist:**
- [ ] 2 gallons Behr Atmospheric paint
- [ ] Painter's tape (2-3 rolls)
- [ ] Drop cloths
- [ ] Paint roller kit + brush
- [ ] Progress Lighting Archie fixture
- [ ] Kate and Laurel Hutton mirror
- [ ] Delta Trinsic hardware set
- [ ] Drywall anchors (if not included)
- [ ] Wire nuts (if not included with fixture)

---

### Day 1: Preparation & Painting (6-8 hours)

#### Step 1: Clear and Prep (1 hour)
1. Remove all decorations, towels, toiletries
2. Remove old mirror, light fixture, hardware
   - **Mirror removal**: Support mirror, remove mounting hardware
   - **Light fixture**: Turn off breaker, test wires, disconnect
   - **Save**: Keep old drywall anchors location marked
3. Clean walls thoroughly
   - TSP cleaner or sugar soap
   - Let dry completely (30 min)
4. Fill any holes with spackle
   - Let dry 1 hour, sand smooth
5. Tape edges:
   - Around vanity
   - Ceiling line
   - Door/window trim
   - **Pro Tip**: Press tape firmly to prevent bleed

#### Step 2: Prime (if needed) (2 hours)
- Apply primer if:
  - Changing from dark to light color
  - Covering stains or repairs
  - New drywall patches
- Let dry per manufacturer instructions (usually 2-4 hours)

#### Step 3: First Coat of Paint (2-3 hours)
1. Start with ceiling
   - Cut in edges with brush (10 min)
   - Roll main area (20 min)
2. Paint walls
   - Cut in all edges, corners, trim (30-45 min)
   - Roll walls in "W" pattern for even coverage
   - Work top to bottom
3. Let dry 2-4 hours
4. **End of Day 1**: Leave to dry overnight

---

### Day 2: Second Coat & Install Fixtures (6-8 hours)

#### Step 4: Second Coat (2-3 hours)
1. Check first coat coverage
2. Apply second coat same technique
3. Let dry 2-4 hours
4. Remove painter's tape while paint is slightly tacky
   - Pull at 45-degree angle
   - **Pro Tip**: Don't wait until fully dry or it may peel

#### Step 5: Install Light Fixture (45 min - 1 hour)
⚠️ **ELECTRICAL SAFETY REQUIRED**

1. Verify breaker is OFF
2. Test wires with voltage tester
3. Connect fixture wires:
   - Black to black (hot)
   - White to white (neutral)
   - Copper/green to copper/green (ground)
   - Secure with wire nuts, wrap with electrical tape
4. Mount fixture to junction box
5. Install bulbs (LED recommended, 60W equivalent)
6. Turn breaker on and test
7. **When to Call Pro**: If wires are different colors, more than 3 wires, or you're unsure

#### Step 6: Install Mirror (30-45 min)
1. Measure and mark center position
   - Height: 5-6 inches above vanity backsplash
   - **Pro Tip**: Have helper verify level from different angles
2. Mark D-ring or bracket positions
3. Install drywall anchors if not hitting studs
4. Hang mirror
5. Verify level
6. Secure mounting hardware

#### Step 7: Install Hardware (1 hour)
1. **Towel Bar** (centered on largest wall)
   - Height: 48 inches from floor
   - Stud-mounted preferred
2. **Toilet Paper Holder**
   - 26 inches from floor
   - 8-12 inches from front of toilet
3. **Towel Ring** (near sink)
   - 50-52 inches from floor
4. Use level for all installations
5. **Pro Tip**: Drill pilot holes to prevent cracking

#### Step 8: Final Touches (30 min)
1. Touch up any paint nicks
2. Clean all surfaces
3. Remove all drop cloths and tape
4. Caulk any gaps (if needed)
5. Let cure 24 hours before heavy use

---

### Pro Tips & Common Mistakes to Avoid

**Painting:**
- ❌ Don't skip primer on repairs
- ✅ Use bathroom-specific paint (moisture resistant)
- ✅ "Cut in" edges before rolling
- ✅ Remove tape while paint slightly tacky
- ❌ Don't paint in high humidity

**Electrical:**
- ✅ Always turn off breaker, not just light switch
- ✅ Test with voltage tester
- ✅ Take photos of wire connections before disconnecting
- ❌ Never work on live circuits
- ⚠️ Call electrician if uncertain

**Hanging Hardware:**
- ✅ Always use drywall anchors if not in stud
- ✅ Drill pilot holes in tile to prevent cracking
- ❌ Don't overtighten screws (can crack tile)
- ✅ Apply clear silicone to mounting holes in tile (prevent water intrusion)

**Time Management:**
- Start early (8 AM) for drying time
- Primer/paint dry times are critical - don't rush
- Have helper for mirror installation (safety + accuracy)

---

### Budget Breakdown
| Item | Cost |
|------|------|
| Paint (2 gallons) | $90 |
| Paint supplies | $75 |
| Light fixture | $89 |
| Mirror | $79 |
| Hardware set | $54 |
| Misc (anchors, wire nuts, etc.) | $30 |
| **Total** | **$417** |
| **Remaining Budget** | **$383** |

**Upgrade Ideas:**
- Premium faucet ($150-$200)
- Decorative items (plants, art, towels)
- Matching wastebasket/accessories

---

### Timeline
- **Friday Evening**: Shop for materials (2 hours)
- **Saturday**: Prep and paint first coat (6-8 hours)
- **Sunday**: Second coat and install fixtures (6-8 hours)
- **Monday**: Final cure time, enjoy your new bathroom!

---

### Maintenance
- Wait 30 days before cleaning painted surfaces
- Use gentle cleaners (avoid abrasive)
- Touch up paint as needed (keep leftover paint)
- Clean fixtures weekly with mild soap
```

**API Endpoints Tested:**
- `POST /api/v1/documents/generate-diy-guide`
- `POST /api/v1/tools/youtube-search`
- `POST /api/v1/tools/generate-image` (for before/after mockup)
- `POST /api/v1/tools/generate-visual` (for timeline infographic)
- `POST /api/v1/tools/web-search` (for tool rental, trends)
- Document parser service

**Intent Classification:** `diy_guide_request`, `step_by_step_instructions`, `video_tutorial_request`

---

### Step 6: Safety & Troubleshooting

**User Message:**
```
What if I run into problems? Like what if the light fixture wiring is confusing?
```

**Expected AI Response:**
- Common troubleshooting scenarios
- When to stop and call a professional
- Safety-first messaging
- Emergency contact recommendations
- Offer additional resources (videos, forums)

**Expected Troubleshooting Guide:**
```json
{
  "common_issues": [
    {
      "problem": "Paint is streaky or shows roller marks",
      "solution": "Apply additional thin coat. Use high-quality roller. Don't over-work the paint.",
      "prevention": "Use premium paint, maintain wet edge, proper technique"
    },
    {
      "problem": "Paint peeling near shower/tub",
      "solution": "Use bathroom-specific paint. Ensure surface was clean and dry before painting.",
      "call_pro": false
    },
    {
      "problem": "Light fixture has more than 3 wires (black, white, ground)",
      "solution": "⚠️ STOP - Call licensed electrician. May have 3-way switch or other complexity.",
      "call_pro": true,
      "safety_warning": "Do not proceed with installation. Complex wiring requires professional assessment."
    },
    {
      "problem": "Drywall anchor spinning, won't tighten",
      "solution": "Remove anchor, use larger size or toggle bolt. May need to patch hole and start over.",
      "call_pro": false
    },
    {
      "problem": "Mirror is not level after hanging",
      "solution": "Adjust hanging hardware. Use shims behind frame if needed. Get helper to verify from distance.",
      "call_pro": false
    }
  ],
  "when_to_call_professional": [
    "Any electrical issue beyond simple wire-to-wire connection",
    "Discovering mold or water damage during prep",
    "Cracked or damaged tiles need repair",
    "Plumbing leaks discovered",
    "Structural issues (soft walls, water damage)"
  ],
  "emergency_contacts": {
    "electrical_issue": "Turn off breaker, call licensed electrician",
    "water_leak": "Turn off water main, call plumber",
    "injury": "Call 911 if serious"
  }
}
```

---

### Step 7: Post-Project Validation

**User Message:**
```
I'm done! It looks amazing! How do I keep it looking great?
```

**Expected AI Response:**
- Congratulations and positive reinforcement
- Maintenance schedule
- Cleaning product recommendations
- Request for project photos (to improve AI)
- Suggest updating Digital Twin with changes
- Offer to help with next project

**Expected Maintenance Recommendations:**
```json
{
  "maintenance_schedule": {
    "daily": [
      "Wipe down sink and fixtures after use",
      "Run exhaust fan during and after showers"
    ],
    "weekly": [
      "Clean mirror with glass cleaner",
      "Wipe light fixture (dust accumulates)",
      "Clean chrome hardware with microfiber cloth"
    ],
    "monthly": [
      "Deep clean walls with damp microfiber (avoid harsh chemicals on fresh paint)",
      "Check caulk lines for any separation",
      "Clean/replace exhaust fan filter"
    ],
    "every_6_months": [
      "Touch up paint if needed",
      "Deep clean grout (if tile present)",
      "Check for any moisture issues"
    ]
  },
  "cleaning_products": [
    "Gentle all-purpose cleaner (Method, Mrs. Meyer's)",
    "Glass cleaner (Windex, vinegar solution)",
    "Microfiber cloths (prevent scratching)",
    "⚠️ Avoid: Abrasive cleaners, bleach on chrome, harsh chemicals on fresh paint"
  ],
  "paint_care": {
    "curing_time": "30 days for full cure",
    "first_30_days": "Gentle wipes only, no scrubbing",
    "long_term": "Store leftover paint for touch-ups (label with date and room)"
  }
}
```

---

### Journey 2 Summary

**Total Conversation Steps:** 7  
**Persona:** DIY Worker  
**Budget:** $800 (ended up $417 in materials)  
**System Features Validated:**
- ✅ Material quantity calculations (paint)
- ✅ Product matching within budget
- ✅ Dimensional fit verification
- ✅ DIY guide generation
- ✅ Step-by-step instructions
- ✅ Safety warnings and troubleshooting
- ✅ Maintenance recommendations
- ✅ Budget tracking and optimization

**API Endpoints Exercised:**
- Material quantity calculations
- Product catalog search and matching
- DIY guide generation
- Document export

**Key Differentiators from Journey 1:**
- Budget-focused (vs. value-focused)
- DIY emphasis (vs. contractor-based)
- Shorter timeline (weekend vs. weeks)
- Simpler scope (cosmetic vs. full renovation)
- More safety/how-to content

**Edge Cases to Test:**
- Safety concerns (electrical, structural)
- Budget overruns
- Skill level mismatch (project too complex)
- Material unavailability
- Timeline unrealistic for skill level

---

## Journey 3: Multi-Floor Home Assessment

**Persona:** Homeowner (Jennifer, 48, just purchased a 3,000 sq ft two-story home)  
**Context:** New home purchase, wants comprehensive assessment and improvement roadmap  
**Scenario Type:** `homeowner` persona, whole-home digital twin analysis  
**Complexity Level:** ⭐⭐⭐⭐ (High Complexity)  
**Estimated Duration:** 40-60 minutes of conversation  
**System Features Tested:** Multi-floor Digital Twin, Comprehensive analysis, Maintenance predictions, Priority recommendations, Budget planning across multiple rooms

---

### Step 1: Whole-Home Digital Twin Creation

**User Message:**
```
Hi! We just bought a 2-story house built in 1985. It needs work but I'm not sure where to start. Can you help me assess the whole house and figure out what to prioritize?
```

**Expected AI Response:**
- Welcome and congratulate on new home
- Explain comprehensive home assessment approach
- Request floor plan (both floors) for complete Digital Twin
- Explain benefits: room-by-room analysis, budget prioritization, maintenance tracking
- Set expectations for assessment process

**Intent Classification:** `whole_home_assessment`, `digital_twin_creation`, `prioritization_planning`

**Suggested Actions:**
```json
[
  {
    "action": "upload_multi_floor_plan",
    "label": "Upload Floor Plans",
    "description": "Upload floor plans for all levels (basement, main, second floor)"
  },
  {
    "action": "create_home_profile",
    "label": "Create Home Profile",
    "description": "Enter basic home information (year built, square footage, etc.)"
  }
]
```

---

### Step 2: Multi-Floor Plan Analysis

**User Message:**
```
Here's the floor plan document. It shows both floors on one sheet.
[Uploads multi-floor architectural drawing]
```

**Expected AI Response:**
- Confirm receipt and processing
- Detect multiple floor levels from single document
- Provide comprehensive room breakdown by floor
- Calculate total square footage
- Identify key rooms on each level
- Ask for confirmation of room counts and uses

**Expected Backend Processing:**
```
1. Gemini Vision detects multi-floor sheet layout
2. Separates floor plans into distinct levels
3. Analyzes each floor independently
4. Creates FloorPlan records for each level
5. Extracts room boundaries, labels, dimensions
6. Creates Room records with floor_level attribution
7. Calculates per-floor and total square footage
```

**API Endpoints Tested:**
- `POST /api/digital-twin/homes/{home_id}/floor-plan` (multi-floor detection enabled)
- Multi-floor detection prompt
- Digital Twin service

**Expected Analysis Result:**
```json
{
  "multi_floor_detected": true,
  "total_floors": 2,
  "floor_plans": [
    {
      "floor_level": 1,
      "floor_name": "Main Floor",
      "rooms_detected": 6,
      "square_footage": 1500,
      "rooms": [
        {"name": "Living Room", "type": "living_room", "area": 320},
        {"name": "Kitchen", "type": "kitchen", "area": 180},
        {"name": "Dining Room", "type": "dining_room", "area": 150},
        {"name": "Powder Room", "type": "powder_room", "area": 40},
        {"name": "Foyer", "type": "foyer", "area": 80},
        {"name": "Family Room", "type": "family_room", "area": 280}
      ]
    },
    {
      "floor_level": 2,
      "floor_name": "Second Floor",
      "rooms_detected": 5,
      "square_footage": 1500,
      "rooms": [
        {"name": "Master Bedroom", "type": "master_bedroom", "area": 400},
        {"name": "Master Bath", "type": "bathroom", "area": 120},
        {"name": "Bedroom 2", "type": "bedroom", "area": 200},
        {"name": "Bedroom 3", "type": "bedroom", "area": 180},
        {"name": "Hall Bathroom", "type": "bathroom", "area": 100}
      ]
    }
  ],
  "total_rooms": 11,
  "total_square_footage": 3000,
  "bedrooms": 3,
  "bathrooms": 2.5,
  "year_built": 1985,
  "home_age": 40
}
```

**Intent Classification:** `multi_floor_analysis`, `digital_twin_setup`

---

### Step 3: Comprehensive Room-by-Room Image Upload

**User Message:**
```
Got it! Now I'll upload photos of each room so you can see what condition everything is in.
[User uploads 25-30 images covering all major rooms across both floors]
```

**Expected AI Response:**
- Acknowledge bulk image upload
- Process each image and link to appropriate room
- Provide summary by floor and by room type
- Highlight rooms in best/worst condition
- Identify common patterns (e.g., outdated fixtures throughout)
- Create initial priority assessment

**Expected Backend Processing:**
```
1. Batch process all images with Gemini Vision
2. Extract room type, materials, fixtures, products from each
3. Use image similarity and room type matching to link images to rooms
4. Create RoomImage, Material, Fixture, Product records
5. Calculate condition scores per room
6. Aggregate patterns across home
7. Generate initial priority ranking
```

**API Endpoints Tested:**
- `POST /api/digital-twin/rooms/bulk-import` (batch processing)
- Image analysis service
- Room matching algorithm

**Expected Analysis Summary:**
```json
{
  "images_processed": 28,
  "rooms_analyzed": 11,
  "overall_condition": "fair",
  "digital_twin_completeness": 0.85,
  
  "condition_by_floor": {
    "floor_1": {
      "overall": "fair",
      "best_room": "Family Room (good condition)",
      "worst_room": "Kitchen (poor condition)",
      "common_issues": ["Outdated finishes", "Worn flooring", "1980s oak trim"]
    },
    "floor_2": {
      "overall": "fair",
      "best_room": "Master Bedroom (good condition)",
      "worst_room": "Master Bath (poor condition)",
      "common_issues": ["Old fixtures", "Dated tile", "Insufficient lighting"]
    }
  },
  
  "materials_inventory": {
    "flooring": {
      "carpet": {"rooms": 4, "condition": "fair", "era": "1990s"},
      "vinyl": {"rooms": 3, "condition": "worn", "era": "1980s"},
      "hardwood": {"rooms": 2, "condition": "good", "era": "original"},
      "tile": {"rooms": 2, "condition": "fair", "era": "1980s"}
    },
    "cabinetry": {
      "oak_honey": {"rooms": 2, "condition": "fair", "era": "1985"}
    },
    "countertops": {
      "laminate": {"rooms": 2, "condition": "worn", "era": "1980s"}
    },
    "paint": {
      "walls": {"condition": "fair", "colors": ["beige", "cream", "off-white"]},
      "trim": {"finish": "oak stain", "condition": "dated"}
    }
  },
  
  "fixtures_inventory": {
    "lighting": {
      "total": 18,
      "outdated": 14,
      "common_style": "brass finish, 1980s style"
    },
    "plumbing": {
      "total": 8,
      "outdated": 6,
      "common_issues": "Low-flow needed, dated finishes"
    }
  },
  
  "appliances_detected": {
    "kitchen": {
      "refrigerator": {"age": "10-15 years", "condition": "functional"},
      "range": {"age": "15+ years", "condition": "fair"},
      "dishwasher": {"age": "15+ years", "condition": "poor"},
      "microwave": {"age": "10+ years", "condition": "functional"}
    }
  },
  
  "immediate_concerns": [
    "Master bathroom shows water damage near tub",
    "Kitchen dishwasher appears non-functional",
    "Several outlets missing cover plates (safety)"
  ],
  
  "style_assessment": {
    "current_era": "1980s-1990s builder grade",
    "dominant_colors": "beige, cream, honey oak",
    "style_tags": ["traditional", "dated", "builder_grade"],
    "modernization_potential": "high"
  }
}
```

**Intent Classification:** `comprehensive_analysis`, `condition_assessment`

---

### Step 4: Priority Recommendation & Budget Allocation

**User Message:**
```
Wow, that's a lot of information! We have about $75,000 to spend over the next 2 years. What should we tackle first? What will give us the best return and livability?
```

**Expected AI Response:**
- Acknowledge budget constraint and timeframe
- Provide tiered priority recommendations:
  - **Immediate (0-3 months)**: Safety, function, urgent repairs
  - **High Priority (3-12 months)**: High-impact value improvements
  - **Medium Priority (1-2 years)**: Quality of life improvements
  - **Low Priority (2+ years)**: Nice-to-haves, aesthetic upgrades
- Include ROI estimates for each project
- Suggest phased approach with budget allocation
- Explain rationale for prioritization

**Expected Recommendation Engine:**
```json
{
  "total_budget": 75000,
  "timeframe_months": 24,
  "strategy": "phased_approach",
  
  "immediate_priorities": {
    "timeframe": "0-3 months",
    "budget_allocation": 5000,
    "projects": [
      {
        "project": "Address Master Bath Water Damage",
        "reason": "Prevent structural damage, mold risk",
        "estimated_cost": {"low": 1500, "high": 3000},
        "urgency": "critical",
        "roi": "n/a - maintenance required",
        "diy_potential": false
      },
      {
        "project": "Replace Kitchen Dishwasher",
        "reason": "Non-functional appliance, daily use impact",
        "estimated_cost": {"low": 600, "high": 1200},
        "urgency": "high",
        "roi": "functional improvement",
        "diy_potential": "partial (delivery install available)"
      },
      {
        "project": "Electrical Safety Items",
        "reason": "Missing outlet covers, potential code violations",
        "estimated_cost": {"low": 200, "high": 500},
        "urgency": "high",
        "roi": "safety",
        "diy_potential": true
      }
    ],
    "total_estimated": "3,300-4,700"
  },
  
  "high_priority": {
    "timeframe": "3-12 months",
    "budget_allocation": 35000,
    "projects": [
      {
        "project": "Kitchen Renovation (Moderate Scope)",
        "reason": "Highest ROI, daily use, major home value driver",
        "estimated_cost": {"low": 20000, "high": 30000},
        "urgency": "high",
        "roi": "75-100% (excellent ROI)",
        "impact_score": 9.5,
        "includes": [
          "New cabinets (painted or refaced)",
          "Quartz countertops",
          "New appliances (stainless steel)",
          "Updated lighting",
          "New backsplash",
          "Paint"
        ],
        "value_engineering": "Consider cabinet refacing vs. replacement to save $5-8K"
      },
      {
        "project": "Master Bathroom Renovation",
        "reason": "High daily use, water damage repair needed, good ROI",
        "estimated_cost": {"low": 12000, "high": 18000},
        "urgency": "medium-high",
        "roi": "60-70%",
        "impact_score": 8.0,
        "includes": [
          "Address water damage",
          "New vanity and countertop",
          "Updated shower/tub",
          "New lighting",
          "Tile update",
          "Modern fixtures"
        ]
      }
    ],
    "total_estimated": "32,000-48,000"
  },
  
  "medium_priority": {
    "timeframe": "12-24 months",
    "budget_allocation": 25000,
    "projects": [
      {
        "project": "Main Floor Flooring Replacement",
        "reason": "Worn condition, high visibility, style update",
        "estimated_cost": {"low": 8000, "high": 12000},
        "urgency": "medium",
        "roi": "50-60%",
        "impact_score": 7.5,
        "scope": "Living room, dining room, foyer, hallway (approx 800 sq ft)",
        "options": ["Luxury vinyl plank", "Engineered hardwood"]
      },
      {
        "project": "Interior Paint - Whole Home",
        "reason": "Transform aesthetic, high impact for cost",
        "estimated_cost": {"low": 5000, "high": 8000},
        "urgency": "medium",
        "roi": "100%+ (low cost, high impact)",
        "impact_score": 8.0,
        "scope": "All rooms, modern neutral palette",
        "diy_potential": true,
        "diy_savings": "$3,000-4,000"
      },
      {
        "project": "Lighting Update - Whole Home",
        "reason": "Dated fixtures throughout, energy efficiency",
        "estimated_cost": {"low": 3000, "high": 5000},
        "urgency": "medium",
        "roi": "70-80%",
        "impact_score": 7.0,
        "scope": "Replace 14 outdated fixtures, add under-cabinet kitchen lighting",
        "diy_potential": "partial"
      },
      {
        "project": "Hall Bathroom Update (Light Refresh)",
        "reason": "Dated but functional, cosmetic improvements",
        "estimated_cost": {"low": 4000, "high": 6000},
        "urgency": "low-medium",
        "roi": "50-60%",
        "impact_score": 6.0,
        "scope": "New vanity, mirror, lighting, paint, hardware"
      }
    ],
    "total_estimated": "20,000-31,000"
  },
  
  "low_priority": {
    "timeframe": "2+ years",
    "budget_allocation": 10000,
    "projects": [
      {
        "project": "Bedroom Carpet Replacement",
        "reason": "Fair condition, low visibility, lower ROI",
        "estimated_cost": {"low": 4000, "high": 6000},
        "urgency": "low",
        "roi": "40-50%"
      },
      {
        "project": "Exterior Updates",
        "reason": "Curb appeal, future consideration",
        "estimated_cost": {"low": 5000, "high": 15000},
        "urgency": "low",
        "roi": "varies by project"
      }
    ],
    "deferred": true
  },
  
  "budget_summary": {
    "immediate": "$3,300-4,700",
    "high_priority": "$32,000-48,000",
    "medium_priority": "$20,000-31,000",
    "total_recommended": "$55,300-83,700",
    "your_budget": "$75,000",
    "recommended_allocation": {
      "year_1": "$40,000-50,000 (kitchen + master bath + immediate)",
      "year_2": "$25,000-30,000 (flooring + paint + lighting + hall bath)"
    },
    "contingency_fund": "$5,000-10,000 (unforeseen issues)"
  },
  
  "phased_timeline": {
    "month_1_3": [
      "Address water damage",
      "Replace dishwasher",
      "Fix electrical safety items",
      "Plan kitchen renovation (design, quotes)"
    ],
    "month_4_6": [
      "Kitchen renovation (5-7 weeks)",
      "Source materials for master bath"
    ],
    "month_7_12": [
      "Master bathroom renovation (3-4 weeks)",
      "Paint touch-ups as needed"
    ],
    "month_13_18": [
      "Main floor flooring replacement",
      "Whole home paint (can DIY to save)"
    ],
    "month_19_24": [
      "Lighting update",
      "Hall bathroom refresh",
      "Remaining punch list items"
    ]
  },
  
  "roi_analysis": {
    "highest_roi_projects": [
      {"project": "Interior Paint", "roi": "100%+", "cost": "$5-8K"},
      {"project": "Kitchen Renovation", "roi": "75-100%", "cost": "$20-30K"},
      {"project": "Lighting Update", "roi": "70-80%", "cost": "$3-5K"}
    ],
    "estimated_home_value_increase": "$60,000-90,000",
    "investment": "$75,000",
    "net_value_creation": "$0-15,000 (break-even to positive)",
    "quality_of_life_improvement": "significant"
  }
}
```

**API Endpoints Tested:**
- `POST /api/intelligence/comprehensive-analysis`
- `POST /api/intelligence/priority-recommendations`
- Smart recommendations agent
- Cost intelligence agent

**Intent Classification:** `priority_planning`, `budget_allocation`, `roi_analysis`

---

### Step 5: Detailed Focus on Top Priority (Kitchen)

**User Message:**
```
This makes total sense. Let's dive deeper into the kitchen renovation. Show me some design options and help me understand exactly what I'm getting for $25,000.
```

**Expected AI Response:**
- Transition to focused kitchen planning
- Retrieve kitchen-specific Digital Twin data
- Offer design styles based on home era and user preferences
- Provide detailed scope breakdown for $25K budget
- Show before/after visualizations (if images available)
- Compare refacing vs. new cabinets with cost deltas

**Expected Kitchen Deep-Dive:**
```json
{
  "room": "Kitchen",
  "current_state": {
    "dimensions": "12' x 15' (180 sq ft)",
    "layout": "Galley style",
    "cabinets": "Honey oak, raised panel, 1985 original",
    "countertops": "Almond laminate, worn edges",
    "appliances": "Mixed ages, non-stainless",
    "flooring": "Vinyl, beige pattern, worn",
    "lighting": "Single overhead + under-cabinet fluorescent",
    "condition_score": 4.2
  },
  
  "budget_scenario_25k": {
    "scope": "Moderate renovation",
    "approach": "Cabinet refacing + strategic upgrades",
    "breakdown": {
      "cabinet_refacing": {
        "cost": 6500,
        "includes": "New doors/drawers, hardware, professional install",
        "vs_replacement": "Saves $4,000-6,000",
        "finish_options": ["White painted", "Gray painted", "Shaker style"]
      },
      "countertops": {
        "cost": 3500,
        "material": "Quartz, 40 sq ft",
        "color_options": ["White with gray veining", "Solid gray", "Marble look"]
      },
      "backsplash": {
        "cost": 1200,
        "material": "Ceramic subway tile, 20 sq ft",
        "options": ["Classic white 3x6", "Gray 3x6", "Herringbone pattern"]
      },
      "appliances": {
        "cost": 4500,
        "package": "Stainless steel suite",
        "includes": ["Refrigerator", "Range", "Dishwasher", "Microwave"],
        "brands": ["Whirlpool mid-range", "GE Profile", "Samsung"]
      },
      "flooring": {
        "cost": 2800,
        "material": "Luxury vinyl plank, 180 sq ft",
        "style": "Wide plank, wood-look",
        "durability": "Waterproof, scratch-resistant"
      },
      "lighting": {
        "cost": 1500,
        "includes": [
          "Recessed LED cans (6-8 lights)",
          "Pendant over sink",
          "Under-cabinet LED strips"
        ]
      },
      "sink_faucet": {
        "cost": 800,
        "includes": "Undermount stainless sink, modern faucet"
      },
      "labor": {
        "cost": 3200,
        "includes": "Installation of all items, electrical updates, plumbing"
      },
      "misc": {
        "cost": 1000,
        "includes": "Permits, disposal, contingency"
      },
      "total": 25000
    },
    
    "design_options": [
      {
        "style": "Modern Farmhouse",
        "description": "White shaker cabinets, butcher block-look LVP, white subway tile",
        "appeal": "Timeless, resale-friendly, bright",
        "image_url": "/generated_images/kitchen_modern_farmhouse.jpg"
      },
      {
        "style": "Contemporary Gray",
        "description": "Gray cabinets, quartz with white veining, gray backsplash",
        "appeal": "Modern, sophisticated, on-trend",
        "image_url": "/generated_images/kitchen_contemporary.jpg"
      },
      {
        "style": "Transitional Two-Tone",
        "description": "White uppers, gray lowers, mixed materials",
        "appeal": "Visual interest, flexible style",
        "image_url": "/generated_images/kitchen_transitional.jpg"
      }
    ],
    
    "upgrade_downgrade_options": {
      "to_reach_20k": [
        "Keep existing appliances if functional (-$4,500)",
        "Paint cabinets instead of reface (-$3,000)",
        "Laminate countertops instead of quartz (-$2,000)"
      ],
      "to_upgrade_30k": [
        "Full cabinet replacement (+$5,000)",
        "Premium appliance package (+$2,500)",
        "Larger format tile, glass backsplash (+$1,000)",
        "Additional cabinet features (soft-close, pull-outs) (+$1,500)"
      ]
    }
  },
  
  "timeline": {
    "planning_phase": "4-6 weeks (design, quotes, material selection)",
    "construction": "5-7 weeks",
    "total": "9-13 weeks from decision to completion"
  },
  
  "expected_outcomes": {
    "condition_score": "8.5/10 (dramatic improvement)",
    "home_value_increase": "$20,000-25,000",
    "roi": "80-100%",
    "livability_improvement": "High - daily use, modern functionality"
  }
}
```

**API Endpoints Tested:**
- Room-specific cost estimation
- Design transformation
- Budget scenario modeling

---

### Step 6: Predictive Maintenance Calendar

**User Message:**
```
This is really helpful! One more thing - can you help me stay on top of maintenance for the whole house? I don't want things to fall apart while I'm renovating other areas.
```

**Expected AI Response:**
- Create comprehensive maintenance schedule
- Based on home age, materials, systems detected
- Prioritize by urgency and cost
- Set up reminders (if system supports)
- Include seasonal maintenance tasks
- Predict major system replacements (HVAC, roof, water heater, etc.)

**Expected Maintenance Calendar:**
```json
{
  "home_age": 40,
  "maintenance_schedule": {
    "immediate_attention": [
      {
        "item": "HVAC System Inspection",
        "reason": "40-year-old home, typical lifespan 15-20 years",
        "action": "Schedule professional inspection",
        "estimated_cost": "$150-250 (inspection)",
        "urgency": "high",
        "predicted_replacement": "May need replacement soon ($5-8K)"
      },
      {
        "item": "Water Heater Age Verification",
        "reason": "Typical lifespan 10-15 years",
        "action": "Check manufacture date, plan replacement if >12 years",
        "estimated_cost": "$1,200-2,000 (replacement)",
        "urgency": "medium-high"
      },
      {
        "item": "Roof Inspection",
        "reason": "40-year-old home, typical shingle lifespan 20-30 years",
        "action": "Professional inspection for leaks, wear",
        "estimated_cost": "$200-400 (inspection)",
        "urgency": "medium",
        "predicted_replacement": "Within 5-10 years ($8-15K)"
      }
    ],
    
    "seasonal_maintenance": {
      "spring": [
        {"task": "HVAC filter replacement", "frequency": "monthly", "cost": "$20"},
        {"task": "Gutter cleaning", "frequency": "2x/year", "cost": "$150 or DIY"},
        {"task": "Exterior caulking inspection", "frequency": "annual", "cost": "$50-200"},
        {"task": "Test sump pump (if applicable)", "frequency": "before rainy season", "cost": "DIY"}
      ],
      "summer": [
        {"task": "AC efficiency check", "frequency": "annual", "cost": "$100-150"},
        {"task": "Deck/patio inspection", "frequency": "annual", "cost": "DIY"},
        {"task": "Window sealing check", "frequency": "annual", "cost": "DIY"}
      ],
      "fall": [
        {"task": "Furnace inspection", "frequency": "annual", "cost": "$100-150"},
        {"task": "Gutter cleaning", "frequency": "2x/year", "cost": "$150 or DIY"},
        {"task": "Chimney inspection (if applicable)", "frequency": "annual", "cost": "$150-300"},
        {"task": "Weatherstripping check", "frequency": "annual", "cost": "$50-100"}
      ],
      "winter": [
        {"task": "HVAC filter replacement", "frequency": "monthly", "cost": "$20"},
        {"task": "Prevent pipe freezing", "frequency": "as needed", "cost": "DIY"},
        {"task": "Snow removal from roof (if heavy)", "frequency": "as needed", "cost": "varies"}
      ]
    },
    
    "monthly_tasks": [
      "HVAC filter replacement",
      "Test smoke/CO detectors",
      "Check for leaks under sinks",
      "Clean range hood filter",
      "Inspect caulking around tubs/showers"
    ],
    
    "major_system_predictions": {
      "hvac": {
        "current_age_estimate": "15-20 years",
        "expected_lifespan": "15-20 years",
        "replacement_window": "1-5 years",
        "estimated_cost": "$5,000-8,000",
        "recommendation": "Schedule inspection now, budget for replacement"
      },
      "water_heater": {
        "current_age_estimate": "10-15 years",
        "expected_lifespan": "10-15 years",
        "replacement_window": "0-3 years",
        "estimated_cost": "$1,200-2,000",
        "recommendation": "Verify age, consider proactive replacement"
      },
      "roof": {
        "current_age_estimate": "15-25 years",
        "expected_lifespan": "20-30 years",
        "replacement_window": "5-15 years",
        "estimated_cost": "$8,000-15,000",
        "recommendation": "Annual inspections, budget in 5-year plan"
      },
      "windows": {
        "current_age": "40 years (original)",
        "expected_lifespan": "20-30 years (past due)",
        "replacement_window": "Consider in 3-5 years",
        "estimated_cost": "$8,000-20,000 (20-30 windows)",
        "recommendation": "Low priority unless energy bills high or drafts noticed"
      }
    },
    
    "annual_maintenance_budget": {
      "routine_maintenance": "$1,500-2,500",
      "inspections": "$500-1,000",
      "emergency_fund": "$2,000-3,000",
      "total_recommended": "$4,000-6,500/year"
    }
  },
  
  "digital_twin_features": {
    "maintenance_reminders": "Set up calendar notifications for upcoming tasks",
    "expense_tracking": "Log all maintenance costs in Digital Twin",
    "warranty_tracking": "Store warranty info for new appliances, materials",
    "service_provider_contacts": "Save preferred contractors, service companies"
  }
}
```

**API Endpoints Tested:**
- Predictive maintenance agent
- Home profile analysis
- System age estimation

**Intent Classification:** `maintenance_planning`, `predictive_analysis`

---

### Step 7: Energy Efficiency Opportunities

**User Message:**
```
Our energy bills seem high. Are there ways to improve efficiency while we're doing these renovations?
```

**Expected AI Response:**
- Assess current energy efficiency based on home age and materials
- Identify efficiency opportunities in planned renovations
- Suggest additional energy upgrades
- Estimate cost vs. savings
- Mention utility rebates and tax credits

**Expected Energy Analysis:**
```json
{
  "current_energy_profile": {
    "home_age": 40,
    "insulation": "Likely original, may be inadequate by modern standards",
    "windows": "Original single or double-pane, not energy efficient",
    "hvac_age": "15-20 years estimated, lower efficiency",
    "lighting": "Mix of incandescent and CFL, not LED",
    "appliances": "Older models, higher energy consumption",
    "estimated_annual_cost": "$2,400-3,200 (regional average for 3,000 sq ft, 1985 home)"
  },
  
  "efficiency_opportunities_in_planned_renovations": {
    "kitchen_renovation": [
      {
        "upgrade": "Energy Star Appliances",
        "additional_cost": "$0-300 (similar price to standard)",
        "annual_savings": "$150-200",
        "payback": "immediate",
        "recommendation": "Strongly recommended"
      },
      {
        "upgrade": "LED Under-Cabinet and Recessed Lighting",
        "additional_cost": "$100-200 over standard",
        "annual_savings": "$50-75",
        "payback": "2-3 years",
        "recommendation": "Include in project"
      }
    ],
    "bathroom_renovations": [
      {
        "upgrade": "Low-Flow Fixtures (WaterSense)",
        "additional_cost": "$0-100 (similar price)",
        "annual_savings": "$80-120 (water + water heating)",
        "payback": "immediate",
        "recommendation": "Strongly recommended"
      },
      {
        "upgrade": "Exhaust Fan with Humidity Sensor",
        "additional_cost": "$100-200",
        "annual_savings": "$30-50",
        "payback": "3-4 years",
        "other_benefits": "Prevents mold, automatic operation"
      }
    ],
    "lighting_update": [
      {
        "upgrade": "LED Throughout (vs. CFL)",
        "additional_cost": "$200-400",
        "annual_savings": "$150-250",
        "payback": "1-2 years",
        "recommendation": "Strongly recommended"
      }
    ]
  },
  
  "additional_efficiency_upgrades": {
    "high_impact": [
      {
        "upgrade": "Attic Insulation Upgrade",
        "estimated_cost": "$1,500-3,000",
        "annual_savings": "$300-500",
        "payback": "3-6 years",
        "roi": "High",
        "priority": "High",
        "notes": "1985 insulation likely inadequate, biggest impact upgrade"
      },
      {
        "upgrade": "Air Sealing (Weatherstripping, Caulking)",
        "estimated_cost": "$300-800 (DIY: $100-200)",
        "annual_savings": "$200-350",
        "payback": "1-3 years",
        "roi": "Very high",
        "priority": "High",
        "diy_friendly": true
      },
      {
        "upgrade": "Smart Thermostat",
        "estimated_cost": "$200-300 (DIY install)",
        "annual_savings": "$100-200",
        "payback": "1-2 years",
        "roi": "High",
        "priority": "High",
        "additional_benefits": "Remote control, usage insights"
      }
    ],
    "medium_impact": [
      {
        "upgrade": "Window Replacement (20-30 windows)",
        "estimated_cost": "$8,000-20,000",
        "annual_savings": "$300-600",
        "payback": "13-40 years",
        "roi": "Low to medium",
        "priority": "Medium (combine with resale/comfort goals)",
        "notes": "Long payback, but improves comfort and resale value"
      },
      {
        "upgrade": "Tankless Water Heater (when replacing)",
        "additional_cost": "$800-1,500 over standard tank",
        "annual_savings": "$100-150",
        "payback": "5-10 years",
        "priority": "Medium",
        "other_benefits": "Endless hot water, space savings"
      }
    ]
  },
  
  "recommended_efficiency_bundle": {
    "include_in_renovations": [
      "Energy Star appliances",
      "LED lighting throughout",
      "Low-flow water fixtures",
      "Humidity-sensing bathroom fans"
    ],
    "standalone_projects": [
      "Attic insulation upgrade ($1,500-3,000)",
      "Air sealing ($300-800)",
      "Smart thermostat ($200-300)"
    ],
    "total_efficiency_investment": "$2,000-4,100",
    "total_annual_savings": "$600-950",
    "payback_period": "2-4 years",
    "20_year_savings": "$12,000-19,000"
  },
  
  "incentives_available": {
    "federal_tax_credits": [
      {"item": "Energy Star appliances", "credit": "varies by product"},
      {"item": "Insulation", "credit": "up to 30% of cost (check current programs)"},
      {"item": "Energy efficient windows", "credit": "up to 30% of cost"}
    ],
    "utility_rebates": [
      {"item": "LED lighting", "rebate": "$5-10 per bulb (check local utility)"},
      {"item": "Smart thermostat", "rebate": "$50-100"},
      {"item": "Energy Star appliances", "rebate": "$50-200 per appliance"}
    ],
    "recommendation": "Check www.energystar.gov and local utility website for current programs"
  }
}
```

**API Endpoints Tested:**
- Energy efficiency analysis
- Cost-benefit calculations
- Incentive database lookup

**Intent Classification:** `energy_efficiency`, `cost_savings_analysis`

---

### Step 8: Document Export & Project Planning

**User Message:**
```
This is incredibly helpful! Can you create a complete document I can share with my spouse and use to plan everything out?
```

**Expected AI Response:**
- Generate comprehensive home assessment report
- Include all analysis, recommendations, timelines, budgets
- Provide multiple format options (PDF, Excel, web view)
- Offer to create separate contractor RFP documents
- Suggest scheduling follow-up conversations for specific projects

**Expected Document Sections:**
```json
{
  "document_type": "comprehensive_home_assessment",
  "title": "Home Assessment & Renovation Roadmap - [Address]",
  "generated_date": "2025-11-08",
  "sections": [
    {
      "title": "Executive Summary",
      "content": "2-page overview of findings, priorities, budget"
    },
    {
      "title": "Digital Twin - Home Profile",
      "content": "Complete home inventory, floor plans, room details"
    },
    {
      "title": "Condition Assessment",
      "content": "Room-by-room analysis with photos, condition scores"
    },
    {
      "title": "Priority Recommendations",
      "content": "Tiered project list with ROI, urgency, cost estimates"
    },
    {
      "title": "24-Month Renovation Plan",
      "content": "Phased timeline with budget allocation"
    },
    {
      "title": "Detailed Project Plans",
      "subsections": [
        "Kitchen Renovation Plan",
        "Master Bathroom Plan",
        "Flooring Replacement Plan",
        "Interior Paint Plan"
      ]
    },
    {
      "title": "Maintenance Calendar",
      "content": "Monthly, seasonal, and annual tasks with estimated costs"
    },
    {
      "title": "Energy Efficiency Roadmap",
      "content": "Efficiency upgrades with cost-benefit analysis"
    },
    {
      "title": "Budget Summary",
      "content": "Complete financial breakdown by project and phase"
    },
    {
      "title": "Appendices",
      "subsections": [
        "Material inventory",
        "Fixture catalog",
        "Contractor checklist",
        "Permit requirements",
        "Incentive programs"
      ]
    }
  ],
  "export_formats": [
    {"format": "PDF", "url": "/exports/home_assessment_20251108.pdf"},
    {"format": "Excel", "url": "/exports/home_assessment_20251108.xlsx"},
    {"format": "Web View", "url": "/dashboard/home-assessment/[home_id]"}
  ]
}
```

**API Endpoints Tested:**
- `POST /api/v1/documents/generate-comprehensive-report`
- Document generation service
- Export utilities

---

### Journey 3 Summary

**Total Conversation Steps:** 8  
**Persona:** Homeowner (New Home Purchase)  
**Budget:** $75,000 over 24 months  
**System Features Validated:**
- ✅ Multi-floor Digital Twin creation
- ✅ Comprehensive room-by-room analysis (11 rooms)
- ✅ Bulk image processing and material detection
- ✅ Priority recommendation engine with ROI analysis
- ✅ Phased budget allocation across 2 years
- ✅ Predictive maintenance calendar
- ✅ Energy efficiency analysis
- ✅ Major system age prediction
- ✅ Comprehensive document generation
- ✅ Multi-project planning and coordination

**API Endpoints Exercised:**
- Multi-floor plan detection and analysis
- Bulk image import and processing
- Comprehensive home intelligence analysis
- Priority ranking algorithms
- Cost estimation across multiple projects
- Predictive maintenance agent
- Energy efficiency calculations
- Document generation (multi-format)

**Key Differentiators from Other Journeys:**
- Multi-floor, whole-home scope (vs. single room)
- Long-term planning (24 months vs. weekend or single project)
- Multiple concurrent projects with dependencies
- Predictive analysis (maintenance, system replacements)
- Strategic prioritization based on ROI and urgency
- Energy efficiency integrated into planning

**Edge Cases to Test:**
- Incomplete room coverage (missing photos for some rooms)
- Budget constraints requiring re-prioritization
- Timeline conflicts between dependent projects
- Hidden issues discovered during renovations
- Changing priorities mid-plan
- Multi-user access (spouse collaboration)
- Tracking actual costs vs. estimates

---

## Journey 4: Contractor Project Scoping

**Persona:** Contractor (Tom, 45, licensed general contractor, 15 years experience)  
**Context:** Initial client consultation for basement finishing project  
**Scenario Type:** `contractor` persona, professional estimation and proposal  
**Complexity Level:** ⭐⭐⭐⭐ (High Complexity)  
**Estimated Duration:** 25-35 minutes of conversation  
**System Features Tested:** Professional measurements, Material/labor estimation, Proposal generation, Permit requirements, Client communication

---

### Step 1: Client Project Brief & Requirements Gathering

**User Message:**
```
I've got a new client who wants to finish their basement. About 800 sq ft, currently unfinished. They want a family room, bedroom, bathroom, and laundry area. I need to scope this out and provide an accurate estimate. Help me make sure I don't miss anything.
```

**Expected AI Response:**
- Acknowledge contractor persona and professional use case
- Provide comprehensive scoping checklist
- Ask critical questions to refine scope:
  - Current basement condition (concrete, framing, moisture issues)
  - Ceiling height
  - Access/egress requirements (windows, doors)
  - Electrical/plumbing current state
  - Code requirements for bedrooms (egress windows)
  - Client budget range
  - Timeline expectations
- Offer to analyze uploaded photos for condition assessment

**Intent Classification:** `contractor_scoping`, `professional_estimation`, `requirements_gathering`

**Suggested Actions:**
```json
[
  {
    "action": "upload_site_photos",
    "label": "Upload Basement Photos",
    "description": "Upload photos for AI-powered condition analysis"
  },
  {
    "action": "create_project_scope",
    "label": "Define Project Scope",
    "description": "Use guided workflow to capture all requirements"
  }
]
```

---

### Step 2: Site Photo Analysis & Condition Assessment

**User Message:**
```
Here are photos I took during the walkthrough. The basement is concrete block walls, poured floor, exposed joists. Ceiling height is 7.5 feet. There's one small window and utilities are roughed in for bathroom.
[Uploads 8-10 basement photos: overall space, walls, ceiling, window, utility rough-ins]
```

**Expected AI Response:**
- Analyze photos for:
  - Structural condition (cracks, moisture, foundation issues)
  - Existing systems (electrical, plumbing, HVAC)
  - Code compliance challenges (ceiling height, egress)
  - Material quantities (framing, drywall, flooring)
  - Potential issues that affect cost
- Flag any red flags or concerns
- Provide preliminary measurements from photos
- Recommend additional investigation areas

**Expected Analysis:**
```json
{
  "space_analysis": {
    "total_area": 800,
    "ceiling_height": 7.5,
    "ceiling_height_note": "Minimum code requirement (7.0 ft), adequate but tight",
    "wall_type": "concrete block",
    "floor": "poured concrete, appears level",
    "structural_condition": "good"
  },
  
  "condition_assessment": {
    "moisture": {
      "status": "no visible signs detected",
      "recommendation": "Verify with moisture meter, check for past water issues",
      "risk": "low",
      "mitigation_cost": "Include vapor barrier in estimate ($500-800)"
    },
    "foundation": {
      "status": "minor hairline cracks visible (typical)",
      "recommendation": "Seal cracks before finishing",
      "cost_impact": "$200-500"
    },
    "insulation": {
      "status": "none detected",
      "requirement": "Required for conditioned space",
      "cost_impact": "$2,000-3,000 for full insulation"
    },
    "overall_condition": "Good - suitable for finishing",
    "major_concerns": "None identified"
  },
  
  "existing_systems": {
    "electrical": {
      "status": "Panel visible, appears adequate capacity",
      "work_needed": "New circuits for lights, outlets, HVAC",
      "estimated_cost": "$3,000-5,000"
    },
    "plumbing": {
      "status": "Rough-in visible for bathroom",
      "work_needed": "Complete bathroom plumbing, laundry hookups",
      "estimated_cost": "$4,000-6,000",
      "note": "Check if ejector pump needed (appears below grade)"
    },
    "hvac": {
      "status": "Existing system visible",
      "work_needed": "Extend ductwork, additional vents",
      "estimated_cost": "$2,500-4,000",
      "note": "Verify existing system capacity"
    }
  },
  
  "code_compliance_considerations": {
    "egress_window": {
      "current": "One small window detected",
      "requirement": "Bedroom requires code-compliant egress window",
      "compliance": "DOES NOT MEET CODE",
      "solution": "Install egress window well",
      "cost_impact": "$3,500-6,000",
      "critical": true,
      "note": "Cannot legally use as bedroom without proper egress"
    },
    "ceiling_height": {
      "current": 7.5,
      "requirement": 7.0,
      "compliance": "MEETS CODE",
      "note": "Tight but acceptable. Consider bulkhead for ductwork."
    },
    "smoke_detectors": {
      "requirement": "Hardwired with battery backup",
      "cost_impact": "$300-500"
    },
    "electrical_outlets": {
      "requirement": "Every 12 ft on walls, GFCI in bathroom/laundry",
      "estimated_count": 20,
      "cost_included": "in electrical estimate"
    }
  },
  
  "material_takeoffs": {
    "framing": {
      "partition_walls": "120 linear feet (estimated)",
      "studs_2x4": "240 studs @ 16 OC",
      "plates": "240 linear feet",
      "estimated_cost": "$800-1,200"
    },
    "drywall": {
      "walls": "1,600 sq ft (estimated)",
      "ceiling": "800 sq ft",
      "total": "2,400 sq ft",
      "sheets_4x8": "75 sheets",
      "estimated_cost": "$2,400-3,600 (material + labor)"
    },
    "flooring": {
      "area": "800 sq ft",
      "recommended": "Luxury vinyl plank (waterproof)",
      "estimated_cost": "$4,000-6,000 (material + install)"
    },
    "doors": {
      "interior_doors": 4,
      "bathroom_door": 1,
      "estimated_cost": "$1,200-2,000"
    }
  },
  
  "critical_questions_for_client": [
    "Have you had any water issues in basement (past or present)?",
    "Do you plan to use bedroom regularly or just occasionally?",
    "What's your budget range? (This helps prioritize finishes)",
    "Any specific timeline/deadline for completion?",
    "Preferences for flooring, paint colors, fixtures?"
  ]
}
```

**API Endpoints Tested:**
- `POST /api/digital-twin/rooms/{room_id}/images` (contractor mode)
- Gemini Vision for structural analysis
- Measurement extraction from images
- Material quantity calculations

**Intent Classification:** `site_analysis`, `condition_assessment`, `contractor_scoping`

---

### Step 3: Comprehensive Cost Estimation

**User Message:**
```
Good catch on the egress window - I'll need to include that. Client's budget is around $60-70K. Give me a detailed breakdown so I can create a proposal. Include materials, labor, permits, everything.
```

**Expected AI Response:**
- Generate professional-grade estimate
- Break down by trade (rough carpentry, electrical, plumbing, HVAC, drywall, flooring, etc.)
- Include labor hours and rates by trade
- Material costs with quantities
- Permit costs and timeline
- Contingency recommendations
- Compare to budget range

**Expected Comprehensive Estimate:**
```json
{
  "project": "Basement Finishing - 800 sq ft",
  "client_budget": "$60,000-70,000",
  "estimate_date": "2025-11-08",
  "valid_for": "30 days",
  
  "scope_summary": {
    "family_room": "450 sq ft",
    "bedroom": "200 sq ft (with code-compliant egress)",
    "bathroom": "80 sq ft (3/4 bath)",
    "laundry": "70 sq ft"
  },
  
  "detailed_estimate": {
    "1_site_prep": {
      "description": "Site preparation and protection",
      "items": [
        {"task": "Temporary protection, dust barriers", "cost": 500},
        {"task": "Debris removal and disposal", "cost": 800},
        {"task": "Foundation crack sealing", "cost": 350}
      ],
      "subtotal": 1650
    },
    
    "2_egress_window": {
      "description": "Code-compliant egress window for bedroom",
      "items": [
        {"task": "Excavation and window well", "labor_hours": 16, "labor_rate": 75, "labor": 1200, "materials": 1500},
        {"task": "Cut concrete, install egress window", "labor_hours": 12, "labor_rate": 85, "labor": 1020, "materials": 1800},
        {"task": "Window well cover and ladder", "cost": 400}
      ],
      "subtotal": 5920,
      "note": "CRITICAL - Required for legal bedroom"
    },
    
    "3_rough_framing": {
      "description": "Framing partition walls, soffits, bulkheads",
      "items": [
        {"task": "Partition wall framing (120 LF)", "labor_hours": 32, "labor_rate": 55, "labor": 1760, "materials": 1100},
        {"task": "Soffit/bulkhead framing", "labor_hours": 16, "labor_rate": 55, "labor": 880, "materials": 400},
        {"task": "Door openings and headers", "labor_hours": 8, "labor_rate": 55, "labor": 440, "materials": 200}
      ],
      "subtotal": 4780
    },
    
    "4_electrical": {
      "description": "Complete electrical system for basement",
      "items": [
        {"task": "New circuits to panel (6 circuits)", "labor_hours": 12, "labor_rate": 95, "labor": 1140, "materials": 800},
        {"task": "Receptacles (20), switches (8)", "labor_hours": 16, "labor_rate": 95, "labor": 1520, "materials": 600},
        {"task": "Lighting fixtures and cans (12)", "labor_hours": 12, "labor_rate": 95, "labor": 1140, "materials": 1200},
        {"task": "Bathroom GFCI, exhaust fan/heat lamp", "labor_hours": 6, "labor_rate": 95, "labor": 570, "materials": 350},
        {"task": "Smoke/CO detectors (hardwired)", "labor_hours": 4, "labor_rate": 95, "labor": 380, "materials": 200}
      ],
      "subtotal": 7900,
      "note": "Licensed electrician required"
    },
    
    "5_plumbing": {
      "description": "Bathroom and laundry plumbing",
      "items": [
        {"task": "Bathroom rough-in completion", "labor_hours": 16, "labor_rate": 90, "labor": 1440, "materials": 800},
        {"task": "Ejector pump system (below grade)", "labor_hours": 8, "labor_rate": 90, "labor": 720, "materials": 1200},
        {"task": "Laundry hookups (washer/dryer)", "labor_hours": 6, "labor_rate": 90, "labor": 540, "materials": 300},
        {"task": "Bathroom fixtures (toilet, vanity, shower)", "labor_hours": 12, "labor_rate": 90, "labor": 1080, "materials": 2000}
      ],
      "subtotal": 8080,
      "note": "Licensed plumber required. Ejector pump critical for below-grade bathroom"
    },
    
    "6_hvac": {
      "description": "Heating and cooling extension",
      "items": [
        {"task": "Ductwork extension (trunk + branches)", "labor_hours": 20, "labor_rate": 75, "labor": 1500, "materials": 1200},
        {"task": "Supply and return vents (6 total)", "labor_hours": 8, "labor_rate": 75, "labor": 600, "materials": 400},
        {"task": "System balancing and testing", "labor_hours": 4, "labor_rate": 75, "labor": 300}
      ],
      "subtotal": 4000,
      "note": "Verify existing HVAC capacity adequate"
    },
    
    "7_insulation": {
      "description": "Insulation and vapor barrier",
      "items": [
        {"task": "Rim joist spray foam insulation", "cost": 800},
        {"task": "Exterior wall insulation (R-13)", "labor_hours": 12, "labor_rate": 45, "labor": 540, "materials": 1000},
        {"task": "Vapor barrier installation", "labor_hours": 8, "labor_rate": 45, "labor": 360, "materials": 300}
      ],
      "subtotal": 3000
    },
    
    "8_drywall": {
      "description": "Drywall installation, taping, finishing",
      "items": [
        {"task": "Drywall installation (2,400 sq ft)", "labor_hours": 32, "labor_rate": 50, "labor": 1600, "materials": 1800},
        {"task": "Taping, mudding, sanding (3 coats)", "labor_hours": 48, "labor_rate": 50, "labor": 2400, "materials": 600},
        {"task": "Texture (if desired)", "labor_hours": 8, "labor_rate": 50, "labor": 400, "materials": 200}
      ],
      "subtotal": 7000
    },
    
    "9_flooring": {
      "description": "Luxury vinyl plank flooring throughout",
      "items": [
        {"task": "Concrete prep and leveling", "labor_hours": 12, "labor_rate": 45, "labor": 540, "materials": 300},
        {"task": "LVP installation (800 sq ft)", "labor_hours": 24, "labor_rate": 55, "labor": 1320, "materials": 3200},
        {"task": "Transitions and baseboards", "labor_hours": 12, "labor_rate": 55, "labor": 660, "materials": 400}
      ],
      "subtotal": 6420
    },
    
    "10_doors_trim": {
      "description": "Interior doors, trim, baseboard",
      "items": [
        {"task": "Interior doors (4) with hardware", "labor_hours": 16, "labor_rate": 55, "labor": 880, "materials": 1400},
        {"task": "Door and window trim", "labor_hours": 16, "labor_rate": 55, "labor": 880, "materials": 600},
        {"task": "Baseboard (220 LF)", "labor_hours": 12, "labor_rate": 55, "labor": 660, "materials": 550}
      ],
      "subtotal": 4970
    },
    
    "11_painting": {
      "description": "Prime and paint all surfaces",
      "items": [
        {"task": "Prime all drywall", "labor_hours": 16, "labor_rate": 45, "labor": 720, "materials": 300},
        {"task": "Paint walls (2 coats)", "labor_hours": 32, "labor_rate": 45, "labor": 1440, "materials": 600},
        {"task": "Paint trim and doors", "labor_hours": 16, "labor_rate": 45, "labor": 720, "materials": 200}
      ],
      "subtotal": 3980
    },
    
    "12_bathroom_finishes": {
      "description": "Bathroom tile, vanity, accessories",
      "items": [
        {"task": "Shower tile installation", "labor_hours": 24, "labor_rate": 65, "labor": 1560, "materials": 1200},
        {"task": "Bathroom vanity and countertop", "cost": 1200},
        {"task": "Mirror, lighting, accessories", "cost": 600}
      ],
      "subtotal": 4560
    },
    
    "13_permits_inspections": {
      "description": "Permits and required inspections",
      "items": [
        {"task": "Building permit", "cost": 800},
        {"task": "Electrical permit and inspection", "cost": 250},
        {"task": "Plumbing permit and inspection", "cost": 200},
        {"task": "Final inspection", "cost": 150}
      ],
      "subtotal": 1400
    }
  },
  
  "cost_summary": {
    "subtotal": 63660,
    "contractor_overhead_profit": 9549,
    "total_before_contingency": 73209,
    "contingency_10_percent": 7321,
    "project_total": 80530
  },
  
  "budget_analysis": {
    "client_budget_max": 70000,
    "estimate": 80530,
    "variance": 10530,
    "status": "OVER BUDGET",
    "value_engineering_needed": true
  },
  
  "value_engineering_options": [
    {
      "option": "Reduce bathroom size to 60 sq ft (shower stall vs tub)",
      "savings": "$2,000-3,000",
      "impact": "Low - still functional bathroom"
    },
    {
      "option": "Use standard fixtures vs. mid-grade",
      "savings": "$1,500-2,000",
      "impact": "Low - quality still good"
    },
    {
      "option": "Paint-grade trim vs. stain-grade",
      "savings": "$800-1,200",
      "impact": "Very low - painted trim is popular"
    },
    {
      "option": "Client provide some fixtures (lights, hardware)",
      "savings": "$1,000-1,500",
      "impact": "Low - just coordination needed"
    },
    {
      "option": "Reduce family room size by 50 sq ft",
      "savings": "$2,500-3,500",
      "impact": "Medium - less living space"
    },
    {
      "total_potential_savings": "$7,800-11,200",
      "revised_estimate": "$69,300-72,700",
      "recommendation": "Combination of first 4 options brings project to budget"
    }
  ],
  
  "timeline": {
    "permits": "2-4 weeks",
    "construction": {
      "site_prep": "1 week",
      "egress_window": "1 week",
      "rough_framing": "1 week",
      "rough_electrical_plumbing_hvac": "2 weeks",
      "insulation_inspection": "3 days",
      "drywall": "1.5 weeks",
      "painting": "1 week",
      "flooring": "1 week",
      "trim_doors": "1 week",
      "finish_electrical_plumbing": "1 week",
      "final_details": "3 days",
      "final_inspection": "1 day"
    },
    "total_construction": "10-12 weeks",
    "total_project": "12-16 weeks (including permits)"
  },
  
  "payment_schedule": {
    "deposit": "20% ($16,100) - upon contract signing",
    "permit_approval": "20% ($16,100) - when permits obtained",
    "rough_in_complete": "30% ($24,150) - after framing, mechanical inspections",
    "substantial_completion": "25% ($20,125) - drywall, paint, flooring done",
    "final_payment": "5% ($4,025) - after final inspection, walkthrough"
  },
  
  "assumptions": [
    "No asbestos or lead paint remediation required",
    "Existing HVAC system has adequate capacity",
    "No structural modifications required",
    "Normal soil conditions for egress window excavation",
    "Standard municipal inspections and timelines",
    "Mid-grade fixtures and finishes",
    "Client provides paint color selections timely"
  ],
  
  "exclusions": [
    "Furniture and window treatments",
    "Low-voltage (cable, data, security)",
    "Exterior landscaping around egress window (beyond window well)",
    "Septic system modifications (if applicable)",
    "Appliances (washer/dryer)"
  ]
}
```

**API Endpoints Tested:**
- `POST /api/intelligence/cost-estimate` (contractor mode with trade breakdown)
- Labor rate database by region and trade
- Material cost database
- Permit cost estimation by jurisdiction

**Intent Classification:** `professional_estimation`, `proposal_generation`

---

### Step 4: Proposal Document Generation

**User Message:**
```
Perfect! Now generate a professional proposal I can send to the client. Make it look good and include everything we discussed.
```

**Expected AI Response:**
- Generate formal proposal document
- Professional formatting with company branding placeholder
- All estimates, timelines, payment terms
- Terms and conditions
- Scope of work details
- Multiple format options (PDF, Word)
- Editable sections for contractor customization

**Expected Proposal Structure:**
```markdown
# Professional Basement Finishing Proposal

**Prepared For:** [Client Name]  
**Property Address:** [Address]  
**Prepared By:** [Contractor Company]  
**Date:** November 8, 2025  
**Proposal Valid:** 30 Days

---

## Executive Summary

Thank you for the opportunity to provide this proposal for finishing your basement. This project will transform approximately 800 square feet of unfinished space into a beautiful and functional living area including a family room, bedroom, 3/4 bathroom, and laundry area.

**Project Investment:** $69,300 - $72,700 (after value engineering)  
**Timeline:** 12-16 weeks (including permit approval)  
**Warranty:** 1-year workmanship warranty on all labor

---

## Scope of Work

### Family Room (450 sq ft)
- Framed walls with insulation and vapor barrier
- Drywall, tape, texture, prime, and paint
- Luxury vinyl plank flooring
- Recessed LED lighting (6 cans)
- Electrical outlets per code
- Baseboard trim

### Bedroom (200 sq ft) - **Code-Compliant**
- Code-compliant egress window with window well
- Framed walls with insulation
- Drywall, tape, texture, prime, and paint
- Luxury vinyl plank flooring
- Recessed LED lighting (3 cans)
- Hardwired smoke detector
- Closet (if space allows)
- Baseboard trim

### 3/4 Bathroom (60 sq ft)
- Complete rough-in plumbing (if not existing)
- Ejector pump system for below-grade drainage
- Tile shower with glass door
- Standard toilet
- 36" vanity with countertop and mirror
- Exhaust fan with heat lamp
- GFCI electrical outlets
- Ceramic tile flooring
- Lighting fixture

### Laundry Area (70 sq ft)
- Washer/dryer hookups
- Utility sink (optional)
- Adequate electrical and lighting
- Luxury vinyl plank flooring

### General
- All work performed to code
- All required permits and inspections
- Professional cleanup throughout project
- Final walkthrough and punchlist

---

## Detailed Investment

[Insert cost breakdown table from estimate]

**Total Investment:** $72,700
*(Note: Final cost depends on material selections and any changes to scope)*

---

## Timeline

- **Weeks 1-4:** Permit approval and material ordering
- **Weeks 5-8:** Rough framing, egress window, mechanical rough-ins
- **Weeks 9-12:** Drywall, painting, flooring installation
- **Weeks 13-16:** Finish work, final inspections

**Start Date:** Upon permit approval and 20% deposit  
**Substantial Completion:** 10-12 weeks after start  
**Final Completion:** 12-16 weeks total

---

## Payment Schedule

1. **20% Deposit** ($14,540) - Upon contract signing
2. **20% Progress** ($14,540) - When permits obtained
3. **30% Progress** ($21,810) - After rough-in inspections pass
4. **25% Progress** ($18,175) - Upon substantial completion
5. **5% Final** ($3,635) - After final inspection and client approval

---

## What's Included

✅ All labor and materials specified  
✅ Building, electrical, and plumbing permits  
✅ All required inspections  
✅ Professional project management  
✅ Daily cleanup  
✅ 1-year workmanship warranty  
✅ Licensed and insured contractor  

---

## What's Not Included

❌ Furniture and decor  
❌ Window treatments  
❌ Washer/dryer appliances  
❌ Low-voltage wiring (data, cable, security)  
❌ Exterior landscaping  

---

## Next Steps

1. **Review this proposal** and let me know if you have questions
2. **Schedule a follow-up meeting** to discuss any adjustments
3. **Sign contract and provide deposit** to begin permit process
4. **Select finishes** (paint colors, flooring, fixtures) from provided options
5. **Project kickoff** once permits are approved

---

## Why Choose Us

- ✓ Licensed and insured (License #[NUMBER])
- ✓ 15+ years of experience in basement finishing
- ✓ [X] local references available
- ✓ Clear communication throughout project
- ✓ Quality workmanship guaranteed
- ✓ On-time, on-budget commitment

---

**Questions?** Contact us at [phone] or [email]

**Acceptance:** This proposal is valid for 30 days from the date above.

---

*Terms & Conditions apply - see attached contract for full details*
```

**API Endpoints Tested:**
- `POST /api/v1/documents/generate-contractor-proposal`
- Document template engine
- PDF generation service

---

### Step 5: Client Questions & Modifications

**User Message:**
```
Client wants to know: can we add a wet bar in the family room area? And they want to upgrade the bathroom to a full bath with a tub. How does that change things?
```

**Expected AI Response:**
- Calculate change order costs
- Analyze space impact
- Update timeline
- Revise proposal sections
- Provide pros/cons of changes

**Expected Change Order Analysis:**
```json
{
  "change_requests": [
    {
      "change": "Add wet bar in family room",
      "description": "Small bar area with sink, cabinets, countertop",
      "space_required": "6-8 linear feet",
      "impact_on_family_room": "Reduces usable space by ~40 sq ft",
      "additional_costs": {
        "cabinets_countertop": 1500,
        "sink_faucet": 400,
        "plumbing_rough_in": 1200,
        "plumbing_finish": 600,
        "electrical": 300,
        "total": 4000
      },
      "timeline_impact": "+1 week",
      "recommendation": "Good value-add if client entertains. Consider bar fridge space."
    },
    {
      "change": "Upgrade bathroom to full bath with tub",
      "description": "Change from shower stall to tub/shower combo",
      "space_required": "Increase bathroom from 60 to 80 sq ft",
      "impact_on_other_rooms": "Reduces family room by 20 sq ft",
      "additional_costs": {
        "increased_framing": 300,
        "additional_plumbing": 800,
        "tub_vs_shower": 600,
        "additional_tile": 800,
        "increased_waterproofing": 400,
        "total": 2900
      },
      "timeline_impact": "+3-5 days",
      "recommendation": "Better resale value with full bath. Minimal space sacrifice."
    }
  ],
  
  "revised_estimate": {
    "original_estimate": 72700,
    "wet_bar_addition": 4000,
    "full_bath_upgrade": 2900,
    "revised_total": 79600,
    "vs_original_budget": 9600,
    "status": "Still over original $70K budget",
    "options": [
      "Proceed at $79,600 (revised budget)",
      "Add wet bar only ($76,700)",
      "Add full bath only ($75,600)",
      "Keep original scope ($72,700)"
    ]
  },
  
  "recommendation": "Full bath upgrade strongly recommended for resale value. Wet bar is nice-to-have. Suggest prioritizing full bath, consider wet bar as future addition if budget allows."
}
```

**Intent Classification:** `change_order`, `scope_modification`

---

### Step 6: Permit Requirements & Code Compliance

**User Message:**
```
What permits do I actually need, and what will the inspector be looking for? I want to make sure we pass everything first time.
```

**Expected AI Response:**
- Detailed permit requirements by jurisdiction
- Inspection checkpoint list
- Code compliance checklist by trade
- Common inspection failures and how to avoid
- Timeline for permit approval

**Expected Permit & Inspection Guide:**
```json
{
  "permits_required": {
    "building_permit": {
      "cost": 800,
      "required_documents": [
        "Site plan showing basement layout",
        "Floor plan with room dimensions",
        "Electrical plan",
        "Plumbing plan",
        "Egress window details and specs",
        "HVAC load calculation"
      ],
      "approval_timeline": "2-4 weeks",
      "inspection_stages": ["Rough-in", "Insulation", "Final"]
    },
    "electrical_permit": {
      "cost": 250,
      "requirements": "Licensed electrician must pull permit",
      "inspections": ["Rough-in", "Final"]
    },
    "plumbing_permit": {
      "cost": 200,
      "requirements": "Licensed plumber must pull permit",
      "inspections": ["Rough-in", "Final"]
    },
    "mechanical_hvac": {
      "cost": "May be included in building permit",
      "requirements": "Load calculation to verify capacity"
    }
  },
  
  "inspection_checkpoints": {
    "rough_framing_inspection": {
      "when": "After framing complete, before drywall",
      "inspector_checks": [
        "Wall framing 16\" OC, proper headers",
        "Egress window meets code (net clear opening ≥5.7 sq ft, ≥24\" height, ≥20\" width, sill ≤44\" from floor)",
        "Bedroom has proper egress access",
        "Fire blocking in walls",
        "Ceiling height ≥7 feet throughout"
      ],
      "common_failures": [
        "Egress window too small or high",
        "Missing fire blocking",
        "Improper headers over openings"
      ],
      "how_to_pass": "Verify egress window specs BEFORE ordering. Use proper lumber for headers. Install fire blocking per code."
    },
    
    "electrical_rough_inspection": {
      "when": "After wiring complete, before drywall",
      "inspector_checks": [
        "Wire sizing appropriate for loads",
        "Proper box fill calculations",
        "GFCI protection in bathroom and laundry",
        "AFCI protection on bedroom circuits (per NEC)",
        "Outlets every 12 feet on walls",
        "Hardwired smoke detectors interconnected",
        "Proper grounding throughout"
      ],
      "common_failures": [
        "Missing AFCI protection",
        "Improper GFCI locations",
        "Box overfill",
        "Insufficient outlets"
      ],
      "how_to_pass": "Use licensed electrician. Follow NEC 2020 or local code. Test all GFCI/AFCI before inspection."
    },
    
    "plumbing_rough_inspection": {
      "when": "After pipes installed, before concealment",
      "inspector_checks": [
        "Proper pipe sizing and materials",
        "Adequate slope on drain lines",
        "Proper venting (may require ejector pump vent)",
        "Water supply lines secured",
        "Pressure test (if required)",
        "Ejector pump properly installed"
      ],
      "common_failures": [
        "Improper venting",
        "Insufficient drain slope",
        "Ejector pump issues"
      ],
      "how_to_pass": "Use licensed plumber. Verify ejector pump meets code. Pressure test before inspection."
    },
    
    "insulation_inspection": {
      "when": "After insulation installed, before drywall",
      "inspector_checks": [
        "Proper R-value for climate zone",
        "Vapor barrier correctly installed",
        "No gaps or compression",
        "Proper air sealing"
      ],
      "common_failures": [
        "Insufficient R-value",
        "Gaps around pipes/wires",
        "Vapor barrier on wrong side"
      ],
      "how_to_pass": "Check local R-value requirements. Install vapor barrier toward warm side. Seal all penetrations."
    },
    
    "final_inspection": {
      "when": "After all work complete",
      "inspector_checks": [
        "All electrical, plumbing, HVAC functional",
        "Smoke and CO detectors operational and interconnected",
        "Egress window operable with proper emergency escape",
        "Handrails if stairs modified",
        "All work matches approved plans",
        "Proper ventilation (bathroom exhaust, etc.)",
        "Fire-rated drywall if required (furnace room wall)"
      ],
      "common_failures": [
        "Non-functional smoke detectors",
        "Egress window painted shut or blocked",
        "Missing CO detectors",
        "Poor workmanship"
      ],
      "how_to_pass": "Test everything before calling for inspection. Ensure egress window operates smoothly. Have documentation ready."
    }
  },
  
  "code_compliance_checklist": {
    "egress_requirements": {
      "bedroom_egress_window": {
        "min_net_clear_opening": "5.7 sq ft",
        "min_height": "24 inches",
        "min_width": "20 inches",
        "max_sill_height": "44 inches from floor",
        "operable": "Must open from inside without tools",
        "window_well": "Required if below grade",
        "window_well_dimensions": "Min 9 sq ft, extends 36\" from foundation",
        "ladder_or_steps": "Required if well depth >44 inches"
      }
    },
    "ceiling_height": {
      "minimum": "7 feet (habitable space)",
      "under_beams": "6 feet 4 inches allowed for max 50% of area",
      "bathroom": "6 feet 8 inches minimum"
    },
    "electrical": {
      "receptacles": "Max 12 feet spacing on walls, 6 feet from doorways",
      "gfci_required": "Bathrooms, laundry, within 6 feet of sinks",
      "afci_required": "Bedrooms, family rooms per NEC",
      "lighting": "Every room must have switched lighting",
      "smoke_co_detectors": "Hardwired, interconnected, in bedroom and outside sleeping areas"
    },
    "plumbing": {
      "bathroom": "Toilet, sink minimum. Shower or tub recommended.",
      "venting": "All fixtures must be properly vented",
      "ejector_pump": "Required for below-grade fixtures",
      "water_heater": "Proper venting if in finished space"
    },
    "fire_safety": {
      "smoke_detectors": "Required in bedroom, outside bedroom, per floor",
      "co_detectors": "Required per floor if fuel-burning appliances",
      "fire_blocking": "Required in walls at 10-foot intervals vertically",
      "furnace_room": "Type X drywall if shared with living space"
    }
  },
  
  "pro_tips": [
    "Schedule inspections early in the day for faster turnaround",
    "Have approved plans on-site during inspections",
    "Address any concerns immediately before inspector leaves",
    "Take photos of rough-ins before closing up walls",
    "Keep a log of all inspection dates and results",
    "Build good relationship with inspector - ask questions",
    "Never cover work before inspection if required",
    "Double-check egress window dimensions before ordering"
  ]
}
```

**API Endpoints Tested:**
- Compliance & code agent
- Jurisdiction-specific permit database
- Inspection requirement lookup

**Intent Classification:** `permit_requirements`, `code_compliance`, `inspection_preparation`

---

### Journey 4 Summary

**Total Conversation Steps:** 6  
**Persona:** Contractor (Professional)  
**Project Type:** Basement finishing, $60-80K  
**System Features Validated:**
- ✅ Professional site analysis from photos
- ✅ Structural and condition assessment
- ✅ Code compliance checking (egress, electrical, plumbing)
- ✅ Detailed trade-by-trade cost estimation
- ✅ Material quantity takeoffs
- ✅ Labor hour calculations by trade
- ✅ Professional proposal generation
- ✅ Change order management
- ✅ Permit requirements by jurisdiction
- ✅ Inspection checkpoint guidance
- ✅ Value engineering recommendations

**API Endpoints Exercised:**
- Contractor-mode image analysis
- Professional cost estimation with trade breakdown
- Permit and compliance databases
- Proposal document generation
- Change order calculations

**Key Differentiators from Other Journeys:**
- Professional contractor perspective (vs. homeowner)
- Trade-specific breakdowns and timelines
- Permit and code compliance focus
- Professional proposal formatting
- Change order management
- Client communication considerations
- Inspection preparation guidance

**Edge Cases to Test:**
- Discovering structural issues during analysis
- Code violations in existing space
- Client budget significantly under actual cost
- Permit delays or rejections
- Failed inspections and rework
- Scope creep and change orders
- Material availability issues
- Subcontractor scheduling conflicts

---

## Journey 5: Investment Property ROI Analysis

**Persona:** Property Investor (Lisa, 38, owns 4 rental properties, looking to optimize portfolio)  
**Context:** Recently acquired a duplex, needs to decide which renovations maximize rental income vs. cost  
**Scenario Type:** `investor` persona (business-focused), ROI-driven decision making  
**Complexity Level:** ⭐⭐⭐⭐⭐ (Highest Complexity)  
**Estimated Duration:** 35-50 minutes of conversation  
**System Features Tested:** Multi-property management, ROI calculations, Rental value optimization, Comparative analysis, Investment prioritization

---

### Step 1: Investment Property Assessment Initiation

**User Message:**
```
Hi! I just closed on a duplex - two 2-bed/1-bath units, built in 1975. It's rentable now but pretty dated. I need to figure out which improvements will give me the best ROI and increase my rental income. Can you help me analyze this as an investment?
```

**Expected AI Response:**
- Recognize investor/business persona and adjust language accordingly
- Explain investment-focused analysis approach
- Key metrics we'll calculate:
  - Current vs. post-renovation rental value
  - Renovation cost vs. rental income increase
  - Payback period and cash-on-cash return
  - Market rent comparisons
  - Tenant quality improvements
- Request property details: location, current rents, condition, target tenant demographic
- Offer to create Digital Twin for detailed analysis

**Intent Classification:** `investment_analysis`, `roi_calculation`, `rental_optimization`

**Suggested Actions:**
```json
[
  {
    "action": "create_investment_property_profile",
    "label": "Set Up Investment Property",
    "description": "Enter property financials, current rents, and market data"
  },
  {
    "action": "upload_property_images",
    "label": "Upload Unit Photos",
    "description": "Analyze condition and identify value-add opportunities"
  }
]
```

---

### Step 2: Property & Financial Data Input

**User Message:**
```
It's in a college town - good rental market. Built 1975, each unit is 850 sq ft. Current rents are $950/month per unit ($1,900 total). Market rate for updated units is $1,200-1,300. I bought it for $285K with 25% down. Here are photos of both units.
[Uploads 15-20 photos showing both units - kitchens, baths, living areas, bedrooms]
```

**Expected AI Response:**
- Create investment property profile
- Analyze photos for condition and improvement opportunities
- Calculate current financial metrics (cap rate, cash flow, etc.)
- Identify renovation opportunities ranked by ROI
- Compare current condition to market standards

**Expected Investment Analysis:**
```json
{
  "property_profile": {
    "type": "Duplex (2 units)",
    "location_type": "College town",
    "year_built": 1975,
    "total_sq_ft": 1700,
    "unit_1": "2 bed / 1 bath, 850 sq ft",
    "unit_2": "2 bed / 1 bath, 850 sq ft"
  },
  
  "current_financials": {
    "purchase_price": 285000,
    "down_payment_25_percent": 71250,
    "loan_amount": 213750,
    "estimated_monthly_payment": 1425,
    "current_monthly_rent": 1900,
    "monthly_cash_flow": 475,
    "annual_rental_income": 22800,
    "estimated_annual_expenses": {
      "mortgage": 17100,
      "property_tax": 4275,
      "insurance": 1200,
      "maintenance_reserve_10_percent": 2280,
      "vacancy_5_percent": 1140,
      "total": 25995
    },
    "annual_cash_flow": -3195,
    "cash_on_cash_return": "-4.5% (currently negative)",
    "cap_rate": "5.4% (based on rent/purchase price)",
    "status": "Below-market rents, cash flow negative"
  },
  
  "condition_assessment": {
    "unit_1": {
      "overall_condition": "fair",
      "condition_score": 5.5,
      "kitchen": {
        "condition": "dated, functional",
        "materials": "Laminate counters, vinyl floor, oak cabinets",
        "era": "1990s",
        "issues": "Worn counters, outdated appliances"
      },
      "bathroom": {
        "condition": "fair",
        "materials": "Cultured marble vanity, fiberglass tub/shower",
        "era": "1980s-90s",
        "issues": "Dated fixtures, caulking needs repair"
      },
      "living_areas": {
        "condition": "fair",
        "flooring": "Worn carpet",
        "paint": "Beige, scuffed walls",
        "issues": "General wear and tear"
      },
      "appliances": {
        "condition": "functional but old",
        "age_estimate": "10-15 years",
        "issues": "Non-matching, inefficient"
      }
    },
    "unit_2": {
      "overall_condition": "fair",
      "condition_score": 5.8,
      "similar_to_unit_1": true,
      "notes": "Slightly better maintained, same vintage"
    },
    "common_areas": {
      "exterior": "Needs paint",
      "landscaping": "Basic, needs enhancement"
    }
  },
  
  "market_analysis": {
    "current_rent_per_unit": 950,
    "market_rate_updated_units": 1250,
    "market_rate_premium_units": 1350,
    "current_vs_market": "24-30% below market for updated units",
    "rental_upside": "$300-400 per unit/month",
    "annual_upside": "$7,200-9,600 total",
    "target_tenant": "College students, young professionals",
    "tenant_priorities": [
      "Modern kitchens",
      "Updated bathrooms",
      "In-unit laundry",
      "Modern finishes (not builder-grade 1990s)",
      "Good wi-fi/connectivity"
    ]
  },
  
  "competitive_positioning": {
    "current_rating": "C+ (budget option)",
    "after_renovation_potential": "A- (premium college housing)",
    "vacancy_risk": "Current: Medium | After renovation: Low",
    "tenant_quality": "Current: Mixed | After renovation: Higher quality, lower turnover"
  }
}
```

**API Endpoints Tested:**
- Investment property profile creation
- Multi-unit Digital Twin
- Rental market analysis
- Financial metrics calculation

**Intent Classification:** `investment_profile`, `market_analysis`

---

### Step 3: ROI-Ranked Renovation Recommendations

**User Message:**
```
Okay, so what should I renovate? I want the best bang for my buck. I'm willing to invest if the payback is reasonable.
```

**Expected AI Response:**
- Provide renovation options ranked by ROI
- Calculate payback period for each
- Show rental income impact
- Consider tenant turnover reduction
- Recommend renovation packages (budget/moderate/premium)

**Expected ROI Analysis:**
```json
{
  "renovation_options_ranked_by_roi": [
    {
      "rank": 1,
      "renovation": "Interior Paint & Deep Clean (Both Units)",
      "estimated_cost": 3500,
      "cost_per_unit": 1750,
      "rental_increase_per_unit": 50,
      "annual_income_increase": 1200,
      "roi": "34%",
      "payback_period": "2.9 years",
      "impact": "High visual impact, low cost",
      "tenant_appeal": "High - fresh, clean feel",
      "recommendation": "MUST DO - Foundation for any other improvements"
    },
    {
      "rank": 2,
      "renovation": "Kitchen Refresh (Counters, Backsplash, Paint Cabinets, Hardware)",
      "estimated_cost": 8000,
      "cost_per_unit": 4000,
      "rental_increase_per_unit": 100,
      "annual_income_increase": 2400,
      "roi": "30%",
      "payback_period": "3.3 years",
      "impact": "Highest tenant priority for college market",
      "tenant_appeal": "Very high - modern kitchen is key differentiator",
      "recommendation": "STRONGLY RECOMMENDED - Kitchen drives rental value"
    },
    {
      "rank": 3,
      "renovation": "Luxury Vinyl Plank Flooring (Replace all carpet)",
      "estimated_cost": 10000,
      "cost_per_unit": 5000,
      "rental_increase_per_unit": 75,
      "annual_income_increase": 1800,
      "roi": "18%",
      "payback_period": "5.6 years",
      "impact": "Durable, modern, easy to maintain",
      "tenant_appeal": "High - LVP preferred over carpet",
      "additional_benefit": "Lower turnover costs, easier cleaning between tenants",
      "recommendation": "RECOMMENDED - Pays for itself in reduced turnover costs"
    },
    {
      "rank": 4,
      "renovation": "Bathroom Update (Vanity, Mirror, Light, Hardware, Paint)",
      "estimated_cost": 4000,
      "cost_per_unit": 2000,
      "rental_increase_per_unit": 40,
      "annual_income_increase": 960,
      "roi": "24%",
      "payback_period": "4.2 years",
      "impact": "Moderate - functional bathroom gets refreshed look",
      "tenant_appeal": "Moderate - improves overall unit feel",
      "recommendation": "RECOMMENDED - Good value for modest investment"
    },
    {
      "rank": 5,
      "renovation": "Appliance Package (Matching Stainless Steel)",
      "estimated_cost": 5000,
      "cost_per_unit": 2500,
      "rental_increase_per_unit": 50,
      "annual_income_increase": 1200,
      "roi": "24%",
      "payback_period": "4.2 years",
      "impact": "Modern look, energy efficiency",
      "tenant_appeal": "High - stainless is expected in updated units",
      "additional_benefit": "Lower maintenance, warranty coverage",
      "recommendation": "RECOMMENDED - Pairs well with kitchen refresh"
    },
    {
      "rank": 6,
      "renovation": "In-Unit Washer/Dryer (Stackable)",
      "estimated_cost": 6000,
      "cost_per_unit": 3000,
      "rental_increase_per_unit": 100,
      "annual_income_increase": 2400,
      "roi": "40%",
      "payback_period": "2.5 years",
      "impact": "VERY HIGH - Major competitive advantage",
      "tenant_appeal": "EXTREMELY HIGH - Top priority for young renters",
      "feasibility": "DEPENDS - Need hookups, space, plumbing/electrical",
      "recommendation": "HIGHLY RECOMMENDED IF FEASIBLE - Huge differentiator",
      "caveat": "Check if units have space and hookups. May need plumbing/electrical work."
    },
    {
      "rank": 7,
      "renovation": "Lighting Upgrade (Modern Fixtures Throughout)",
      "estimated_cost": 3000,
      "cost_per_unit": 1500,
      "rental_increase_per_unit": 25,
      "annual_income_increase": 600,
      "roi": "20%",
      "payback_period": "5.0 years",
      "impact": "Moderate - improves ambiance",
      "tenant_appeal": "Moderate - noticed but not primary driver",
      "recommendation": "OPTIONAL - Nice-to-have, do if budget allows"
    },
    {
      "rank": 8,
      "renovation": "Exterior Paint & Curb Appeal",
      "estimated_cost": 5000,
      "rental_increase_per_unit": 25,
      "annual_income_increase": 600,
      "roi": "12%",
      "payback_period": "8.3 years",
      "impact": "Moderate - first impression",
      "tenant_appeal": "Moderate - helps with showing/marketing",
      "recommendation": "OPTIONAL - Consider for tenant quality, not rental rate"
    }
  ],
  
  "recommended_renovation_packages": {
    "budget_package": {
      "name": "Essential Refresh",
      "total_cost": 17500,
      "included": [
        "Paint & deep clean both units",
        "Kitchen refresh (counters, cabinets)",
        "Bathroom updates",
        "Basic lighting improvements"
      ],
      "rental_increase_per_unit": 215,
      "new_rent_per_unit": 1165,
      "annual_income_increase": 5160,
      "payback_period": "3.4 years",
      "roi": "29.5%",
      "pros": "Affordable, fast ROI, significant improvement",
      "cons": "Doesn't address flooring or appliances",
      "recommendation": "Good if budget-constrained or testing market"
    },
    
    "moderate_package": {
      "name": "Competitive Positioning",
      "total_cost": 30500,
      "included": [
        "Paint & deep clean",
        "Kitchen refresh with new appliances",
        "Bathroom updates",
        "LVP flooring throughout",
        "Lighting upgrade"
      ],
      "rental_increase_per_unit": 340,
      "new_rent_per_unit": 1290,
      "annual_income_increase": 8160,
      "payback_period": "3.7 years",
      "roi": "26.7%",
      "pros": "Comprehensive update, competitive with market, durable materials",
      "cons": "Higher upfront cost",
      "recommendation": "BEST VALUE - Positions property as premium option",
      "market_position": "Top 20% of college rentals in area"
    },
    
    "premium_package": {
      "name": "Maximum Value",
      "total_cost": 36500,
      "included": [
        "Everything in moderate package",
        "In-unit washer/dryer (if feasible)",
        "Exterior paint"
      ],
      "rental_increase_per_unit": 465,
      "new_rent_per_unit": 1415,
      "annual_income_increase": 11160,
      "payback_period": "3.3 years",
      "roi": "30.6%",
      "pros": "Premium positioning, lowest vacancy risk, highest tenant quality",
      "cons": "Highest upfront investment",
      "recommendation": "BEST IF FEASIBLE - In-unit laundry is game-changer",
      "market_position": "Top 10% of college rentals, can command premium",
      "additional_benefits": [
        "Longer tenant retention (students stay all 4 years)",
        "Attracts professional roommates, not just students",
        "Lower turnover costs",
        "Premium positioning allows rent growth"
      ]
    }
  },
  
  "financial_projections": {
    "current_state": {
      "annual_rental_income": 22800,
      "annual_cash_flow": -3195,
      "cash_on_cash_return": "-4.5%"
    },
    "after_budget_package": {
      "renovation_cost": 17500,
      "total_investment": 88750,
      "annual_rental_income": 27960,
      "annual_cash_flow": 1965,
      "cash_on_cash_return": "2.2%",
      "improvement": "Positive cash flow achieved"
    },
    "after_moderate_package": {
      "renovation_cost": 30500,
      "total_investment": 101750,
      "annual_rental_income": 30960,
      "annual_cash_flow": 4965,
      "cash_on_cash_return": "4.9%",
      "improvement": "Strong positive cash flow, 9.4% increase vs. current"
    },
    "after_premium_package": {
      "renovation_cost": 36500,
      "total_investment": 107750,
      "annual_rental_income": 33960,
      "annual_cash_flow": 7965,
      "cash_on_cash_return": "7.4%",
      "improvement": "Excellent cash flow, 11.9% return",
      "comparison": "Matches or exceeds typical stock market returns"
    }
  },
  
  "recommendation": {
    "suggested_package": "Moderate Package ($30,500)",
    "rationale": [
      "Achieves competitive positioning without over-improving",
      "3.7-year payback is reasonable for rental property",
      "26.7% ROI is excellent",
      "Addresses all major tenant priorities (kitchen, bath, flooring)",
      "Durable materials reduce turnover costs",
      "Positions for future rent growth"
    ],
    "upgrade_consideration": "If units have space and hookups for W/D, upgrade to Premium Package for exceptional returns",
    "implementation": "Renovate one unit first, rent it out, then do second unit with any refinements"
  }
}
```

**API Endpoints Tested:**
- Investment ROI calculation engine
- Rental market comparison data
- Multi-package scenario modeling
- Cash flow projections

**Intent Classification:** `roi_analysis`, `investment_optimization`

---

### Step 4: Phased Implementation Strategy

**User Message:**
```
I like the moderate package, but can I do one unit at a time? I don't want both units vacant during renovation.
```

**Expected AI Response:**
- Recommend phased approach
- Unit 1 vs. Unit 2 timing strategy
- Cash flow management during renovations
- Tenant communication strategies
- Lessons learned approach

**Expected Phased Strategy:**
```json
{
  "phased_implementation": {
    "approach": "One unit at a time to maintain cash flow",
    "benefits": [
      "Continuous rental income from one unit",
      "Test improvements before replicating",
      "Learn from first unit, refine second",
      "Spread capital expenditure over time"
    ],
    
    "phase_1_unit_1": {
      "timing": "Start immediately (assuming current lease allows)",
      "duration": "4-6 weeks",
      "rent_impact": "Lose $950/month during renovation (~$1,500 total)",
      "strategy": [
        "Wait for current lease to end (or offer early termination incentive)",
        "Complete all renovations while vacant",
        "Market at new rate ($1,290) before completion",
        "Target move-in date to minimize vacancy"
      ],
      "renovation_cost": 15250,
      "marketing_photos": "Use Unit 1 as showcase for leasing Unit 2 (when time comes)",
      "expected_outcome": "$340/month rent increase = $4,080/year"
    },
    
    "phase_2_unit_2": {
      "timing": "3-6 months after Unit 1 (at natural lease end)",
      "duration": "4-6 weeks",
      "rent_impact": "Lose $950/month during renovation (~$1,500 total)",
      "advantages": [
        "Unit 1 cash flow helps fund Unit 2",
        "Refinements based on Unit 1 experience",
        "Proven rent increase gives confidence",
        "Can use Unit 1 photos for marketing"
      ],
      "renovation_cost": 15250,
      "expected_outcome": "$340/month rent increase = $4,080/year"
    },
    
    "total_timeline": "6-12 months for full implementation",
    "total_renovation_cost": 30500,
    "total_renovation_vacancy_cost": 3000,
    "total_investment": 33500,
    "annual_income_increase": 8160,
    "payback_including_vacancy": "4.1 years (still excellent)"
  },
  
  "cash_flow_management": {
    "month_1_3": {
      "unit_1_status": "Under renovation",
      "unit_1_rent": 0,
      "unit_2_status": "Occupied at old rate",
      "unit_2_rent": 950,
      "total_monthly_income": 950,
      "mortgage_payment": 1425,
      "monthly_cash_flow": -475,
      "strategy": "Use reserves or Unit 2 rent to cover shortfall"
    },
    "month_4_6": {
      "unit_1_status": "Occupied at new rate",
      "unit_1_rent": 1290,
      "unit_2_status": "Occupied at old rate (awaiting lease end)",
      "unit_2_rent": 950,
      "total_monthly_income": 2240,
      "monthly_cash_flow": 815,
      "strategy": "Bank extra cash flow for Unit 2 renovation"
    },
    "month_7_9": {
      "unit_1_status": "Occupied at new rate",
      "unit_1_rent": 1290,
      "unit_2_status": "Under renovation",
      "unit_2_rent": 0,
      "total_monthly_income": 1290,
      "monthly_cash_flow": -135,
      "strategy": "Use saved cash flow from months 4-6"
    },
    "month_10_plus": {
      "unit_1_status": "Occupied at new rate",
      "unit_1_rent": 1290,
      "unit_2_status": "Occupied at new rate",
      "unit_2_rent": 1290,
      "total_monthly_income": 2580,
      "monthly_cash_flow": 1155,
      "annual_cash_flow": 13860,
      "outcome": "Strong positive cash flow achieved!"
    }
  },
  
  "tenant_communication_strategies": {
    "current_tenants": {
      "approach": "Professional, transparent communication",
      "options": [
        {
          "option": "Natural lease end",
          "description": "Wait for lease to expire, give 60-day notice",
          "pros": "No conflict, normal process",
          "cons": "May delay timeline"
        },
        {
          "option": "Early termination incentive",
          "description": "Offer $500-1000 incentive to vacate early",
          "pros": "Control timing, goodwill",
          "cons": "Additional cost",
          "when_to_use": "If you want to start immediately"
        },
        {
          "option": "Month-to-month option",
          "description": "Convert to month-to-month, give 30-day notice",
          "pros": "Flexibility",
          "cons": "Check local landlord-tenant laws"
        }
      ]
    },
    "marketing_renovated_units": {
      "strategy": "Premium positioning with professional presentation",
      "tactics": [
        "Professional photos (worth $200-300 investment)",
        "Highlight modern upgrades in listing",
        "Virtual tour or video walkthrough",
        "Higher security deposit justifies higher rent",
        "Target young professionals in addition to students",
        "Emphasize durability, modern amenities"
      ],
      "pricing_strategy": {
        "initial_list": "$1,350 (test market ceiling)",
        "negotiation_floor": "$1,250 (still good ROI)",
        "target": "$1,290 (moderate package projection)"
      }
    }
  },
  
  "lessons_learned_approach": {
    "after_unit_1": [
      "Review actual costs vs. estimates",
      "Assess contractor performance",
      "Get tenant feedback on upgrades",
      "Verify rent increase achieved",
      "Identify any missed items or improvements",
      "Adjust Unit 2 scope if needed"
    ],
    "potential_refinements": [
      "Better material selections based on tenant preferences",
      "Timing adjustments for faster turnaround",
      "Cost savings from bulk material purchases",
      "Additional value-adds that tenants mentioned"
    ]
  }
}
```

**API Endpoints Tested:**
- Phased project planning
- Cash flow modeling over time
- Tenant management strategies

**Intent Classification:** `phased_implementation`, `cash_flow_management`

---

### Step 5: Long-Term Portfolio Strategy

**User Message:**
```
This is really helpful! I have 4 properties total. How do I decide which properties to invest in first? And what's my long-term strategy here?
```

**Expected AI Response:**
- Multi-property portfolio analysis
- Prioritization framework across properties
- Long-term wealth-building strategy
- Refinancing opportunities
- Portfolio optimization

**Expected Portfolio Strategy:**
```json
{
  "portfolio_overview": {
    "total_properties": 4,
    "property_1_duplex": {
      "type": "Duplex (subject property)",
      "current_value": 285000,
      "current_cash_flow": -3195,
      "renovation_potential": "High (as discussed)",
      "priority_ranking": 1,
      "rationale": "Highest upside, negative cash flow needs fixing"
    },
    "property_2_3_4": {
      "status": "Need assessment",
      "recommendation": "Upload data for comprehensive portfolio analysis"
    }
  },
  
  "prioritization_framework": {
    "rank_properties_by": [
      {
        "factor": "Cash Flow Status",
        "weight": "High",
        "logic": "Fix negative/low cash flow properties first",
        "action": "Prioritize properties with negative or <3% COC return"
      },
      {
        "factor": "Renovation ROI",
        "weight": "High",
        "logic": "Higher ROI renovations get priority",
        "action": "Focus on properties where ROI >20%"
      },
      {
        "factor": "Market Rent Gap",
        "weight": "High",
        "logic": "Biggest below-market gaps = biggest opportunity",
        "action": "Properties renting 20%+ below market get priority"
      },
      {
        "factor": "Tenant Turnover Risk",
        "weight": "Medium",
        "logic": "Properties with upcoming lease ends = opportunity",
        "action": "Time renovations to natural turnover"
      },
      {
        "factor": "Capital Available",
        "weight": "Medium",
        "logic": "Don't overextend financially",
        "action": "Sequence projects based on cash flow from previous renovations"
      },
      {
        "factor": "Market Conditions",
        "weight": "Medium",
        "logic": "Renovate before hot rental seasons",
        "action": "College towns: complete before August. General market: before spring."
      }
    ],
    
    "decision_matrix_for_portfolio": {
      "tier_1_urgent": "Negative cash flow OR major deferred maintenance OR >30% below market rent",
      "tier_2_high_priority": "Low cash flow (<3%) OR 20-30% below market rent OR high-ROI renovation opportunities",
      "tier_3_optimization": "Positive cash flow but optimization opportunities exist",
      "tier_4_stable": "Performing well, maintain and monitor"
    }
  },
  
  "long_term_wealth_building_strategy": {
    "years_1_2_renovation_phase": {
      "goal": "Optimize existing portfolio cash flow and value",
      "actions": [
        "Renovate underperforming properties (like this duplex)",
        "Increase rents to market rates",
        "Improve tenant quality and retention",
        "Build cash reserves from improved cash flow"
      ],
      "target_metrics": {
        "portfolio_cash_on_cash": ">6% average across all properties",
        "occupancy_rate": ">95%",
        "tenant_quality": "Higher income, lower turnover"
      }
    },
    
    "years_3_5_growth_phase": {
      "goal": "Leverage equity for expansion",
      "actions": [
        "Refinance appreciated properties (pull cash out)",
        "Use increased cash flow + pulled equity for down payments",
        "Acquire 1-2 additional properties",
        "Focus on properties with similar value-add potential"
      ],
      "example_refinance_scenario": {
        "duplex_current_value": 285000,
        "duplex_after_renovation": 325000,
        "equity_created": 40000,
        "current_loan_balance": 213750,
        "new_loan_75_percent_ltv": 243750,
        "cash_out_available": 30000,
        "use_for": "Down payment on property #5",
        "new_payment_increase": "~$200/month",
        "but_rent_increase": "$680/month",
        "net_benefit": "$480/month additional cash flow + $30K cash out"
      }
    },
    
    "years_6_10_scaling_phase": {
      "goal": "Build significant portfolio (10-15 units)",
      "actions": [
        "Repeat refinance and acquire strategy",
        "Consider larger multifamily (4-8 units) for efficiency",
        "Potentially hire property manager when portfolio >10 units",
        "Focus on cash flow and debt paydown"
      ],
      "target_portfolio": {
        "properties": "6-8 properties",
        "total_units": "12-15 rental units",
        "annual_cash_flow": "$40-60K/year",
        "portfolio_value": "$1.5-2M",
        "equity": "$600-800K"
      }
    },
    
    "years_10_plus_wealth_phase": {
      "goal": "Financial independence from real estate cash flow",
      "actions": [
        "Continue acquiring opportunistically",
        "Pay down mortgages aggressively",
        "Consider transitioning to management oversight role",
        "Plan for retirement income from portfolio"
      ],
      "potential_outcomes": {
        "option_1_cashflow": "Keep leveraged, $80-100K/year passive income",
        "option_2_payoff": "Pay off mortgages, $150-200K/year gross rental income",
        "option_3_sell": "Exit strategy: Sell portfolio for $2-3M+ cash"
      }
    }
  },
  
  "immediate_next_steps": {
    "month_1": [
      "Complete duplex Unit 1 renovation ($15,250)",
      "Gather data on other 3 properties for portfolio analysis",
      "Research mortgage rates for potential refinance in 12-24 months"
    ],
    "month_2_3": [
      "Market and lease Unit 1 at new rate",
      "Analyze other properties' renovation potential",
      "Build cash reserves for Unit 2 renovation"
    ],
    "month_4_6": [
      "Complete duplex Unit 2 renovation",
      "Prioritize next property based on portfolio analysis",
      "Review overall portfolio performance"
    ]
  },
  
  "advanced_strategies": {
    "cost_segregation": {
      "description": "Tax strategy to accelerate depreciation",
      "benefit": "Significant tax deductions in early years",
      "when": "After renovations complete, property stabilized",
      "typical_cost": "$800-1,500 per property",
      "typical_tax_savings": "$3,000-8,000 in first year"
    },
    "1031_exchange": {
      "description": "Defer capital gains taxes when selling",
      "benefit": "Roll proceeds into larger property tax-free",
      "when": "When ready to sell and upgrade portfolio",
      "requirement": "Must identify replacement property within 45 days, close within 180 days"
    },
    "brrrr_strategy": {
      "description": "Buy, Renovate, Rent, Refinance, Repeat",
      "benefit": "Recycle capital infinitely",
      "fit": "This is essentially what you're doing! Keep it up.",
      "key": "Find value-add properties, force appreciation through renovation"
    }
  }
}
```

**API Endpoints Tested:**
- Multi-property portfolio management
- Long-term financial projections
- Refinance scenario modeling
- Investment strategy recommendations

**Intent Classification:** `portfolio_strategy`, `wealth_building`, `long_term_planning`

---

### Step 6: Tax & Financial Optimization

**User Message:**
```
What about taxes? How do I minimize my tax burden and maximize returns?
```

**Expected AI Response:**
- Tax optimization strategies for rental properties
- Depreciation and expense categorization
- Entity structure recommendations
- When to consult CPA/tax professional

**Expected Tax Guidance:**
```json
{
  "tax_optimization_strategies": {
    "depreciation": {
      "residential_rental_property": "27.5 year straight-line depreciation",
      "duplex_example": {
        "building_value": 228000,
        "land_value_not_depreciable": 57000,
        "annual_depreciation": 8291,
        "tax_benefit_at_24_percent_bracket": 1990
      },
      "after_renovation": {
        "additional_depreciable_basis": 30500,
        "annual_depreciation_increase": 1109,
        "additional_tax_benefit": 266
      },
      "total_annual_tax_benefit": 2256
    },
    
    "cost_segregation_study": {
      "description": "Accelerate depreciation by categorizing components into shorter life classes",
      "example_breakdown": {
        "5_year_property": "Appliances, carpeting",
        "15_year_property": "Land improvements, landscaping",
        "27_5_year_property": "Building structure"
      },
      "benefit": "Front-load depreciation deductions in early years",
      "typical_result": "$10-20K additional depreciation in year 1",
      "cost": "$800-1,500 per property",
      "roi_on_study": "Usually positive in year 1 alone",
      "recommendation": "Do after $30K renovation completes - captures improvement depreciation"
    },
    
    "deductible_expenses": {
      "operating_expenses_fully_deductible": [
        "Mortgage interest",
        "Property taxes",
        "Insurance",
        "Repairs and maintenance",
        "Property management fees",
        "HOA fees",
        "Utilities (if landlord-paid)",
        "Advertising for tenants",
        "Legal and professional fees",
        "Travel to property",
        "Home office (if dedicated space for rental business)"
      ],
      "capital_improvements_depreciated": [
        "Renovations (depreciated over 27.5 years)",
        "New appliances (5-year depreciation)",
        "HVAC replacement",
        "Roof replacement"
      ],
      "common_mistakes": [
        "Not tracking mileage to properties",
        "Missing professional fees (CPA, lawyer)",
        "Not deducting home office",
        "Mixing personal and business expenses"
      ]
    },
    
    "entity_structure": {
      "current_likely_structure": "Personal name (Schedule E on 1040)",
      "pros_of_current": "Simple, no entity formation costs",
      "cons_of_current": "Personal liability exposure, less tax optimization",
      
      "llc_option": {
        "description": "Form LLC to hold properties",
        "liability_protection": "Yes - shields personal assets",
        "tax_treatment": "Pass-through (same as Schedule E)",
        "cost": "$500-2,000 (formation + annual fees)",
        "when_to_consider": "3+ properties OR property value >$500K OR high-risk tenants",
        "recommendation": "Consider after property 3-4, consult attorney"
      },
      
      "s_corp_option": {
        "description": "Property management company as S-Corp",
        "benefit": "Potential self-employment tax savings if you actively manage",
        "complexity": "High - requires payroll, separate tax return",
        "when_to_consider": "Property management is full-time business (10+ properties)",
        "recommendation": "Not yet relevant, revisit at 8-10 properties"
      }
    },
    
    "qualified_business_income_deduction": {
      "description": "20% deduction on qualified rental income (Section 199A)",
      "eligibility": "Rental activity must be a 'trade or business'",
      "safe_harbor": ">250 hours per year on rental activities",
      "benefit_example": {
        "net_rental_income": 20000,
        "qbi_deduction_20_percent": 4000,
        "taxable_income_reduced_to": 16000,
        "tax_savings_at_24_percent": 960
      },
      "documentation": "Track all hours spent on property management, maintenance, etc.",
      "recommendation": "Keep detailed log of rental activities to qualify"
    },
    
    "tax_planning_actions": {
      "immediate": [
        "Open separate bank account for rental income/expenses",
        "Start expense tracking system (QuickBooks, Stessa, or spreadsheet)",
        "Save all receipts for renovation materials and labor",
        "Log mileage to/from properties"
      ],
      "before_tax_season": [
        "Consult CPA specializing in real estate",
        "Discuss cost segregation study post-renovation",
        "Review entity structure needs",
        "Ensure QBI deduction eligibility"
      ],
      "ongoing": [
        "Quarterly estimated tax payments (if profitable)",
        "Monthly expense categorization",
        "Annual depreciation schedule updates",
        "Track rental activity hours for QBI"
      ]
    }
  },
  
  "financial_optimization": {
    "cash_flow_maximization": [
      "Minimize vacancy through quality renovations",
      "Proper tenant screening to reduce turnover",
      "Preventive maintenance to avoid costly repairs",
      "Annual rent increases at lease renewal (2-3% typical)"
    ],
    "debt_optimization": [
      "Refinance when rates drop 0.75%+ from current",
      "Consider 15-year mortgage for properties with strong cash flow (faster equity build)",
      "Shop for lower insurance rates annually",
      "Appeal property tax assessments if overvalued"
    ],
    "wealth_building_focus": [
      "Balance cash flow and appreciation",
      "Reinvest profits into additional properties",
      "Build 6-month cash reserve for portfolio",
      "Pay down debt in later years for retirement income"
    ]
  },
  
  "when_to_hire_professionals": {
    "cpa_tax_professional": {
      "when": "Now (for first tax season with rentals)",
      "cost": "$500-1,500/year",
      "value": "Tax savings typically exceed cost",
      "specialization": "Find CPA with real estate investor focus"
    },
    "property_manager": {
      "when": "5+ properties OR out-of-state properties OR full-time job",
      "cost": "8-10% of monthly rent",
      "value": "Time savings, professional tenant management",
      "roi": "Worth it if your time is valuable or properties are distant"
    },
    "real_estate_attorney": {
      "when": "Forming LLC, complex tenant issues, legal questions",
      "cost": "$200-400/hour",
      "value": "Asset protection, legal compliance"
    },
    "bookkeeper": {
      "when": "6+ properties OR prefer to outsource",
      "cost": "$100-300/month",
      "value": "Clean books for tax time, better financial visibility"
    }
  }
}
```

**API Endpoints Tested:**
- Tax calculation and optimization
- Entity structure recommendations
- Professional service recommendations

**Intent Classification:** `tax_optimization`, `financial_planning`

---

### Journey 5 Summary

**Total Conversation Steps:** 6  
**Persona:** Property Investor  
**Property Type:** Duplex (2 units, $285K purchase)  
**Investment:** $30,500 renovation  
**Expected Returns:** 26.7% ROI, 3.7-year payback, $8,160 annual income increase  

**System Features Validated:**
- ✅ Investment property financial analysis
- ✅ Multi-unit Digital Twin and management
- ✅ Rental market comparison and positioning
- ✅ ROI-ranked renovation recommendations
- ✅ Multi-scenario package modeling (budget/moderate/premium)
- ✅ Cash flow projections over time
- ✅ Phased implementation planning
- ✅ Portfolio prioritization framework
- ✅ Long-term wealth-building strategy
- ✅ Refinance scenario modeling
- ✅ Tax optimization strategies
- ✅ Professional service recommendations

**API Endpoints Exercised:**
- Investment property profile creation
- Financial metrics calculations (cash flow, COC, cap rate)
- Rental market analysis and comps
- ROI ranking algorithms
- Multi-scenario cost estimation
- Cash flow modeling
- Tax calculation and optimization
- Portfolio management tools

**Key Differentiators from Other Journeys:**
- Business/investment focus (vs. personal homeowner)
- ROI-driven decision making (vs. aesthetic preferences)
- Cash flow and financial metrics emphasis
- Multi-property portfolio perspective
- Phased implementation for cash flow management
- Long-term wealth-building strategy
- Tax optimization integration
- Professional service recommendations

**Edge Cases to Test:**
- Properties with negative cash flow (urgent fixes)
- Market rent uncertainty (how to validate projections)
- Renovation cost overruns impact on ROI
- Tenant resistance to rent increases
- Unexpected deferred maintenance discovered
- Market downturn during renovation
- Financing challenges for next acquisition
- Portfolio-wide emergency (multiple properties need attention)

---

## Edge Cases & Error Scenarios

This section documents challenging scenarios to test system robustness, error handling, and fallback behaviors.

---

### Category 1: Missing or Incomplete Data

#### Scenario 1.1: No Floor Plan Available
**User Input:**
```
I don't have a floor plan. Can you still help me?
```

**Expected Behavior:**
- Gracefully acknowledge limitation
- Offer alternatives: room-by-room photo analysis, manual dimension input, professional measurement services
- Proceed with image-based Digital Twin creation
- Note reduced accuracy in cost estimates

**System Response Should Include:**
- "No problem! While a floor plan provides the most accurate dimensions, I can work with room photos and your input."
- Request photos with visible room dimensions or reference objects
- Offer to calculate based on estimated dimensions with disclaimer

---

#### Scenario 1.2: Poor Quality Images
**User Input:**
```
[Uploads dark, blurry, or partial room images]
```

**Expected Behavior:**
- AI detects low confidence in analysis
- Politely request better quality images
- Provide guidance on photo best practices
- Offer to work with what's available with caveats

**System Response:**
```json
{
  "image_quality_assessment": "low",
  "confidence_score": 0.45,
  "issues_detected": ["insufficient lighting", "blur", "obstructed view"],
  "recommendation": "For the most accurate analysis, please upload clearer photos",
  "photo_tips": [
    "Use good lighting (open blinds, turn on lights)",
    "Hold camera steady",
    "Capture full room from corner",
    "Include close-ups of materials and fixtures",
    "Take photos during daytime if possible"
  ],
  "fallback_option": "I can provide a general assessment based on these images, but recommendations may be less precise"
}
```

---

#### Scenario 1.3: Ambiguous Room Type
**User Input:**
```
[Uploads image of room that could be bedroom, office, or flex space]
```

**Expected Behavior:**
- AI flags ambiguity
- Ask clarifying question
- Offer multiple categorization options
- Let user confirm intended use

**System Response:**
```
I see this space could be used in several ways. How do you plan to use this room?
- Bedroom
- Home Office
- Flex Space / Multi-Purpose Room
- Guest Room
- Other (please specify)

Your intended use will help me provide more relevant recommendations.
```

---

### Category 2: Budget Constraints

#### Scenario 2.1: Budget Way Below Estimate
**User Input:**
```
You estimated $50K for the kitchen, but I only have $20K. What can I do?
```

**Expected Behavior:**
- Acknowledge constraint without judgment
- Provide value engineering options
- Rank changes by impact
- Offer phased approach
- Suggest DIY alternatives
- Be realistic about tradeoffs

**System Response Structure:**
```json
{
  "budget_gap": 30000,
  "options": [
    {
      "approach": "Phased Renovation",
      "phase_1": "Cosmetic refresh now ($20K): paint, hardware, lighting, backsplash",
      "phase_2": "Major items later: cabinets, counters, appliances when budget allows",
      "pros": "Immediate improvement, spread costs over time",
      "cons": "Not a complete transformation yet"
    },
    {
      "approach": "Value Engineering",
      "changes": [
        "Paint cabinets instead of replace (-$8K)",
        "Laminate counters instead of quartz (-$2K)",
        "Keep appliances if functional (-$4K)",
        "DIY demolition and painting (-$3K)"
      ],
      "revised_total": "$33K (still over, need more cuts)"
    },
    {
      "approach": "Strategic Priorities",
      "focus": "Spend $20K on highest-impact items only",
      "include": ["Cabinet refresh", "New counters", "Backsplash", "Paint"],
      "defer": ["Appliances", "Flooring", "Major layout changes"],
      "honest_assessment": "Won't achieve full transformation, but noticeable improvement"
    }
  ],
  "recommendation": "I suggest the phased approach. Start with cosmetic refresh ($20K), enjoy the improvement, then save for phase 2. This gives you time to plan and budget."
}
```

---

#### Scenario 2.2: Unlimited Budget / Luxury Request
**User Input:**
```
Money is no object. I want the absolute best, top-of-the-line everything.
```

**Expected Behavior:**
- Provide premium options
- Still educate on value and ROI
- Warn against over-improvement for area
- Suggest where premium makes sense vs. overkill

**System Response:**
```
Wonderful! Even with an unlimited budget, I recommend strategic investments. Some premium upgrades have amazing impact, others don't justify the cost even if you can afford them.

**High-Value Premium Upgrades:**
- Professional-grade appliances (if you cook often)
- Premium natural stone counters (Calacatta marble, quartzite)
- Custom cabinetry with premium features
- High-end lighting design

**Lower-Value Premium Upgrades:**
- Gold-plated fixtures (aesthetic only, no functional benefit)
- Exotic woods that need high maintenance
- Overly trendy designs (may feel dated quickly)

**My Recommendation:** Focus on timeless quality and craftsmanship rather than just "most expensive." I can design a stunning kitchen at $80-100K that outperforms a $150K kitchen with poor choices.
```

---

### Category 3: Unclear or Complex Intent

#### Scenario 3.1: Vague Request
**User Input:**
```
Make my house better.
```

**Expected Behavior:**
- Ask clarifying questions
- Offer structured assessment approach
- Guide user to specific goals

**System Response:**
```
I'd love to help! To provide the best recommendations, let me ask a few questions:

1. **What's prompting this?**
   - Planning to sell soon?
   - Just moved in and want to personalize?
   - Lived here a while and ready for an update?
   
2. **Any specific areas or issues bothering you?**
   - Outdated kitchen or bathrooms?
   - Cramped or dark spaces?
   - Worn flooring or damaged areas?

3. **Budget range?**
   - Under $10K (cosmetic improvements)
   - $10-50K (moderate upgrades)
   - $50K+ (major renovations)

4. **Timeline?**
   - ASAP (urgent issues)
   - This year (planned improvements)
   - Multi-year plan (strategic upgrades)

Or, I can start with a comprehensive home assessment if you upload your floor plan and some photos. I'll analyze everything and provide prioritized recommendations!
```

---

#### Scenario 3.2: Conflicting Requirements
**User Input:**
```
I want a modern kitchen with traditional elements, but also farmhouse style, and keep it minimalist. Budget is $30K but I want custom everything.
```

**Expected Behavior:**
- Identify contradictions
- Educate on style definitions
- Help user prioritize and clarify
- Suggest cohesive direction

**System Response:**
```
I notice some conflicting elements in your vision. Let me help clarify:

**Style Conflict:**
- "Modern" = clean lines, minimal ornamentation
- "Traditional" = ornate details, classic elements
- "Farmhouse" = rustic, textured, warm
- "Minimalist" = very few elements, monochromatic

**These can sometimes blend, but need a clear hierarchy. Let me suggest some cohesive directions:**

1. **Modern Farmhouse** (most popular blend)
   - Clean lines (modern) + warm materials (farmhouse)
   - White shaker cabinets, butcher block, simple hardware
   - Budget-friendly and achievable

2. **Transitional** (modern + traditional)
   - Mix contemporary and classic
   - Gray cabinets, marble counters, mixed metals
   - Balanced and timeless

3. **Scandinavian Minimalist** (minimalist + warmth)
   - Minimal but not cold
   - Light woods, white, natural materials
   - Clean but inviting

**Budget Reality Check:**
Custom everything typically starts at $60K+. At $30K, we'll need to use:
- Semi-custom or RTA cabinets (not fully custom)
- Quartz or butcher block (not natural stone)
- Mid-grade appliances

**Which style direction appeals most? I'll design around that with your budget.**
```

---

### Category 4: Technical Limitations

#### Scenario 4.1: Unsupported Request
**User Input:**
```
Can you design my outdoor kitchen and pool area?
```

**Expected Behavior:**
- Acknowledge request
- Clarify current capabilities
- Offer partial assistance
- Suggest resources for full solution

**System Response:**
```
I specialize in interior home improvements and renovations. While I can't fully design outdoor kitchens and pools (those require specialized landscape architecture and pool engineering), I can help with:

**What I Can Help With:**
- Budget estimation for outdoor kitchen components
- Product recommendations for outdoor appliances
- Connection to indoor spaces (doors, windows, access)
- Material suggestions (weather-resistant options)
- General layout ideas

**What Requires Specialists:**
- Pool engineering and permitting
- Outdoor plumbing and gas lines
- Structural elements (pergolas, pavilions)
- Landscaping design
- Drainage and grading

**Recommendation:** Let me help you plan the budget and general requirements, then I can help you prepare a briefing for a landscape architect and pool contractor.
```

---

#### Scenario 4.2: Local Jurisdiction Information Unavailable
**User Input:**
```
What are the specific permit requirements for my addition in [small town]?
```

**Expected Behavior:**
- Provide general information
- Acknowledge limitation
- Direct to official sources

**System Response:**
```
Permit requirements vary significantly by jurisdiction. Here's what I can provide:

**General Requirements (typical for most areas):**
- Building permit for structural changes
- Electrical permit
- Plumbing permit (if applicable)
- Zoning/setback compliance

**For [Your Specific Town]:**
I don't have access to [Town Name]'s specific codes. You'll need to:
1. Contact [Town Name] Building Department
   - Call or visit their office
   - Ask for "residential addition requirements"
2. Check their website: [try searching "Town Name building permits"]
3. Hire a local contractor familiar with local codes

**What I Can Help With:**
- Preparing documentation for permit application
- General code compliance (IRC, NEC, IPC)
- Typical permit costs to budget for
- Questions to ask the building department

Would you like me to create a permit checklist and questions to ask your local building department?
```

---

### Category 5: System Errors & Recovery

#### Scenario 5.1: AI Analysis Failure
**Simulation:**
```
Gemini Vision API returns error or very low confidence
```

**Expected Behavior:**
- Graceful fallback
- Transparent communication
- Alternative paths forward

**System Response:**
```
I'm having difficulty analyzing that image. This could be due to:
- Image quality or format issues
- Temporary service interruption
- Unusual room configuration

**Let's try this:**
1. **Re-upload** the image (sometimes this resolves it)
2. **Try a different photo** of the same room
3. **Manual input** - Tell me about the room and I'll help based on your description
4. **Skip for now** - We can continue with other rooms and come back to this

Which would you prefer? I'm still here to help!
```

---

#### Scenario 5.2: Cost Estimation Uncertainty
**User Input:**
```
How much to renovate my bathroom?
```

**Expected Behavior:**
- Request necessary details
- Provide range with clear assumptions
- Explain variability factors

**System Response:**
```
Bathroom renovations can range from $5K (refresh) to $50K+ (luxury gut renovation). To give you an accurate estimate, I need some info:

**Critical Details:**
1. **Bathroom size?** (small 5x7, medium 8x10, large 10x12+)
2. **Current condition?** (photos help!)
3. **Scope desired?**
   - Cosmetic refresh (paint, fixtures, hardware)
   - Moderate (vanity, flooring, tile, fixtures)
   - Full gut (everything new including layout)
4. **Moving plumbing/walls?** (adds significant cost)

**Without photos, here's a rough range:**
- Small bathroom refresh: $5-10K
- Medium bathroom moderate reno: $12-20K
- Medium bathroom gut reno: $20-35K

**Cost Varies By:**
- Labor rates in your region (can vary 30-50%)
- Material selections (builder vs. premium)
- Existing conditions (surprises behind walls)
- Accessibility (2nd floor harder than 1st)

Upload photos for a more accurate estimate!
```

---

### Category 6: Conversation Management

#### Scenario 6.1: Topic Switching Mid-Conversation
**User Input:**
```
[Started discussing kitchen renovation, suddenly asks about refinancing mortgage]
```

**Expected Behavior:**
- Acknowledge topic change
- Offer to save kitchen progress
- Clarify if separate topic or related

**System Response:**
```
I notice you're shifting from kitchen renovation to mortgage refinancing. No problem!

**Options:**
1. **Save kitchen progress** - I'll remember everything we discussed. We can return to it anytime.
2. **Refinance helps kitchen?** - If you're refinancing to fund the renovation, I can help you understand how much to borrow based on our estimated costs.
3. **Separate topic** - I can help with general home finance questions, but mortgage rates and refinancing are best handled by a mortgage broker. I can help you prepare the information they'll need.

Which applies to your situation?
```

---

#### Scenario 6.2: Repeat Questions
**User Input:**
```
How much will the kitchen cost? [Asked 3rd time]
```

**Expected Behavior:**
- Recognize repetition
- Check if previous answer was unclear
- Provide summary with context

**System Response:**
```
I've provided cost estimates a couple of times - let me make sure I'm answering what you actually need:

**Previous Estimates I Gave:**
1. Full kitchen renovation: $45-55K (based on your 12x15 kitchen)
2. Moderate refresh: $25-30K (cabinets, counters, paint)
3. Budget cosmetic: $8-12K (paint, hardware, backsplash)

**Are you asking because:**
- These numbers seem wrong? (I can review assumptions)
- You need more detail? (I can break down by category)
- You're unsure which scope is right? (I can help you decide)
- You need financing options? (I can discuss payment strategies)

What specific aspect of the cost are you trying to understand?
```

---

## API Validation Matrix

This section maps features and capabilities to specific API endpoints for comprehensive testing.

---

### Digital Twin APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Create Home | `POST /api/digital-twin/homes` | Valid data, missing fields, duplicate | Home ID, basic info |
| Upload Floor Plan (Single) | `POST /api/digital-twin/homes/{id}/floor-plan` | PDF, image, poor quality | Room count, dimensions |
| Upload Floor Plan (Multi) | `POST /api/digital-twin/homes/{id}/floor-plan` | Multi-floor sheet | Multiple FloorPlan IDs, per-floor data |
| Upload Room Images | `POST /api/digital-twin/rooms/{id}/images` | Single, bulk, various quality | Materials, fixtures, products detected |
| Get Digital Twin | `GET /api/digital-twin/homes/{id}` | Complete data, partial data | Full home structure with nested rooms |
| Update Room | `PUT /api/digital-twin/rooms/{id}` | Valid updates, invalid data | Updated room info |
| Bulk Import Images | `POST /api/digital-twin/rooms/bulk-import` | Directory with many images | Multiple rooms updated |

---

### Chat & Conversation APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Send Chat Message | `POST /api/v1/chat` | Various intents, with/without context | AI response, intent, actions |
| Stream Chat Response | `POST /api/v1/chat/stream` | Long responses, real-time | SSE stream of response |
| Execute Action | `POST /api/v1/chat/execute-action` | Cost estimate, product search, PDF generation | Action-specific result |
| Get Conversation History | `GET /api/v1/chat/conversations/{id}` | Short/long conversations | Message array |
| Create Conversation | `POST /api/v1/chat/conversations` | With/without home_id, persona | Conversation ID |
| Upload Document to Chat | `POST /api/v1/chat/upload-document` | PDF, images, various formats | Parsed content, chat context |

---

### Design Transformation APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Transform Paint | `POST /api/v1/design/transform-paint` | Various colors, finishes | Generated image URL, metadata |
| Transform Flooring | `POST /api/v1/design/transform-flooring` | Wood, tile, vinyl options | Generated image, material details |
| Transform Cabinets | `POST /api/v1/design/transform-cabinets` | Colors, styles | Generated image |
| Transform Countertops | `POST /api/v1/design/transform-countertops` | Granite, quartz, marble | Generated image |
| Comprehensive Redesign | `POST /api/v1/design/comprehensive-redesign` | Multiple style directions | Multiple design variations |
| Get Transform History | `GET /api/v1/design/transformations` | User history | Array of past transformations |

---

### Intelligence & Recommendations APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Material Quantity | `POST /api/intelligence/material-quantity` | Paint, flooring, tile | Quantities with waste factor |
| Product Fit Check | `POST /api/intelligence/product-fit` | Various furniture, dimensions | Fit analysis, recommendations |
| Cost Estimate | `POST /api/intelligence/cost-estimate` | Refresh, moderate, full reno | Detailed cost breakdown |
| Style Suggestions | `POST /api/intelligence/style-suggestions` | Based on existing materials | Style-matched recommendations |
| Comprehensive Analysis | `POST /api/intelligence/comprehensive` | Full room analysis | Multi-faceted recommendations |

---

### Product APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Search Products | `GET /api/v1/products/search` | Keywords, filters | Matching products |
| Match to Room | `POST /api/v1/products/match-to-room` | Room ID, category, budget | Ranked product recommendations |
| Get Product Details | `GET /api/v1/products/{id}` | Valid/invalid IDs | Product details, availability |
| Create Product | `POST /api/v1/products` | Valid product data | Created product |

---

### Document Generation APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Generate DIY Guide | `POST /api/v1/documents/generate-diy-guide` | Room type, project type | Step-by-step guide PDF/MD |
| Generate Project Plan | `POST /api/v1/documents/generate-project-plan` | Renovation details | Comprehensive project doc |
| Generate Contractor Proposal | `POST /api/v1/documents/generate-contractor-proposal` | Cost breakdown, timeline | Professional proposal PDF |
| Generate Home Assessment | `POST /api/v1/documents/generate-comprehensive-report` | Home ID | Multi-section assessment report |
| Parse Uploaded Document | `POST /api/v1/documents/parse` | PDF, images | Extracted text and data |

---

### Authentication & User APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Register | `POST /api/v1/auth/register` | Valid/invalid data | User object, token |
| Login | `POST /api/v1/auth/login` | Correct/incorrect credentials | JWT token |
| Get Current User | `GET /api/v1/auth/me` | With/without token | User profile |
| Refresh Token | `POST /api/v1/auth/refresh` | Valid/expired token | New token |
| Logout | `POST /api/v1/auth/logout` | - | Success confirmation |

---

### Advanced AI Tool APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Web Search | `POST /api/v1/tools/web-search` | Real-time pricing, local data, trends | Search results with sources |
| YouTube Search | `POST /api/v1/tools/youtube-search` | DIY tutorials, how-to videos | Video metadata, URLs, ratings |
| Generate Image | `POST /api/v1/tools/generate-image` | Design concepts, mockups | Imagen 3 generated images |
| Generate Visual | `POST /api/v1/tools/generate-visual` | Charts, diagrams, infographics | Data visualization images |
| Generate Comparison | `POST /api/v1/tools/generate-comparison` | Product/material comparisons | Side-by-side comparison charts |
| **Contractor Search** | **`POST /api/v1/contractors/search-local`** | **Local contractor lookup, license verification** | **Contractor profiles with ratings, licenses, reviews** |

**Tool Integration Test Scenarios:**
1. **Web Search**: Current material prices, local contractor reviews, code updates
2. **YouTube**: DIY installation tutorials, technique demonstrations, safety guides
3. **Image Generation**: Before/after mockups, design style variations, color previews
4. **Visual Charts**: Cost breakdowns, timeline Gantt charts, ROI comparisons
5. **Contractor Search**: Real-time contractor recommendations with verified licenses and reviews
6. **Hybrid Usage**: Combine tools (web search → image generation → visual chart)

---

### Contractor Search & Recommendation APIs

| Feature | Endpoint | Test Scenarios | Expected Data |
|---------|----------|----------------|---------------|
| Search Local Contractors | `POST /api/v1/contractors/search-local` | Location, specialty, budget range | Ranked contractor list with contact info |
| Verify Contractor License | `POST /api/v1/contractors/verify-license` | License number, state | License status, expiration, bond info |
| Get Contractor Reviews | `GET /api/v1/contractors/{id}/reviews` | Contractor ID | Aggregated reviews from multiple sources |
| Generate Contractor RFP | `POST /api/v1/contractors/generate-rfp` | Project details, requirements | Professional RFP document |
| Send Contractor Inquiry | `POST /api/v1/contractors/send-inquiry` | Contractor IDs, project brief | Inquiry sent to selected contractors |

**Contractor Search Features:**
- Real-time search using Gemini grounding
- License verification via state databases
- Review aggregation (Google, Yelp, Houzz, BBB)
- Specialty matching (kitchen, bathroom, basement, etc.)
- Budget range filtering
- Availability checking
- Portfolio viewing
- Free consultation indication

---

### Testing Checklist by Journey

#### Journey 1 (Kitchen Renovation) - API Coverage
- ✅ Digital Twin: Home creation, floor plan upload, room images
- ✅ Chat: Multi-turn conversation with context
- ✅ Design: Paint, countertop, comprehensive redesign
- ✅ Intelligence: Cost estimate, material quantity
- ✅ Products: Match to room, fit check
- ✅ Documents: Project plan, DIY guide
- ✅ **Web Search**: Design trends, current pricing, product availability
- ✅ **Image Generation**: 3 design variations, before/after mockups
- ✅ **Visual Charts**: Cost comparison, product comparison
- ✅ **YouTube**: DIY maintenance tutorials
- ✅ **Contractor Search**: 5-7 local contractors with ratings, licenses, reviews, RFP generation

#### Journey 2 (DIY Bathroom) - API Coverage
- ✅ Intelligence: Material quantity (paint calculation)
- ✅ Products: Product search, match to room
- ✅ Documents: DIY guide generation
- ✅ Chat: Safety guidance, troubleshooting
- ✅ **Web Search**: Tool rental prices, paint trends
- ✅ **Image Generation**: Before/after mockup, timeline infographic
- ✅ **YouTube**: Painting, electrical, mirror installation tutorials (4+ videos)
- ✅ **Visual Charts**: DIY difficulty comparison, safety infographic

#### Journey 3 (Multi-Floor Assessment) - API Coverage
- ✅ Digital Twin: Multi-floor detection, bulk image import
- ✅ Intelligence: Comprehensive analysis, priority ranking
- ✅ Documents: Comprehensive home assessment report
- ✅ Chat: Complex multi-topic conversation
- ✅ **Web Search**: Energy rebate programs, local permit requirements
- ✅ **Visual Charts**: Priority matrix, cost/impact analysis
- ✅ **Contractor Search**: Multi-trade contractor recommendations

#### Journey 4 (Contractor Scoping) - API Coverage
- ✅ Digital Twin: Professional site analysis
- ✅ Intelligence: Detailed cost breakdown by trade
#### Journey 4 (Contractor Scoping) - API Coverage
- ✅ Digital Twin: Professional site analysis
- ✅ Intelligence: Detailed cost breakdown by trade
- ✅ Documents: Contractor proposal generation
- ✅ Chat: Change order management
- ✅ **Web Search**: Local building codes, permit requirements, contractor licensing
- ✅ **Contractor Search**: Subcontractor recommendations (electrician, plumber, HVAC)

#### Journey 5 (Investment ROI) - API Coverage
- ✅ Digital Twin: Multi-unit property
- ✅ Intelligence: ROI calculations, scenario modeling
- ✅ Chat: Financial projections, portfolio strategy
- ✅ Custom: Investment-specific metrics
- ✅ **Web Search**: Local rental market data, tax law updates
- ✅ **Visual Charts**: ROI comparison graphs, 10-year projection charts
- ✅ **Contractor Search**: Investor-friendly contractors, multi-property specialists

---

### Performance & Scale Testing

**Load Testing Scenarios:**
1. **Concurrent Users:** 100+ simultaneous chat sessions
2. **Bulk Image Upload:** 50+ images in one request
3. **Large Document Generation:** 50-page comprehensive report
4. **Complex Digital Twin:** 20+ rooms, 100+ images
5. **Contractor Search:** Multiple simultaneous location-based searches
5. **Long Conversations:** 50+ message threads with full context

**Expected Performance:**
- Chat response: <3 seconds (non-streaming)
- Image analysis: <10 seconds per image
- Document generation: <30 seconds
- Floor plan analysis: <20 seconds
- Cost estimation: <5 seconds
- **Contractor search: <5 seconds** (using Gemini grounding)

---

## Conclusion

These comprehensive customer journey test scenarios provide:

1. **5 Complex User Journeys** covering all main personas and use cases
2. **50+ Conversation Steps** with expected behaviors and API calls
3. **Detailed Edge Cases** for robustness testing
4. **Complete API Validation Matrix** ensuring full feature coverage
5. **Real-World Scenarios** that stress-test the entire system
6. **🔍 Web Search Integration** for real-time data and local information
7. **📺 YouTube Tutorial Recommendations** for visual learning and DIY guidance
8. **🎨 Image Generation** using Gemini Imagen 3 for design visualization
9. **📊 Visual Data Communication** with charts, diagrams, and infographics
10. **🏗️ Contractor Search & Recommendations** with verified licenses and real reviews
11. **Hybrid Tool Usage** demonstrating multiple AI capabilities working together

### Advanced Tool Coverage Summary

**Web Search Examples:**
- Material pricing trends (Journey 1, Step 5)
- Design trend validation (Journey 1, Step 4)
- Tool rental prices (Journey 2, Step 5)
- Local building codes (Journey 4)
- Rental market data (Journey 5)
- Energy rebate programs (Journey 3)

**Contractor Search Examples:**
- Kitchen remodeling contractors in Seattle (Journey 1, Step 8)
  - 5-7 recommendations with ratings, licenses, reviews
  - License verification via state databases
  - Review aggregation from Google, Yelp, Houzz
  - Budget range matching ($45-50K)
  - Specialty filtering (modern farmhouse)
  - RFP document generation
- Subcontractor recommendations (Journey 4)
  - Electricians, plumbers, HVAC specialists
  - Trade-specific licensing verification
- Multi-property specialists (Journey 5)
  - Investor-friendly contractors
  - Volume discount capabilities

**YouTube Tutorial Examples:**
- Kitchen demo safety (Journey 1, Step 9)
- Tile backsplash installation (Journey 1, Step 9)
- Bathroom painting techniques (Journey 2, Step 5)
- Vanity light installation (Journey 2, Step 5)
- Mirror hanging methods (Journey 2, Step 5)
- Butcher block maintenance (Journey 1, Step 10)
- Grout sealing (Journey 1, Step 10)

**Image Generation Examples:**
- 3 kitchen design variations (Journey 1, Step 4)
- Before/after mockups (Journey 1, Step 4; Journey 2, Step 5)
- Product comparison visuals (Journey 1, Step 5)
- Material visualization on room photos (throughout)

**Visual Communication Examples:**
- Cost breakdown pie charts (Journey 1, Step 7)
- Product comparison charts (Journey 1, Step 5)
- DIY difficulty bar charts (Journey 1, Step 9; Journey 2, Step 5)
- Timeline infographics (Journey 2, Step 5)
- Maintenance calendars (Journey 1, Step 10)
- Safety infographics (Journey 1, Step 9; Journey 2, Step 5)
- ROI projection graphs (Journey 5)

### Multi-Tool Orchestration Examples

**Example 1: Design Decision Support**
1. User asks: "Show me modern farmhouse kitchens"
2. **Web Search**: Find current trends and popular examples
3. **Image Generation**: Create 3 design variations
4. **Visual Chart**: Generate cost/timeline comparison
5. **Result**: Comprehensive visual response with data-backed recommendations

**Example 2: DIY Task Support**
1. User asks: "How do I install subway tile backsplash?"
2. **YouTube Search**: Find top-rated tutorial videos
3. **Web Search**: Get current material prices
4. **Image Generation**: Show expected result in user's kitchen
5. **Visual Chart**: Create step-by-step timeline infographic
6. **Result**: Complete learning package with video, pricing, and visual preview

**Example 3: ROI Analysis**
1. User asks: "Which renovation gives best ROI?"
2. **Web Search**: Local market data and comparable sales
3. **Visual Chart**: Generate ROI comparison for 8 renovation options
4. **Image Generation**: Show before/after for top recommendations
5. **Result**: Data-driven decision support with visual evidence

**Example 4: Complete Project Handoff** (NEW)
1. User: "I'm ready to hire someone. Find me contractors."
2. **Contractor Search**: Search for licensed contractors in user's location
3. **Web Search**: Verify licenses, aggregate reviews from multiple sources
4. **Document Generation**: Create professional RFP with project details
5. **Visual Chart**: Create contractor comparison chart (ratings, pricing, availability)
6. **Result**: Complete contractor recommendation package with verified credentials

**Next Steps for Implementation:**
1. Use these scenarios for manual QA testing
2. Build automated test scripts based on these flows
3. Create Postman/API collections for endpoint validation
4. Set up monitoring for performance metrics
5. **Implement Gemini grounding** for web search (replaces Perplexity)
6. **Implement YouTube search** (hybrid: Gemini grounding + YouTube Data API v3)
7. **Enhance Imagen 3 prompting** for consistent design generation
8. **Build visual chart generator** (using Gemini code execution or charting APIs)
9. **Implement contractor search** using Gemini grounding for real-time results
10. Test tool orchestration workflows
11. Iterate based on real user feedback

**Success Metrics:**
- Intent classification accuracy: >90%
- User satisfaction with recommendations: >85%
- API response times within targets: >95%
- Conversation completion rates: >80%
- Action execution success: >90%
- **Tool integration success rate: >85%**
- **YouTube video relevance rating: >90%**
- **Web search result accuracy: >90%**
- **Image generation quality score: >4.0/5.0**
- **Visual chart clarity rating: >90%**
- **Contractor recommendation accuracy: >85%**
- **License verification success: >95%**

### Tool Performance Targets

| Tool | Expected Response Time | Quality Metric |
|------|----------------------|----------------|
| Web Search (Gemini Grounding) | <2 seconds | >90% result relevance |
| YouTube Search | <1.5 seconds | >90% video relevance |
| Image Generation (Imagen 3) | <8 seconds | >4.0/5.0 quality rating |
| Visual Chart Generation | <3 seconds | >90% clarity rating |
| **Contractor Search** | **<5 seconds** | **>85% match accuracy, >95% license verification** |
| Multi-tool Orchestration | <15 seconds total | Seamless integration |

---

**Document Version:** 1.2  
**Last Updated:** November 8, 2025  
**Author:** HomeView AI Testing Team  
**Status:** Ready for Implementation with Advanced AI Tools

**Changelog:**
- v1.0 (Initial): 5 journeys, edge cases, API validation
- v1.1 (Enhanced): Added web search, YouTube recommendations, image generation, visual charts, multi-tool orchestration examples
- v1.2 (Contractor Search): Added comprehensive contractor search and recommendation feature using Gemini grounding with license verification, review aggregation, and RFP generation
- v1.1 (Enhanced): Added web search, YouTube recommendations, image generation, visual charts, multi-tool orchestration examples

