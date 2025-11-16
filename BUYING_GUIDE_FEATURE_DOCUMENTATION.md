# 📖 Buying Guide Feature - Complete Documentation

## 🎯 Overview

The Buying Guide feature generates comprehensive, structured buying guides similar to **Home Depot's format** for any product category. Users can generate expert-level guides with product types, features, comparisons, and recommendations.

---

## ✨ Features

### 1. **Comprehensive Content Sections**
- 📋 Overview - Introduction to the product category
- 🏷️ Types & Categories - Different types with descriptions
- ⭐ Key Features - Important features to consider
- 📏 Sizes & Specifications - Common dimensions and ranges
- 🎨 Materials & Finishes - Available options with pros/cons
- 💰 Price Ranges - Typical price points by tier
- 📊 Comparison Table - Side-by-side product comparison
- 💡 Expert Buying Tips - Professional recommendations
- 🔧 Installation & Maintenance - Care and setup info
- 🏆 Top Recommendations - 5-7 recommended products
- ❓ FAQ - Common questions answered

### 2. **Customization Options**
- Product category (required)
- Room type (optional) - kitchen, bathroom, living room, etc.
- Budget range (optional) - e.g., "$500-$1500"
- Region (optional) - Canada, USA, Vancouver, Toronto, etc.

### 3. **AI-Powered Generation**
- Uses Google Gemini for intelligent content creation
- Structured JSON output for consistent formatting
- Canadian-focused recommendations when relevant
- Expert-level information and analysis

---

## 🏗️ Architecture

### Backend Components

#### 1. **Buying Guide Agent** (`backend/agents/intelligence/buying_guide_agent.py`)
```python
class BuyingGuideAgent:
    async def process(
        product_category: str,
        room_type: Optional[str] = None,
        budget_range: Optional[str] = None,
        region: str = "Canada"
    ) -> Dict[str, Any]
```

**Responsibilities:**
- Generate comprehensive buying guide content
- Structure response in Home Depot-like format
- Parse Gemini AI responses into JSON
- Handle errors gracefully

#### 2. **API Endpoint** (`backend/api/intelligence.py`)
```
POST /api/v1/intelligence/generate-buying-guide
```

**Request:**
```json
{
    "product_category": "dishwashers",
    "room_type": "kitchen",
    "budget_range": "$500-$1500",
    "region": "Canada"
}
```

**Response:**
```json
{
    "success": true,
    "product_category": "dishwashers",
    "guide": {
        "title": "Complete Dishwasher Buying Guide",
        "overview": "...",
        "types": [...],
        "key_features": [...],
        "sizes_specifications": [...],
        "materials_finishes": [...],
        "price_ranges": [...],
        "comparison_table": [...],
        "buying_tips": [...],
        "installation_maintenance": {...},
        "top_recommendations": [...],
        "faq": [...]
    },
    "region": "Canada"
}
```

### Frontend Components

#### **Streamlit Page** (`streamlit_homeview_chat.py`)
- Page: `📖 Buying Guides`
- Function: `_render_buying_guides_page()`
- Features:
  - Input form for product category and options
  - Real-time guide generation with spinner
  - Expandable sections for detailed information
  - Comparison table display
  - FAQ accordion
  - Save guide option

---

## 🚀 How to Use

### 1. **Access the Feature**
- Open Streamlit app: http://localhost:8501
- Click "📖 Buying Guides" in sidebar

### 2. **Generate a Guide**
- Enter product category (e.g., "dishwashers", "paint", "flooring")
- Optionally select room type and budget range
- Click "📖 Generate Buying Guide"
- Wait for AI to generate comprehensive guide (~30-60 seconds)

### 3. **Explore the Guide**
- Read overview and key information
- Expand sections to see detailed content
- View comparison table for side-by-side analysis
- Check FAQ for common questions
- Review top recommendations

### 4. **Save the Guide**
- Click "💾 Save Guide" to save to your library
- Access saved guides later for reference

---

## 📊 Example Use Cases

### 1. **Dishwasher Buying Guide**
```
Product Category: dishwashers
Room Type: kitchen
Budget Range: $500-$1500
Region: Canada
```
**Output:** Complete guide with types (built-in, portable, drawer), features, sizes, materials, price tiers, comparison table, and top recommendations.

### 2. **Paint Buying Guide**
```
Product Category: paint
Room Type: living room
Budget Range: $50-$200
Region: Canada
```
**Output:** Guide covering paint types (latex, acrylic, oil), finishes (matte, satin, gloss), coverage calculations, application tips, and product recommendations.

### 3. **Flooring Buying Guide**
```
Product Category: flooring
Room Type: kitchen
Budget Range: $1000-$5000
Region: Vancouver, BC
```
**Output:** Comprehensive guide with flooring types (tile, laminate, hardwood), durability ratings, maintenance requirements, installation costs, and local product recommendations.

---

## 🔧 Technical Details

### Response Model Structure
```python
{
    "title": str,
    "overview": str,
    "types": [
        {
            "name": str,
            "description": str,
            "best_for": str
        }
    ],
    "key_features": [str],
    "sizes_specifications": [
        {
            "dimension": str,
            "common_range": str,
            "notes": str
        }
    ],
    "materials_finishes": [
        {
            "material": str,
            "pros": [str],
            "cons": [str],
            "price_impact": str
        }
    ],
    "price_ranges": [
        {
            "tier": str,
            "price_range": str,
            "features": [str]
        }
    ],
    "comparison_table": [
        {
            "product_type": str,
            "durability": str,
            "cost": str,
            "maintenance": str,
            "best_for": str
        }
    ],
    "buying_tips": [str],
    "installation_maintenance": {
        "installation": str,
        "maintenance": [str]
    },
    "top_recommendations": [
        {
            "rank": int,
            "name": str,
            "type": str,
            "price_range": str,
            "key_benefits": [str],
            "best_for": str
        }
    ],
    "faq": [
        {
            "question": str,
            "answer": str
        }
    ]
}
```

---

## 🎨 UI Components

### Input Section
- Product category text input
- Region dropdown
- Room type dropdown
- Budget range input
- Generate button

### Display Sections
- Title and overview
- Expandable type cards
- Feature list
- Specifications table
- Material comparison cards
- Price tier breakdown
- Comparison data table
- Tips list
- Installation/maintenance info
- Recommendation cards
- FAQ accordion
- Save button

---

## ⚡ Performance

- **Generation Time:** 30-60 seconds (depends on Gemini API)
- **Response Size:** ~10-20 KB JSON
- **Timeout:** 120 seconds
- **Caching:** Not implemented (each request generates fresh guide)

---

## 🔐 Authentication

- ✅ Works with guest mode (no login required)
- ✅ Works with authenticated users
- ✅ Uses optional JWT token if available

---

## 🐛 Error Handling

- ✅ Validates product category input
- ✅ Handles API timeouts gracefully
- ✅ Displays user-friendly error messages
- ✅ Logs errors for debugging

---

## 📈 Future Enhancements

1. **Product Integration** - Link to actual products from Google Grounding
2. **Guide Caching** - Cache generated guides for faster retrieval
3. **User Library** - Save and organize guides by user
4. **Comparison Mode** - Compare multiple product categories
5. **Video Integration** - Embed YouTube tutorials
6. **PDF Export** - Download guides as PDF
7. **Ratings & Reviews** - Show user ratings for products
8. **Price Tracking** - Monitor price changes over time

---

## 📝 Files Modified/Created

### Created
- `backend/agents/intelligence/buying_guide_agent.py` - Buying guide generation agent
- `BUYING_GUIDE_FEATURE_DOCUMENTATION.md` - This documentation

### Modified
- `backend/api/intelligence.py` - Added `/generate-buying-guide` endpoint
- `streamlit_homeview_chat.py` - Added buying guides page and navigation

---

## ✅ Testing Checklist

- [ ] Test with "dishwashers" category
- [ ] Test with "paint" category
- [ ] Test with "flooring" category
- [ ] Test with room type selection
- [ ] Test with budget range
- [ ] Test with different regions
- [ ] Test error handling (invalid category)
- [ ] Test timeout handling
- [ ] Test guest mode access
- [ ] Test authenticated mode access
- [ ] Verify all sections display correctly
- [ ] Test expandable sections
- [ ] Test comparison table rendering
- [ ] Test FAQ accordion
- [ ] Test save functionality

---

## 🎉 Summary

The Buying Guide feature provides users with **professional, comprehensive buying guides** for any product category, similar to Home Depot's format. It combines AI-powered content generation with a beautiful, interactive Streamlit interface to help customers make informed purchasing decisions.

**Key Benefits:**
- ✅ Expert-level information
- ✅ Structured, easy-to-read format
- ✅ Customizable by room type and budget
- ✅ Canadian-focused recommendations
- ✅ No login required
- ✅ Fast generation (~30-60 seconds)

