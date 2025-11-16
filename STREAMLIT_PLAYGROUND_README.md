# HomeView AI - Streamlit Chat Playground

A universal, ChatGPT-style chat interface for testing the HomeView AI backend. Works for **everyone** (homeowners, contractors, DIY enthusiasts) without requiring authentication.

## Design Philosophy

**Universal & Guest-First**
- No login required - works for all users out of the box
- Test any persona (homeowner, contractor, DIY worker) or leave it universal
- Generate images, designs, cost estimates, DIY plans on demand
- Clean, ChatGPT/Claude-style interface with chat input at bottom

## Features

### 1. **Universal Chat** ✅
- Works in **guest mode** by default (no authentication needed)
- Supports all personas: homeowners, contractors, DIY workers
- Handles all query types: design ideas, cost estimates, DIY planning, contractor quotes
- Optional persona/scenario settings for context-aware responses

### 2. **Image & Design Generation** ✅
- Generate design transformations on demand
- View before/after images inline
- HD-quality image display
- Works without authentication

### 3. **Clickable Action Buttons** ✅
- Suggested actions rendered as clickable buttons
- One-click execution:
  - `get_detailed_estimate` - Get cost estimates
  - `find_products` - Find matching products
  - `generate_diy_guide` - Create DIY plans
  - `export_pdf` - Export plans to PDF
  - `start_contractor_quotes` - Get contractor quotes

### 4. **Rich Metadata Display**
- **Intent classification** - See what the AI understands
- **Generated images** - Design transformations inline
- **Web/product sources** - Clickable product links
- **Execution logs** - Toggle to see full JSON responses
- **PDF attachments** - Download DIY plans

### 5. **ChatGPT-Style UX**
- Clean, modern interface
- Chat input at bottom (like ChatGPT/Claude)
- Collapsible settings panel (⚙️ Settings button)
- Optional execution logs (📊 Logs button)
- Simulated streaming for smooth UX

## Installation

```bash
# Install Streamlit if not already installed
pip install streamlit requests
```

## Usage

### 1. Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Run the Streamlit playground

```bash
# From repo root
streamlit run streamlit_homeview_chat.py
```

The playground will open in your browser at `http://localhost:8501`.

## Configuration

### Settings Panel (⚙️ Button)

**Context (Optional):**
- **Persona** - `(none)`, `homeowner`, `diy_worker`, or `contractor`
  - Leave as `(none)` for universal chat
  - Set to get persona-specific responses
- **Scenario** - `(none)`, `diy_project_plan`, or `contractor_quotes`
  - Leave as `(none)` for universal chat
  - Set for context-aware suggestions

**Advanced:**
- **Home ID** - Optional home context for personalized responses
- **Room ID** - Optional room context
- **Backend URL** - FastAPI backend URL (default: `http://localhost:8000`)

**💡 Tip:** Leave persona and scenario as `(none)` for universal chat that works for all queries.

## Testing Scenarios

### Universal Queries (No Setup Needed)

**Homeowner Queries:**
- "I want to renovate my kitchen. What should I consider?"
- "Show me modern bathroom design ideas"
- "How much does it cost to paint a 12x15 living room?"
- "Find me affordable flooring options for my bedroom"

**DIY Planning:**
- "Create a DIY plan for painting my living room"
- "What tools do I need to install laminate flooring?"
- "Make a shopping list for a bathroom renovation"
- "Give me step-by-step instructions for tiling a backsplash"

**Design & Images:**
- "Show me design ideas for a modern kitchen"
- "Transform my living room into a minimalist space"
- "What colors work well for a small bedroom?"
- "Generate a farmhouse-style kitchen design"

**Contractor Queries:**
- "I need quotes for a kitchen renovation"
- "Find contractors in Vancouver for bathroom remodeling"
- "What's the typical timeline for a full home renovation?"

**Cost Estimates:**
- "What's the estimated cost for painting a 12x15 room?"
- "How much does a kitchen renovation cost in Vancouver?"
- "Compare costs: DIY vs hiring a contractor for flooring"

### Using Action Buttons

After the AI responds, you'll see action buttons like:
- **Generate DIY Guide** - Creates a detailed step-by-step plan
- **Export as PDF** - Downloads the plan as a PDF
- **Get Detailed Estimate** - Provides itemized cost breakdown
- **Find Products** - Shows matching products with links
- **Start Contractor Quotes** - Connects you with contractors

Just click the button to execute the action!

## Architecture

### Endpoints Used

- **`/api/v1/chat/message`** - Main chat endpoint (guest mode)
  - Uses ChatWorkflow with Gemini tools
  - Returns full response with metadata
  - Works without authentication
  - Supports all personas and scenarios

- **`/api/v1/chat/execute-action`** - Execute suggested actions
  - Used for action button clicks
  - Handles PDF export, cost estimates, product matching, etc.
  - Works in guest mode

### Response Structure

```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "response": "AI response text",
  "intent": "diy_planning",
  "suggested_actions": [
    {
      "action": "export_pdf",
      "label": "Export as PDF",
      "description": "Download your DIY plan as a PDF"
    }
  ],
  "generated_images": [
    {
      "url": "/uploads/images/...",
      "caption": "Modern kitchen design"
    }
  ],
  "web_sources": [
    {
      "title": "Benjamin Moore Paint",
      "url": "https://..."
    }
  ],
  "metadata": {
    "intent": "diy_planning",
    "diy_plan": { ... },
    "attachments": [ ... ]
  }
}
```

## Troubleshooting

### "Error calling backend: Connection refused"
- Make sure the FastAPI backend is running at `http://localhost:8000`
- Start the backend: `cd backend && uvicorn main:app --reload --port 8000`
- Check the "Backend URL" in Settings (⚙️ button)

### Action buttons not appearing
- Make sure the backend returned suggested actions in the response
- Check the Logs panel (📊 button) to see the raw API response
- Some queries may not trigger suggested actions (this is normal)

### PDF export fails
- Make sure you've generated a DIY plan first
- The backend needs the DIY plan in conversation history to export
- Check that the backend has the required PDF export dependencies installed

### Images not displaying
- Check that the backend URL is correct in Settings
- Make sure the backend has the image files in the `uploads/` directory
- View the Logs panel to see the image URLs returned by the API

### No response from AI
- Check the Logs panel (📊 button) to see the error details
- Make sure the backend has the Gemini API key configured
- Check backend logs for errors: `cd backend && tail -f logs/app.log`

## Next Steps

After testing with the Streamlit playground, you can:
1. Return to the Next.js frontend implementation
2. Complete Phase 2 backend cleanup (remove legacy DIY action handlers)
3. Continue with Phase 3 and Phase 4 of the API consolidation plan

