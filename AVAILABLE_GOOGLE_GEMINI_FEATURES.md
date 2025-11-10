# Available Google/Gemini Features for HomeView AI

## 📋 Overview

This document lists all available Google/Gemini features we can integrate into HomeView AI's chat assistant.

---

## ✅ Currently Implemented Features

### 1. **Google Search Grounding** ✅
- **Status:** IMPLEMENTED
- **Purpose:** Product recommendations, cost estimates, material selection
- **Tool:** `types.Tool(google_search=types.GoogleSearch())`
- **Location:** `backend/workflows/chat_workflow.py` - `_enrich_with_multimodal` node
- **Returns:** Web search results with Canadian priority (.ca domains)
- **UI:** Product cards with name, price, description, vendor, Canadian flag
- **Pricing:** $25 per 1,000 grounded prompts

### 2. **Google Maps Grounding** ✅
- **Status:** IMPLEMENTED
- **Purpose:** Contractor search in Vancouver, BC area
- **Tool:** `types.Tool(google_maps=types.GoogleMaps())`
- **Location:** `backend/workflows/chat_workflow.py` - `_enrich_with_multimodal` node
- **Returns:** Contractor names, place IDs, Google Maps URLs
- **UI:** Contractor cards with icon, name, type, location, rating, phone
- **Pricing:** $25 per 1,000 grounded prompts

### 3. **YouTube Search via Google Grounding** ✅
- **Status:** IMPLEMENTED
- **Purpose:** DIY tutorial videos
- **Method:** Google Search with `site:youtube.com` filter
- **Location:** `backend/workflows/chat_workflow.py` - `_enrich_with_multimodal` node
- **Returns:** Video URLs, thumbnails, titles, channels
- **UI:** Video cards with thumbnails, titles, channels, duration
- **Pricing:** Included in Google Search Grounding

### 4. **Image Generation (Imagen)** ✅
- **Status:** IMPLEMENTED (in design studio)
- **Purpose:** Generate/edit room images
- **Model:** `imagen-4.0-generate-001`
- **Location:** `backend/integrations/gemini/client.py`
- **Returns:** Base64-encoded images
- **UI:** Image gallery grid
- **Pricing:** Separate Imagen pricing

### 5. **Image Understanding (Vision)** ✅
- **Status:** IMPLEMENTED
- **Purpose:** Analyze uploaded room images
- **Model:** `gemini-2.5-flash-image`
- **Location:** `backend/integrations/gemini/client.py`
- **Returns:** Room analysis (type, features, dimensions, condition)
- **Pricing:** Included in Gemini model pricing

### 6. **Chat/Agent Mode Toggle** ✅
- **Status:** IMPLEMENTED
- **Purpose:** Switch between simple chat and full agentic workflow
- **Location:** `homeview-frontend/components/chat/ChatModeToggle.tsx`
- **UI:** Beautiful toggle (Chat | Agent) in top-right corner
- **Behavior:** Agent mode enables all tools, Chat mode is simple conversation

---

## 🔄 Available But Not Yet Implemented

### 7. **Code Execution** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Execute Python code for calculations, data analysis
- **Tool:** `types.Tool(code_execution=types.CodeExecution())`
- **Use Cases:**
  - Calculate material quantities (e.g., "How many tiles for 100 sq ft?")
  - Cost calculations with tax and labor
  - Complex measurements and conversions
  - Data analysis of home metrics
- **Example:**
  ```python
  config = types.GenerateContentConfig(
      tools=[types.Tool(code_execution=types.CodeExecution())]
  )
  ```
- **Pricing:** Free (included in Gemini model pricing)

### 8. **Function Calling** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Call custom backend functions from AI
- **Tool:** `types.Tool(function_declarations=[...])`
- **Use Cases:**
  - Fetch user's home data from database
  - Create DIY project plans
  - Generate contractor quotes
  - Update home information
  - Schedule appointments
- **Example:**
  ```python
  get_home_data = types.FunctionDeclaration(
      name="get_home_data",
      description="Fetch home data from database",
      parameters={
          "type": "object",
          "properties": {
              "home_id": {"type": "string"}
          }
      }
  )
  ```
- **Pricing:** Free (included in Gemini model pricing)

### 9. **Google Maps Widget** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Show interactive Google Maps in chat
- **Tool:** `google_maps=types.GoogleMaps(enable_widget=True)`
- **Returns:** `googleMapsWidgetContextToken`
- **Use Cases:**
  - Show contractor locations on map
  - Display nearby home improvement stores
  - Visualize service areas
- **Example:**
  ```html
  <gmp-place-contextual context-token="{token}"></gmp-place-contextual>
  ```
- **Pricing:** Included in Maps Grounding pricing

### 10. **URL Context** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Extract content from specific URLs
- **Tool:** `types.Tool(url_context=types.UrlContext(urls=[...]))`
- **Use Cases:**
  - Analyze product pages
  - Extract contractor information from websites
  - Read DIY guides from specific URLs
  - Parse building codes and regulations
- **Example:**
  ```python
  config = types.GenerateContentConfig(
      tools=[types.Tool(url_context=types.UrlContext(
          urls=["https://example.com/product"]
      ))]
  )
  ```
- **Pricing:** Free (included in Gemini model pricing)

### 11. **File Search (RAG)** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Search through uploaded documents
- **Tool:** `types.Tool(file_search=types.FileSearch())`
- **Use Cases:**
  - Search through uploaded floor plans
  - Query building permits and documents
  - Find information in contractor proposals
  - Search home inspection reports
- **Requires:** Files API integration
- **Pricing:** Free (included in Gemini model pricing)

### 12. **Context Caching** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Cache large contexts (floor plans, home data) for faster responses
- **API:** `cached_content` parameter
- **Use Cases:**
  - Cache floor plan analysis
  - Cache home data for entire conversation
  - Cache contractor database
  - Reduce latency and costs
- **Pricing:** 50% discount on cached tokens

### 13. **Structured Output (JSON Mode)** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Force AI to return structured JSON
- **Config:** `response_mime_type="application/json"`
- **Use Cases:**
  - Generate DIY project plans in structured format
  - Extract room data in consistent schema
  - Create contractor quotes with fixed fields
  - Parse measurements and dimensions
- **Example:**
  ```python
  config = types.GenerateContentConfig(
      response_mime_type="application/json",
      response_schema={
          "type": "object",
          "properties": {
              "room_type": {"type": "string"},
              "dimensions": {"type": "object"}
          }
      }
  )
  ```
- **Pricing:** Free (included in Gemini model pricing)

### 14. **Batch API** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Process multiple requests in batch
- **Use Cases:**
  - Analyze multiple room images at once
  - Generate multiple design variations
  - Bulk contractor searches
  - Process entire home floor plan
- **Pricing:** 50% discount on batch requests

### 15. **Live API (Real-time Audio/Video)** 🔄
- **Status:** NOT IMPLEMENTED
- **Purpose:** Real-time voice/video conversations
- **Use Cases:**
  - Voice-guided home tours
  - Real-time contractor consultations
  - Voice-controlled design studio
  - Live DIY assistance
- **Pricing:** Separate Live API pricing

---

## 🎯 Recommended Next Implementations

### Priority 1: **Code Execution** 🔥
**Why:** Essential for accurate calculations
- Material quantity calculations
- Cost estimates with tax
- Measurement conversions
- Complex math for DIY projects

**Implementation Effort:** LOW (just add tool to config)

### Priority 2: **Function Calling** 🔥
**Why:** Connect AI to our database and backend
- Fetch home data automatically
- Create DIY plans in database
- Update home information
- Schedule contractor appointments

**Implementation Effort:** MEDIUM (need to define functions)

### Priority 3: **Structured Output (JSON Mode)** 🔥
**Why:** Consistent data format for DIY plans and quotes
- Generate DIY project plans
- Create contractor quotes
- Extract room measurements
- Parse cost estimates

**Implementation Effort:** LOW (just add config)

### Priority 4: **Google Maps Widget** 🔥
**Why:** Better contractor visualization
- Show contractor locations on map
- Display service areas
- Visualize nearby stores

**Implementation Effort:** MEDIUM (need to add Maps JS API)

### Priority 5: **Context Caching**
**Why:** Faster responses and lower costs
- Cache floor plan analysis
- Cache home data
- Reduce latency

**Implementation Effort:** MEDIUM (need to manage cache lifecycle)

---

## 📊 Feature Comparison Matrix

| Feature | Status | Effort | Impact | Priority |
|---------|--------|--------|--------|----------|
| Google Search Grounding | ✅ Done | - | High | - |
| Google Maps Grounding | ✅ Done | - | High | - |
| YouTube Search | ✅ Done | - | Medium | - |
| Image Generation | ✅ Done | - | High | - |
| Image Understanding | ✅ Done | - | High | - |
| Chat/Agent Toggle | ✅ Done | - | High | - |
| **Code Execution** | 🔄 Todo | Low | High | **P1** |
| **Function Calling** | 🔄 Todo | Medium | High | **P2** |
| **Structured Output** | 🔄 Todo | Low | High | **P3** |
| **Maps Widget** | 🔄 Todo | Medium | Medium | **P4** |
| **Context Caching** | 🔄 Todo | Medium | Medium | P5 |
| URL Context | 🔄 Todo | Low | Low | P6 |
| File Search | 🔄 Todo | High | Medium | P7 |
| Batch API | 🔄 Todo | Medium | Low | P8 |
| Live API | 🔄 Todo | High | High | P9 |

---

## 🚀 Quick Implementation Guide

### Add Code Execution (5 minutes)

```python
# In backend/workflows/chat_workflow.py - _enrich_with_multimodal

if intent in ["calculation", "cost_estimate", "material_quantity"]:
    # Enable code execution for calculations
    from google.genai import types
    
    response = await self.gemini_client.generate_content(
        prompt=f"Calculate: {user_message}",
        tools=[types.Tool(code_execution=types.CodeExecution())]
    )
```

### Add Function Calling (30 minutes)

```python
# Define functions
get_home_data = types.FunctionDeclaration(
    name="get_home_data",
    description="Fetch home data from database",
    parameters={
        "type": "object",
        "properties": {
            "home_id": {"type": "string", "description": "Home UUID"}
        },
        "required": ["home_id"]
    }
)

# Use in workflow
config = types.GenerateContentConfig(
    tools=[types.Tool(function_declarations=[get_home_data])]
)

# Handle function calls
if response.candidates[0].function_calls:
    for fc in response.candidates[0].function_calls:
        if fc.name == "get_home_data":
            result = await fetch_home_data(fc.args["home_id"])
            # Send result back to model
```

### Add Structured Output (10 minutes)

```python
# Force JSON output for DIY plans
config = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema={
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_number": {"type": "integer"},
                        "description": {"type": "string"},
                        "duration": {"type": "string"}
                    }
                }
            },
            "materials": {"type": "array"},
            "total_cost": {"type": "number"}
        }
    }
)
```

---

## ✅ Summary

**Currently Using:**
- ✅ Google Search Grounding (products, costs)
- ✅ Google Maps Grounding (contractors)
- ✅ YouTube Search (DIY videos)
- ✅ Image Generation (Imagen)
- ✅ Image Understanding (Vision)
- ✅ Chat/Agent Mode Toggle

**Ready to Add (High Priority):**
- 🔥 Code Execution (calculations)
- 🔥 Function Calling (database integration)
- 🔥 Structured Output (DIY plans, quotes)
- 🔥 Maps Widget (interactive maps)

**Future Enhancements:**
- Context Caching (performance)
- URL Context (web scraping)
- File Search (document RAG)
- Batch API (bulk processing)
- Live API (voice/video)

**Next Steps:** Let me know which features you'd like to implement next! 🚀

