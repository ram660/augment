# Getting Started with HomeVision AI

This guide will help you set up and start developing with the HomeVision AI agentic platform.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11 or higher** installed
- **Git** for version control
- **PostgreSQL 14+** (for production; optional for initial development)
- **Redis 7+** (for production; optional for initial development)
- **Google Gemini API key** ([Get one here](https://aistudio.google.com/app/apikey))

## Step 1: Clone and Setup

```bash
# Navigate to your project directory
cd c:\Users\ramma\Documents\augment-projects\augment

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy the example environment file
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env and add your Gemini API key
# You can use any text editor
notepad .env  # Windows
# nano .env  # macOS/Linux
```

**Required environment variables:**

```env
# Minimum required for testing
GOOGLE_API_KEY=your_gemini_api_key_here
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it into your `.env` file

**Note:** The Gemini API has a generous free tier perfect for development!

## Step 3: Test the Installation

Run the test script to verify everything is working:

```bash
python test_agents.py
```

You should see output like:

```
============================================================
HomeVision AI - Agent System Tests
============================================================

✓ API key found: AIzaSyB...

============================================================
Testing Gemini Client
============================================================

✓ Gemini client initialized successfully

Test: Text generation
Response: HomeVision AI is an AI-powered platform that connects homeowners...

✓ All Gemini client tests passed!

============================================================
Testing Conversation Agent
============================================================

Test 1: Simple greeting
Success: True
Intent: design_request
Response: That's exciting! I'd love to help you plan your kitchen remodel...
Specialist Agent: design_orchestrator

...
```

## Step 4: Understanding the Architecture

### Project Structure

```
homevision-ai/
├── backend/
│   ├── agents/              # All agent implementations
│   │   ├── base/           # Base agent classes
│   │   │   ├── agent.py    # BaseAgent class
│   │   │   └── memory.py   # Memory management
│   │   ├── homeowner/      # Homeowner-facing agents
│   │   │   ├── conversation_agent.py
│   │   │   └── vision_agent.py
│   │   ├── contractor/     # Contractor-facing agents (future)
│   │   └── marketplace/    # Marketplace agents (future)
│   ├── integrations/       # External API integrations
│   │   └── gemini/        # Gemini API wrapper
│   │       ├── client.py  # GeminiClient class
│   │       └── __init__.py
│   └── workflows/          # LangGraph workflows (future)
├── tests/                  # Test suites
├── docs/                   # Documentation
├── .env                    # Environment variables (create from .env.example)
├── requirements.txt        # Python dependencies
└── test_agents.py         # Test script
```

### Key Components

1. **Base Agent (`backend/agents/base/agent.py`)**
   - Abstract base class for all agents
   - Handles configuration, memory, error handling, retries
   - All agents inherit from this

2. **Gemini Client (`backend/integrations/gemini/client.py`)**
   - Unified interface to Gemini models
   - Text generation, vision analysis, image generation, embeddings
   - Handles API calls, retries, error handling

3. **Conversation Agent (`backend/agents/homeowner/conversation_agent.py`)**
   - Natural language interface
   - Intent classification
   - Routes to specialist agents
   - Maintains conversation context

4. **Vision Agent (`backend/agents/homeowner/vision_agent.py`)**
   - Image analysis using Gemini Vision
   - Room dimension extraction
   - Style classification
   - Product identification

## Step 5: Create Your First Agent

Let's create a simple custom agent:

```python
# my_first_agent.py
import asyncio
from backend.agents.base import BaseAgent, AgentConfig, AgentRole, AgentResponse
from backend.integrations.gemini import GeminiClient

class GreetingAgent(BaseAgent):
    """A simple agent that generates personalized greetings."""
    
    def __init__(self):
        config = AgentConfig(
            name="greeting_agent",
            role=AgentRole.CONVERSATION,
            description="Generates personalized greetings",
            temperature=0.9  # Higher temperature for creative greetings
        )
        super().__init__(config)
        self.gemini = GeminiClient()
    
    async def process(self, input_data):
        """Generate a personalized greeting."""
        name = input_data.get("name", "friend")
        style = input_data.get("style", "friendly")
        
        prompt = f"Generate a {style} greeting for someone named {name}. Keep it under 50 words."
        
        greeting = await self.gemini.generate_text(prompt)
        
        return AgentResponse(
            agent_name=self.name,
            agent_role=self.role,
            success=True,
            data={"greeting": greeting}
        )

# Test it
async def main():
    agent = GreetingAgent()
    
    result = await agent.execute({
        "name": "Sarah",
        "style": "professional"
    })
    
    print(f"Success: {result.success}")
    print(f"Greeting: {result.data['greeting']}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")

asyncio.run(main())
```

Run it:

```bash
python my_first_agent.py
```

## Step 6: Explore the Conversation Agent

Try having a conversation with the AI:

```python
# conversation_demo.py
import asyncio
from backend.agents.homeowner import ConversationAgent

async def main():
    agent = ConversationAgent()
    
    # Simulate a conversation
    messages = [
        "Hi! I want to renovate my bathroom.",
        "I have about $15,000 to spend.",
        "I like modern minimalist style with lots of white.",
        "What should I do first?"
    ]
    
    for msg in messages:
        print(f"\nYou: {msg}")
        
        result = await agent.execute({
            "message": msg,
            "user_id": "demo_user"
        })
        
        print(f"AI: {result.data['response']}")
        print(f"(Intent: {result.data['intent']})")

asyncio.run(main())
```

## Step 7: Test Vision Analysis

If you have room photos, test the vision agent:

```python
# vision_demo.py
import asyncio
from backend.agents.homeowner import VisionAnalysisAgent
from pathlib import Path

async def main():
    agent = VisionAnalysisAgent()
    
    # Analyze an image
    image_path = "path/to/your/room/photo.jpg"
    
    if Path(image_path).exists():
        result = await agent.execute({
            "image": image_path,
            "analysis_type": "comprehensive"
        })
        
        if result.success:
            import json
            print(json.dumps(result.data['analysis'], indent=2))
        else:
            print(f"Error: {result.error}")
    else:
        print(f"Image not found: {image_path}")

asyncio.run(main())
```

## Next Steps

### For Development

1. **Read the Architecture Docs**
   - [Enhanced Agentic Architecture](./ENHANCED_AGENTIC_ARCHITECTURE.md)
   - [Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md)

2. **Implement More Agents**
   - Product Discovery Agent
   - Cost Intelligence Agent
   - Design Orchestrator Agent

3. **Build LangGraph Workflows**
   - Design request workflow
   - Contractor matching workflow
   - Project management workflow

4. **Set Up Database**
   - Install PostgreSQL
   - Run migrations
   - Create data models

5. **Build API Layer**
   - FastAPI endpoints
   - WebSocket for real-time collaboration
   - Authentication

### For Testing

1. **Unit Tests**
   ```bash
   pytest tests/
   ```

2. **Integration Tests**
   - Test agent interactions
   - Test workflows
   - Test API endpoints

3. **Load Testing**
   - Test with multiple concurrent users
   - Measure response times
   - Optimize performance

### For Production

1. **Set Up Infrastructure**
   - PostgreSQL database
   - Redis cache
   - File storage (S3)

2. **Configure Services**
   - Stripe for payments
   - Email service
   - Monitoring (Sentry)

3. **Deploy**
   - Docker containers
   - Kubernetes orchestration
   - CI/CD pipeline

## Common Issues

### "No API key found"

Make sure you've:
1. Created a `.env` file (copy from `.env.example`)
2. Added your Gemini API key
3. Named it `GOOGLE_API_KEY` or `GEMINI_API_KEY`

### "Module not found"

Make sure you've:
1. Activated your virtual environment
2. Installed all dependencies: `pip install -r requirements.txt`

### "Import errors"

Make sure you're running Python from the project root directory.

## Resources

- **Gemini API Docs**: https://ai.google.dev/gemini-api/docs
- **LangChain Docs**: https://docs.langchain.com
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com

## Getting Help

- Check the documentation in the `docs/` folder
- Review example code in `test_agents.py`
- Read the architecture documents

---

**Ready to build the future of home improvement? Let's go! 🚀**

