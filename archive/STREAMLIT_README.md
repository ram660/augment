> Archived notice (2025-11-03)
>
> This document has been archived. The primary, up-to-date documentation now lives under `docs/` and the main project `README.md`. See: docs/INDEX.md

# 🏠 HomeVision AI - Streamlit Application

A modern, interactive web interface for the HomeVision AI Digital Twin Platform built with Streamlit.

## ✨ Features

- **🏡 Create Homes** - Add new properties with detailed information
- **📐 Upload Floor Plans** - AI-powered floor plan analysis with room detection
- **📸 Upload Room Images** - Comprehensive room analysis for materials, fixtures, and products
- **🔍 View Digital Twin** - Interactive visualization of complete home data
- **📊 Real-time Stats** - Live metrics and progress tracking
- **🎨 Modern UI** - Beautiful gradient design with responsive layout

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **FastAPI backend running** on `http://localhost:8000`
3. **Streamlit installed** (included in requirements.txt)

### Installation

```bash
# Install Streamlit (if not already installed)
pip install streamlit>=1.31.0

# Or install all dependencies
pip install -r requirements.txt
```

### Running the App

#### Method 1: Using the run script (Recommended)

```bash
python run_streamlit.py
```

#### Method 2: Using Streamlit directly

```bash
streamlit run streamlit_app.py
```

#### Method 3: Custom port

```bash
streamlit run streamlit_app.py --server.port 8501
```

The app will automatically open in your browser at **http://localhost:8501**

## 📋 Usage Guide

### Step 1: Create a Home 🏡

1. Navigate to **"Create Home"** in the sidebar
2. Fill in owner information:
   - Email address
   - Home name
3. Enter complete address details
4. Add property details:
   - Home type (single family, condo, townhouse, etc.)
   - Year built
   - Square footage
   - Number of bedrooms, bathrooms, floors
5. Click **"Create Home"**
6. Note the Home ID for future reference

### Step 2: Upload Floor Plan 📐

1. Navigate to **"Upload Floor Plan"**
2. Select a floor plan image (PNG, JPG, JPEG, WEBP)
3. Preview the image
4. Set floor level and name
5. Click **"Analyze Floor Plan"**
6. Wait 10-30 seconds for AI analysis
7. View detected rooms

### Step 3: Upload Room Images 📸

1. Navigate to **"Upload Room Images"**
2. Select a room from the dropdown
3. Upload a room image
4. Choose image type, view angle, and analysis type
5. Click **"Analyze Room Image"**
6. Wait for AI to detect materials, fixtures, and products

### Step 4: View Digital Twin 🔍

1. Navigate to **"View Digital Twin"**
2. See overview statistics:
   - Total rooms
   - Total images
   - Square footage
   - Completeness percentage
3. Explore home information and property details
4. View floor plans
5. Drill down into individual rooms:
   - Dimensions
   - Materials detected
   - Fixtures identified
   - Products recognized
   - Images uploaded

## 🎨 Features in Detail

### Modern UI Design

- **Gradient Headers** - Eye-catching purple gradient branding
- **Stat Cards** - Beautiful cards displaying key metrics
- **Color-coded Messages** - Success (green), error (red), info (blue)
- **Responsive Layout** - Works on desktop and tablet
- **Image Previews** - See uploads before processing

### AI-Powered Analysis

- **Floor Plan Analysis**
  - Room detection and layout extraction
  - Dimension estimation
  - Room type classification
  - Spatial relationships

- **Room Image Analysis**
  - Material identification (flooring, walls, countertops)
  - Fixture detection (faucets, lights, outlets)
  - Product recognition (appliances, furniture)
  - Condition assessment

### Session Management

- Maintains home ID across pages
- Tracks detected rooms
- Caches digital twin data
- Seamless navigation

## 🔧 Configuration

### API Endpoint

The app connects to the FastAPI backend. To change the API URL, edit `streamlit_app.py`:

```python
API_BASE_URL = "http://localhost:8000/api/digital-twin"
```

### Port Configuration

Default port is 8501. To change:

```bash
streamlit run streamlit_app.py --server.port YOUR_PORT
```

### Theme Customization

Edit the custom CSS in `streamlit_app.py` to change colors, fonts, and styling.

## 📊 API Integration

The Streamlit app integrates with these FastAPI endpoints:

- `POST /api/digital-twin/homes` - Create home
- `POST /api/digital-twin/homes/{home_id}/floor-plans` - Upload floor plan
- `POST /api/digital-twin/rooms/{room_id}/images` - Upload room image
- `GET /api/digital-twin/homes/{home_id}` - Get digital twin data

## 🐛 Troubleshooting

### App won't start

```bash
# Check if Streamlit is installed
pip show streamlit

# Reinstall if needed
pip install --upgrade streamlit
```

### Can't connect to API

1. Verify FastAPI backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check API_BASE_URL in streamlit_app.py

3. Look for CORS errors in browser console

### Images won't upload

1. Check file format (PNG, JPG, JPEG, WEBP only)
2. Verify file size (< 10MB recommended)
3. Check backend logs for errors

### Analysis takes too long

- Floor plan analysis: 10-30 seconds (normal)
- Room image analysis: 10-30 seconds (normal)
- If longer, check:
  - Internet connection (Gemini API requires internet)
  - API quota limits
  - Backend logs

## 🎯 Tips for Best Results

### Floor Plans

- Use high-resolution images
- Ensure good contrast
- Include scale if possible
- Avoid blurry or distorted images

### Room Images

- Take photos in good lighting
- Capture full room view
- Include key features (fixtures, materials)
- Avoid extreme angles

## 🚀 Advanced Features

### Session State

The app uses Streamlit session state to maintain:
- Current home ID
- Detected room IDs
- Digital twin data cache

### Error Handling

- Graceful API error messages
- User-friendly error boxes
- Automatic retry suggestions

### Performance

- Lazy loading of digital twin data
- Image preview before upload
- Efficient API calls

## 📱 Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🔐 Security Notes

- This is a development version
- No authentication implemented yet
- Use in trusted networks only
- Don't expose to public internet

## 📚 Next Steps

After using the Streamlit app, you can:

1. **View API Docs** - http://localhost:8000/docs
2. **Access Database** - Query SQLite database directly
3. **Build Custom Features** - Extend the Streamlit app
4. **Export Data** - Add export functionality
5. **Add Visualizations** - Create charts and graphs

## 🤝 Contributing

To add new features to the Streamlit app:

1. Edit `streamlit_app.py`
2. Add new pages or components
3. Update this README
4. Test thoroughly

## 📄 License

Proprietary - Part of HomeVision AI Platform

---

**Built with ❤️ using Streamlit and FastAPI**

For questions or issues, check the main project documentation.

