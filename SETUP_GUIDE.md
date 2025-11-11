# 🚀 HomeView AI - Quick Setup Guide

Get HomeView AI running locally in 5 minutes!

---

## ✅ Prerequisites

Before you start, make sure you have:

- ✅ **Python 3.11+** installed ([Download](https://www.python.org/downloads/))
- ✅ **Node.js 18+** installed ([Download](https://nodejs.org/))
- ✅ **Git** installed ([Download](https://git-scm.com/))
- ✅ **Google Gemini API Key** ([Get one free](https://aistudio.google.com/app/apikey))

---

## 📥 Step 1: Clone the Repository

```bash
git clone https://github.com/ram660/augment.git
cd augment
```

---

## 🐍 Step 2: Set Up Backend

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

```bash
# Copy the example environment file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux
```

**Edit `.env` and add your Gemini API key:**

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Initialize Database

```bash
# Run database migrations (creates SQLite database)
alembic upgrade head
```

### Start Backend Server

```bash
# Start the FastAPI backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

✅ **Backend is now running!**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/monitoring/health`

---

## 🎨 Step 3: Set Up Frontend (Choose One)

### Option A: Main Frontend (Next.js) - Recommended

```bash
# Open a new terminal
cd homeview-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ **Frontend is now running at:** `http://localhost:3000`

### Option B: Design Studio (React + Vite)

```bash
# Open a new terminal
cd frontend-studio

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ **Design Studio is now running at:** `http://localhost:5173`

---

## 🎉 Step 4: Start Using HomeView AI!

### Try the Design Studio

1. Open `http://localhost:3000` (or `http://localhost:5173` for Design Studio)
2. Upload a room photo
3. Select a transformation type (paint, flooring, staging, etc.)
4. Click "Transform" and see AI-generated results in seconds!

### Try the API

Visit `http://localhost:8000/docs` to explore all 25+ API endpoints interactively.

**Example: Transform Paint Color**

```bash
curl -X POST "http://localhost:8000/api/v1/design/transform-prompted-upload" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data_url": "data:image/jpeg;base64,...",
    "prompt": "paint the walls soft gray",
    "num_variations": 2
  }'
```

---

## 🔧 Common Issues & Solutions

### Issue: "Module not found" error

**Solution:** Make sure you activated the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Issue: "Database connection error"

**Solution:** Run database migrations:
```bash
alembic upgrade head
```

### Issue: "API key not found"

**Solution:** Make sure you created `.env` file and added your Gemini API key:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

### Issue: "Port already in use"

**Solution:** Change the port in the command:
```bash
# Backend on different port
uvicorn backend.main:app --reload --port 8001

# Frontend on different port
npm run dev -- --port 3001
```

---

## 📚 Next Steps

### Explore the Documentation

- **[Complete README](README.md)** - Full project documentation
- **[Design Studio Docs](docs/DESIGN_STUDIO_INDEX.md)** - All Design Studio features
- **[API Reference](docs/DESIGN_STUDIO_API_REFERENCE.md)** - Complete API documentation
- **[Development Guide](README.md#-development)** - Development tips & tricks

### Try These Features

1. **Design Studio** - Transform any room with 20+ AI tools
2. **Virtual Staging** - Add furniture with real product suggestions
3. **Digital Twin** - Create a complete home model
4. **AI Chat** - Ask questions about home improvement
5. **Journey Management** - Plan and track projects

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html
```

### View Database

```bash
# Print digital twin summary
python -m scripts.print_twin_summary

# Export database to CSV
python -m scripts.export_db_to_csv
```

---

## 🆘 Need Help?

- **Documentation**: [docs/INDEX.md](docs/INDEX.md)
- **API Docs**: `http://localhost:8000/docs`
- **Issues**: [GitHub Issues](https://github.com/ram660/augment/issues)

---

## 🎯 Quick Reference

### Backend Commands

```bash
# Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
alembic upgrade head

# Run tests
pytest

# View API docs
# Open http://localhost:8000/docs
```

### Frontend Commands

```bash
# Main Frontend (Next.js)
cd homeview-frontend
npm install
npm run dev
# Open http://localhost:3000

# Design Studio (React + Vite)
cd frontend-studio
npm install
npm run dev
# Open http://localhost:5173
```

### Environment Variables

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional (defaults work for development)
USE_SQLITE=true
DATABASE_URL=sqlite:///./homevision.db
API_PORT=8000
ENVIRONMENT=development
DEBUG=true
```

---

## ✨ What You Can Do

### Design Studio Features

- 🎨 **Paint Walls** - Any color, any finish
- 🪵 **Change Flooring** - Hardwood, tile, carpet, vinyl
- 🗄️ **Transform Kitchens** - Cabinets, countertops, backsplash
- 🛋️ **Virtual Staging** - Add furniture with real products
- ✂️ **Precision Editing** - Masking, segmentation, polygon tools
- 💬 **Freeform Prompts** - Natural language transformations
- 📸 **Multi-Angle Views** - See from different perspectives
- ✨ **Image Enhancement** - 2x upscale, quality boost

### Digital Twin Features

- 📐 **Floor Plan Analysis** - Automatic room detection
- 🏢 **Multi-Floor Support** - Manage multiple levels
- 📸 **Room Documentation** - Link photos to rooms
- 🔗 **Intelligent Linking** - Connect plans, rooms, images

### AI Chat Features

- 💬 **Natural Language** - Ask questions in plain English
- 🖼️ **Image Understanding** - Upload photos for advice
- 📝 **Project Planning** - Step-by-step guides
- 💰 **Cost Estimation** - Budget planning

---

## 🚀 You're All Set!

HomeView AI is now running locally. Start transforming rooms, creating digital twins, and planning your home improvement projects!

**Happy building! 🏠✨**

---

**Built with ❤️ using Google Gemini, LangChain, and FastAPI**

