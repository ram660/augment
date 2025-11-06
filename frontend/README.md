# HomeVision AI - Digital Twin Test UI

A simple, modern web interface to test the HomeVision AI Digital Twin system.

## Features

- ✅ Create homes with address and property details
- 📐 Upload and analyze floor plans with Gemini AI
- 🏠 Upload and analyze room images
- 📊 View complete digital twin data
- 🎨 Modern, responsive UI with real-time feedback

## How to Use

### 1. Start the API Server

Make sure the backend API is running:

```bash
python backend/main.py
```

Or:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Open the UI

Navigate to: **http://localhost:8000**

The frontend is automatically served by the FastAPI backend.

### 3. Test the Digital Twin System

#### Step 1: Create a Home
1. Fill in the home details (pre-filled with test data)
2. Click "Create Home"
3. Wait for confirmation

#### Step 2: Upload Floor Plan
1. Select a floor plan image (JPG, PNG, WEBP)
2. Set the floor level and name
3. Click "Analyze Floor Plan"
4. Wait for Gemini AI to analyze the image (may take 10-30 seconds)
5. View detected rooms

#### Step 3: Upload Room Images
1. For each detected room, upload a room photo
2. Select analysis type (comprehensive, quick, or detailed)
3. Click "Analyze Room"
4. Wait for Gemini AI to detect materials, fixtures, and products

#### Step 4: View Digital Twin
1. Click "Refresh Data" to see the complete digital twin
2. View statistics, room details, materials, fixtures, and products
3. Check the digital twin completeness score

## UI Components

### Home Creation Form
- Owner email
- Home name
- Full address (street, city, province, postal code)
- Year built, square footage
- Number of bedrooms and bathrooms

### Floor Plan Upload
- File upload with image preview
- Floor level selector
- Floor name input
- Real-time analysis progress

### Room Image Upload
- One upload form per detected room
- Analysis type selector
- Individual progress tracking per room

### Digital Twin Display
- Statistics cards (home type, rooms, images, square footage)
- Completeness progress bar
- Detailed room information
- Materials, fixtures, and products tags

## Technical Details

### Frontend Stack
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with gradients and animations
- **Vanilla JavaScript** - No frameworks, pure ES6+
- **Fetch API** - For HTTP requests

### API Integration
- Base URL: `http://localhost:8000/api/digital-twin`
- Endpoints used:
  - `POST /homes` - Create home
  - `POST /homes/{id}/floor-plans` - Upload floor plan
  - `POST /rooms/{id}/images` - Upload room image
  - `GET /homes/{id}` - Get digital twin data

### Features
- Real-time loading indicators
- Error handling with user-friendly messages
- Image preview before upload
- Responsive design
- Color-coded result messages (success, error, info)

## Customization

### Change API URL
Edit `frontend/app.js`:
```javascript
const API_BASE_URL = 'http://your-api-url/api/digital-twin';
```

### Modify Styles
Edit `frontend/styles.css` to customize:
- Colors and gradients
- Card layouts
- Typography
- Animations

### Add Features
Edit `frontend/app.js` to add:
- More form fields
- Additional API calls
- Data visualization
- Export functionality

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Notes

- Make sure your Gemini API key is set in `.env`
- Floor plan analysis may take 10-30 seconds
- Room image analysis may take 5-15 seconds
- Large images will be automatically resized by the backend
- Supported image formats: JPG, PNG, WEBP

## Troubleshooting

### UI doesn't load
- Check that the API server is running on port 8000
- Check browser console for errors
- Verify `frontend` folder exists in project root

### API calls fail
- Check CORS is enabled in backend
- Verify API endpoints are correct
- Check network tab in browser dev tools

### Images don't upload
- Check file size (max 10MB recommended)
- Verify image format (JPG, PNG, WEBP only)
- Check backend logs for errors

## Next Steps

- Add authentication
- Implement user sessions
- Add data export (JSON, PDF)
- Create data visualization charts
- Add image gallery for uploaded photos
- Implement room editing
- Add cost estimation features

