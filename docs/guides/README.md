# 📖 Guides & Tutorials

This folder contains all how-to guides, tutorials, and best practices for HomeVision AI development.

---

## 📂 Available Guides

### [GETTING_STARTED.md](GETTING_STARTED.md)
**Developer Onboarding Guide**

Complete setup and first steps for new developers:
- Environment setup (Python, dependencies)
- API key configuration
- Running your first agent
- Testing and debugging
- Common troubleshooting

**Start here if:** You're new to the project and want to get up and running.

---

### [GEMINI_MODEL_CONFIGURATION.md](GEMINI_MODEL_CONFIGURATION.md)
**Complete Gemini 2.5 Flash Guide**

Everything you need to know about using Gemini models:
- Model selection rationale
- Configuration examples
- Usage patterns (text, vision, image generation)
- Best practices and optimization
- Monitoring and debugging
- Performance tuning

**Start here if:** You're working with AI models or building agents.

---

### [PROMPT_ENGINEERING_GUIDE.md](PROMPT_ENGINEERING_GUIDE.md)
**Universal Prompt Engineering**

Comprehensive guide to prompts for home improvement:
- Core prompt structures
- Room types and configurations
- Transformation categories (paint, flooring, cabinetry, etc.)
- Design styles library
- Quality control patterns
- 2600+ lines of tested prompts

**Start here if:** You're building image generation or transformation features.

---

### [AGENT_PROMPTS_GUIDE.md](AGENT_PROMPTS_GUIDE.md)
**Specialized Agent Prompts**

Detailed prompts for DIY and Contractor agents:
- Safety assessment prompts
- Project planning prompts
- Cost estimation prompts
- Compliance checking prompts
- 4000+ lines of agent-specific prompts

**Start here if:** You're building specialized agents or need domain-specific prompts.

---

## 🎯 Guides by Task

### **Setting Up Development Environment**
1. [GETTING_STARTED.md](GETTING_STARTED.md) - Complete setup
2. [GEMINI_MODEL_CONFIGURATION.md](GEMINI_MODEL_CONFIGURATION.md) - AI configuration

### **Building AI Agents**
1. [GEMINI_MODEL_CONFIGURATION.md](GEMINI_MODEL_CONFIGURATION.md) - Model usage
2. [AGENT_PROMPTS_GUIDE.md](AGENT_PROMPTS_GUIDE.md) - Agent prompts
3. [PROMPT_ENGINEERING_GUIDE.md](PROMPT_ENGINEERING_GUIDE.md) - Prompt patterns

### **Working with Images**
1. [PROMPT_ENGINEERING_GUIDE.md](PROMPT_ENGINEERING_GUIDE.md) - Image transformation
2. [GEMINI_MODEL_CONFIGURATION.md](GEMINI_MODEL_CONFIGURATION.md) - Vision API usage

### **Testing and Debugging**
1. [GETTING_STARTED.md](GETTING_STARTED.md) - Testing guide
2. [GEMINI_MODEL_CONFIGURATION.md](GEMINI_MODEL_CONFIGURATION.md) - Debugging tips

---

## 💡 Best Practices

### **Code Quality**
- Follow PEP 8 style guide
- Write docstrings for all functions
- Add type hints
- Write tests for new features

### **Agent Development**
- Start with simple prompts, iterate
- Test with multiple scenarios
- Monitor token usage
- Handle errors gracefully

### **Prompt Engineering**
- Be specific and detailed
- Include preservation requirements
- Test with various inputs
- Document successful patterns

### **Performance**
- Cache frequently used results
- Batch process when possible
- Monitor API rate limits
- Optimize token usage

---

## 🔧 Quick Reference

### **Environment Variables**
```env
GOOGLE_API_KEY=your_api_key_here
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_VISION_MODEL=gemini-2.5-flash
GEMINI_IMAGE_GEN_MODEL=gemini-2.5-flash
```

**Note:** Using Gemini 2.5 Flash for all tasks (text, vision, image generation)

### **Common Commands**
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_agents.py

# Start development server (future)
uvicorn backend.main:app --reload
```

### **Agent Template**
```python
from backend.agents.base import BaseAgent, AgentConfig, AgentRole

class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            role=AgentRole.CUSTOM,
            description="My custom agent",
            temperature=0.7
        )
        super().__init__(config)
    
    async def process(self, input_data):
        # Your logic here
        pass
```

---

## 📚 Additional Resources

### **Official Documentation**
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs)
- [LangChain Docs](https://docs.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

### **Internal Documentation**
- [Architecture](../architecture/README.md) - System design
- [Business Plan](../business/business.md) - Business context
- [Feature Catalog](../reference/FEATURE_CATALOG.md) - Available features

---

## 🤝 Contributing to Guides

When adding new guides:

1. **Clear Structure** - Use headings, code blocks, examples
2. **Practical Examples** - Include working code snippets
3. **Troubleshooting** - Add common issues and solutions
4. **Keep Updated** - Update when features change
5. **Link Related Docs** - Cross-reference other documentation

---

## 🆘 Getting Help

- **Setup Issues**: See [GETTING_STARTED.md](GETTING_STARTED.md)
- **AI/Model Issues**: See [GEMINI_MODEL_CONFIGURATION.md](GEMINI_MODEL_CONFIGURATION.md)
- **Prompt Issues**: See [PROMPT_ENGINEERING_GUIDE.md](PROMPT_ENGINEERING_GUIDE.md)
- **Architecture Questions**: See [../architecture/README.md](../architecture/README.md)

---

**Happy Coding! 🚀**

