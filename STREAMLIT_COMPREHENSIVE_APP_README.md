# HomeView AI - Comprehensive Streamlit Application

## 🎯 Overview

This is a **complete, multi-page Streamlit application** that provides access to **ALL HomeView AI backend endpoints** in a user-friendly interface. It serves customers in all possible ways with comprehensive features across the entire platform.

## 🚀 Quick Start

### 1. Start the Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Run the Streamlit App
```bash
# From repo root
streamlit run streamlit_homeview_chat.py
```

### 3. Access the App
Open your browser to `http://localhost:8501`

## 📱 Features & Pages

### 💬 **Chat Assistant**
- **Multimodal chat** with text and image support
- **Real-time streaming** responses
- **Thinking process visualization** - see how AI plans and executes tasks
- **Suggested actions** with one-click execution
- **Rich metadata display** - intent, images, products, videos, web sources
- **Image uploads** for design transformations
- **Conversation history** with context

### 🎨 **Design Studio** (25+ Endpoints)
- **Paint Transformations** - Change wall colors with different finishes
- **Flooring Changes** - Hardwood, tile, carpet, laminate, vinyl
- **Cabinet Transformations** - Modern, traditional, custom styles
- **Countertop Changes** - Granite, quartz, marble, butcher block
- **Backsplash Transformations** - Subway tile, custom patterns
- **Virtual Staging** - Add furniture in different styles
- **Unstaging** - Remove furniture from images
- **Custom Transformations** - Freeform prompts
- **Object Segmentation** - AI-powered object detection
- **Multi-Angle Views** - Generate different perspectives
- **Style Variations** - Multiple design options
- **Before/After Comparisons** - Side-by-side results
- **Product Recommendations** - Google Grounding integration
- **Transformation History** - Track all your designs

### 🏠 **Digital Twin**
- **Home Management** - Create and manage multiple homes
- **Floor Plan Upload** - AI-powered floor plan analysis
- **Room Detection** - Automatic room identification
- **Room Management** - Add, edit, view rooms
- **Image Analysis** - Material, fixture, product detection
- **Digital Twin Visualization** - Complete home representation

### 🗺️ **Journey Manager**
- **Project Tracking** - Track home improvement projects
- **Journey Templates** - Kitchen, bathroom, living room renovations
- **Progress Monitoring** - Step-by-step progress tracking
- **Image Uploads** - Document your journey with photos
- **Journey History** - View all past and active projects

### 🛍️ **Products**
- **Product Catalog** - Browse all products
- **Advanced Search** - Filter by category, price, style
- **Google Grounding Search** - Real-world product recommendations
- **Product Details** - Dimensions, pricing, availability
- **AI Recommendations** - Personalized product suggestions

### 📄 **Documents**
- **Document Parsing** - Upload and parse any document
- **Contractor Quote Parsing** - Extract pricing and services
- **Datasheet Parsing** - Product specification extraction
- **Inspection Report Parsing** - Home inspection analysis
- **Quote Comparison** - Compare multiple contractor quotes
- **Chat with Documents** - Ask questions about uploaded files

### 🧠 **Intelligence**
- **Cost Estimation** - Renovation cost calculations
- **Material Quantity** - Calculate material needs
- **Product Fit Analysis** - Check if products fit your space
- **Style Suggestions** - AI-powered design recommendations
- **Image Generation** - Generate design concepts from text

### 📊 **Monitoring**
- **System Health** - Backend health checks
- **Performance Metrics** - API response times, usage stats
- **Error Tracking** - Monitor system errors

### ⚙️ **Admin**
- **User Management** - Manage user accounts
- **System Settings** - Configure platform settings
- **Analytics Dashboard** - Usage and performance analytics

## 🔐 Authentication

### Guest Mode (Default)
- Access most features without login
- Limited to public endpoints
- No data persistence across sessions

### Authenticated Mode
- Full access to all features
- Data persistence and history
- Personal homes, journeys, and transformations
- Saved conversations and preferences

### Login/Register
1. Click **"🔐 Login"** in the sidebar
2. Use existing credentials or register a new account
3. Default test account: `test@homeview.ai` / `test123`

## 🎨 Usage Examples

### Example 1: Design Transformation
1. Navigate to **🎨 Design Studio**
2. Upload a room image
3. Select transformation type (e.g., "Paint Walls")
4. Choose color and finish
5. Click **"🎨 Transform"**
6. View before/after comparison
7. Browse product recommendations

### Example 2: Chat with AI
1. Navigate to **💬 Chat Assistant**
2. Type your question or upload an image
3. Watch the AI thinking process
4. View rich responses with images and suggestions
5. Click suggested actions for quick follow-ups

### Example 3: Create Digital Twin
1. Navigate to **🏠 Digital Twin**
2. Create a new home with address and details
3. Upload floor plan image
4. AI analyzes and detects rooms
5. Upload room images for detailed analysis
6. View complete digital twin

### Example 4: Track Renovation Journey
1. Navigate to **🗺️ Journey Manager**
2. Start a new journey (e.g., "Kitchen Renovation")
3. Follow step-by-step guidance
4. Upload progress photos
5. Track completion percentage

## 🔧 Configuration

### Backend URL
- Default: `http://localhost:8000`
- Change in sidebar: **🔧 Backend Settings**
- Test connection with **"🔄 Test Connection"** button

### Chat Settings
- **Persona**: homeowner, diy_worker, contractor
- **Scenario**: diy_project_plan, contractor_quotes
- **Show Thinking**: Toggle AI thinking process visualization

## 📊 Logs & Debugging

### Execution Logs
- Click **"📊 Logs"** button in header
- View full API responses
- Debug request/response data

### Thinking Process
- Enable in settings
- See AI planning and task execution
- View tool invocations and context sources

## 🌟 Key Benefits

1. **Complete Platform Access** - All backend endpoints in one place
2. **User-Friendly Interface** - Intuitive navigation and controls
3. **Real-Time Feedback** - Streaming responses and progress indicators
4. **Rich Visualizations** - Images, comparisons, product recommendations
5. **Guest Mode Support** - Try features without registration
6. **Comprehensive Testing** - Test all backend functionality easily

## 🛠️ Technical Details

- **Framework**: Streamlit
- **Backend**: FastAPI (HomeView AI)
- **Authentication**: JWT tokens with optional guest mode
- **Streaming**: Server-Sent Events (SSE) for real-time responses
- **File Uploads**: Multipart form data for images and documents
- **API Integration**: All 9 backend routers fully integrated

## 📝 Notes

- Ensure backend is running before starting the app
- Some features require authentication
- Guest mode has limited functionality
- All transformations are saved to history
- Product recommendations use Google Grounding API

## 🐛 Troubleshooting

### Backend Connection Failed
- Verify backend is running on port 8000
- Check backend URL in settings
- Test connection with health check

### Authentication Errors
- Login with valid credentials
- Or use guest mode for public features
- Check token expiration

### Transformation Failures
- Ensure image is valid format (JPG, PNG)
- Check image size (< 10MB recommended)
- Verify backend has required API keys

## 🎉 Enjoy!

This comprehensive app gives you complete access to HomeView AI's powerful features. Explore, experiment, and transform your home improvement ideas into reality!

