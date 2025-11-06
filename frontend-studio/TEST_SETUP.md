# Studio Setup Test

## Manual Testing Steps

Since the automated terminal launch is having issues, please follow these manual steps:

### 1. Open a NEW PowerShell/Command Prompt

### 2. Navigate to the frontend-studio directory
```bash
cd C:\Users\ramma\Documents\augment-projects\augment\frontend-studio
```

### 3. Run the dev server
```bash
npm run dev
```

### 4. Expected Output
You should see something like:
```
  VITE v5.4.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### 5. Open Browser
Navigate to: **http://localhost:3000**

### 6. What You Should See

- Header with "🏠 HomeVision AI Studio"
- Home selector dropdown (should load homes from database)
- Left sidebar with layers
- Center canvas with floor plan and rooms
- Right chat panel

### 7. Test the Chat

1. Click on a room node on the canvas
2. Type a question in the chat: "What materials are in this room?"
3. Press Enter
4. You should get a response from the AI

### Troubleshooting

If you see errors:

1. **"No homes found"** - Run the import script first:
   ```bash
   python import_complete_home_data.py
   ```

2. **"Cannot connect to backend"** - Make sure backend is running:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Vite errors** - Reinstall dependencies:
   ```bash
   cd frontend-studio
   rm -rf node_modules
   npm install
   ```

## API Endpoints Being Used

- `GET /api/digital-twin/homes` - List all homes
- `GET /api/digital-twin/homes/{home_id}` - Get home details
- `POST /api/digital-twin/chat` - Chat with AI

All endpoints are proxied through Vite (see vite.config.js).

