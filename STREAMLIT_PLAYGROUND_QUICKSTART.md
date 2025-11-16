# HomeView AI Chat Playground - Quick Start

## 🧠 Your Personal AI Assistant - Watch Me Think!

This playground shows you **exactly how the AI works** - from understanding your request, to planning tasks, to executing them step-by-step. It's like having a personal assistant who explains their thought process!

## 🚀 Get Started in 3 Steps

### 1. Start the Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Run the Playground
```bash
# From repo root
streamlit run streamlit_homeview_chat.py
```

### 3. Start Chatting!
The playground opens at `http://localhost:8501`

**Watch the AI:**
- 🧠 **Think** - See intent classification and task planning
- 📋 **Plan** - View the breakdown of complex requests
- 🔧 **Execute** - Watch tools being called in real-time
- ✅ **Complete** - Get results with full transparency

---

## 💬 What Can You Ask?

### Homeowner Queries
- "I want to renovate my kitchen. What should I consider?"
- "Show me modern bathroom design ideas"
- "How much does it cost to paint a 12x15 living room?"

### DIY Planning
- "Create a DIY plan for painting my living room"
- "What tools do I need to install laminate flooring?"
- "Make a shopping list for a bathroom renovation"

### Design & Images
- "Show me design ideas for a modern kitchen"
- "Transform my living room into a minimalist space"
- "Generate a farmhouse-style kitchen design"

### Contractor Queries
- "I need quotes for a kitchen renovation"
- "Find contractors in Vancouver for bathroom remodeling"

### Cost Estimates
- "What's the estimated cost for painting a 12x15 room?"
- "Compare costs: DIY vs hiring a contractor for flooring"

---

## 🎯 Key Features

### 🧠 AI Thinking Process (NEW!)
- **See the AI think in real-time** - Watch intent classification, task planning, and execution
- **Task breakdown** - Complex requests are broken into clear steps
- **Tool execution** - See which specialized tools are called and why
- **Workflow visualization** - Track progress through each stage
- **Toggle on/off** - Control visibility in Settings (⚙️)

### ✅ Universal & Guest-First
- **No login required** - works for everyone out of the box
- Test any persona or leave it universal
- All features accessible without authentication

### ✅ ChatGPT-Style Interface
- Clean, modern UI
- Chat input at bottom
- Collapsible settings (⚙️ button)
- Optional execution logs (📊 button)
- **Status indicators** - See "AI is thinking..." with progress steps

### ✅ Rich Responses
- **Images** - Design transformations inline
- **Action Buttons** - One-click execution (DIY plans, PDFs, estimates)
- **Product Links** - Clickable recommendations
- **Metadata** - Intent, sources, and execution details

### ✅ Streaming Experience
- Smooth typing effect like ChatGPT
- Real-time status updates
- Progress indicators for actions
- No authentication needed

---

## ⚙️ Optional Settings

Click the **⚙️ Settings** button to configure:

- **Persona** - Leave as `(none)` for universal chat, or set to `homeowner`, `diy_worker`, `contractor`
- **Scenario** - Leave as `(none)` for universal chat, or set to `diy_project_plan`, `contractor_quotes`
- **Home ID / Room ID** - Optional context for personalized responses
- **Backend URL** - Change if backend is not at `http://localhost:8000`

**💡 Tip:** Leave everything as default for universal chat!

---

## 📊 Execution Logs

Click the **📊 Logs** button to see:
- Full JSON API responses
- Intent classification
- Tool execution details
- Debugging information

---

## 🎬 Example Workflow - Watch the AI Work!

### Example 1: DIY Planning
1. **You ask:** "Create a DIY plan for painting my living room"
2. **AI thinks:**
   - 🎯 Detects intent: `diy_project_plan`
   - 📋 Plans tasks: Analyze room → Generate steps → Estimate materials
   - 🔧 Calls tools: `intelligence_generate_diy_guide`
3. **AI responds** with a detailed plan
4. **You click:** "Export as PDF" action button
5. **AI executes:**
   - 📄 Finding DIY plan in history...
   - 📝 Formatting content...
   - 🎨 Generating PDF...
   - ✅ Done!
6. **Download** your PDF

### Example 2: Design Ideas
1. **You ask:** "Show me modern kitchen design ideas"
2. **AI thinks:**
   - 🎯 Detects intent: `design_inspiration`
   - 📋 Plans: Search trends → Generate images → Find products
   - 🔧 Calls tools: `imagen_generate_design`, `google_grounding_search`
3. **AI responds** with images and product recommendations
4. **You see:** Before/after images, clickable product links, cost estimates

---

## 🆘 Troubleshooting

### Backend not responding?
```bash
# Make sure backend is running
cd backend
uvicorn main:app --reload --port 8000
```

### Action buttons not showing?
- Some queries don't trigger actions (this is normal)
- Check the 📊 Logs panel to see the raw response

### Images not displaying?
- Check Settings (⚙️) to verify backend URL
- Make sure backend has image files in `uploads/` directory

---

## 🎉 That's It!

You now have a universal, ChatGPT-style interface for testing HomeView AI.

**No authentication. No setup. Just chat!**

For more details, see [STREAMLIT_PLAYGROUND_README.md](STREAMLIT_PLAYGROUND_README.md)

