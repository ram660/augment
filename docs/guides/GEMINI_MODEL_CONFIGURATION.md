# Gemini 2.0 Flash - Model Configuration

## Overview

HomeVision AI uses **Google Gemini 2.0 Flash** as the primary AI model for all tasks. This unified approach simplifies the architecture while leveraging Gemini's powerful multimodal capabilities.

---

## Model Selection

### **Gemini 2.0 Flash**
- **Model ID**: `gemini-2.0-flash`
- **Use Cases**: 
  - Text generation and reasoning
  - Vision analysis and image understanding
  - Conversational AI
  - Intent classification
  - Content generation

### **Gemini 2.0 Flash with Imagen**
- **Model ID**: `gemini-2.0-flash` (with Imagen capabilities)
- **Use Cases**:
  - Photorealistic image generation
  - Room visualization and rendering
  - Style transfer
  - Material swapping
  - Before/after comparisons

### **Text Embedding 004**
- **Model ID**: `text-embedding-004`
- **Use Cases**:
  - Semantic search
  - Product matching
  - Contractor matching
  - Similarity calculations

---

## Why Gemini 2.0 Flash?

### 1. **Multimodal Capabilities**
- Single model handles text, vision, and image generation
- Seamless integration across different tasks
- Consistent performance and behavior

### 2. **Performance**
- Fast inference times (< 2 seconds for most tasks)
- Efficient token usage
- Low latency for real-time applications

### 3. **Cost-Effective**
- Generous free tier for development
- Competitive pricing for production
- Single model reduces complexity and costs

### 4. **Quality**
- State-of-the-art performance on vision tasks
- High-quality text generation
- Photorealistic image generation with Imagen

### 5. **Official Support**
- Excellent documentation
- Active development and updates
- Google's commitment to the platform

---

## Configuration

### Environment Variables

```env
# API Key
GOOGLE_API_KEY=your_api_key_here

# Model Configuration
GEMINI_TEXT_MODEL=gemini-2.0-flash
GEMINI_VISION_MODEL=gemini-2.0-flash
GEMINI_IMAGE_GEN_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004

# Generation Settings
GEMINI_DEFAULT_TEMPERATURE=0.7
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT_SECONDS=60
```

### Python Configuration

```python
from backend.integrations.gemini import GeminiClient, GeminiConfig

# Default configuration (uses environment variables)
client = GeminiClient()

# Custom configuration
config = GeminiConfig(
    api_key="your_api_key",
    default_text_model="gemini-2.0-flash",
    default_vision_model="gemini-2.0-flash",
    default_image_gen_model="gemini-2.0-flash",
    default_temperature=0.7
)
client = GeminiClient(config)
```

---

## Usage Examples

### Text Generation

```python
from backend.integrations.gemini import GeminiClient

client = GeminiClient()

# Simple text generation
response = await client.generate_text(
    prompt="Explain the benefits of modern farmhouse kitchen design",
    temperature=0.7
)
print(response)
```

### Vision Analysis

```python
# Analyze a room image
response = await client.analyze_image(
    image="path/to/kitchen.jpg",
    prompt="Analyze this kitchen and identify all visible products and materials",
    temperature=0.3  # Lower temperature for factual analysis
)
print(response)
```

### Image Generation

```python
# Generate a design visualization
images = await client.generate_image(
    prompt="Modern farmhouse kitchen with white shaker cabinets, quartz countertops, and subway tile backsplash",
    num_images=3,
    aspect_ratio="16:9"
)

for i, img in enumerate(images):
    img.save(f"design_{i}.jpg")
```

### Chat Conversation

```python
# Multi-turn conversation
messages = [
    ("user", "I want to remodel my kitchen"),
    ("assistant", "Great! What's your budget?"),
    ("user", "$25,000"),
]

response = await client.chat(
    messages=messages,
    temperature=0.8,
    system_instruction="You are a helpful home improvement assistant"
)
print(response)
```

### Embeddings

```python
# Generate embeddings for semantic search
texts = [
    "Modern farmhouse kitchen with white cabinets",
    "Industrial loft kitchen with exposed brick",
    "Coastal kitchen with blue accents"
]

embeddings = await client.get_embeddings(texts)
# embeddings is a list of 768-dimensional vectors
```

---

## Agent-Specific Configurations

### Conversation Agent
- **Model**: `gemini-2.0-flash`
- **Temperature**: 0.7 (balanced creativity and consistency)
- **Use Case**: Natural language understanding and response generation

### Vision Analysis Agent
- **Model**: `gemini-2.0-flash`
- **Temperature**: 0.3 (factual, precise analysis)
- **Use Case**: Room analysis, product identification, dimension extraction

### Product Discovery Agent
- **Model**: `gemini-2.0-flash`
- **Temperature**: 0.5 (balanced)
- **Use Case**: Product search and recommendations

### Cost Intelligence Agent
- **Model**: `gemini-2.0-flash`
- **Temperature**: 0.2 (precise calculations)
- **Use Case**: BOM generation, cost estimation

### Rendering Agent
- **Model**: `gemini-2.0-flash` with Imagen
- **Temperature**: 0.8 (creative image generation)
- **Use Case**: Photorealistic visualizations

---

## Best Practices

### 1. **Temperature Settings**

- **0.0 - 0.3**: Factual, deterministic tasks (analysis, calculations)
- **0.4 - 0.7**: Balanced tasks (conversation, recommendations)
- **0.8 - 1.0**: Creative tasks (design generation, brainstorming)

### 2. **Prompt Engineering**

```python
# Good: Specific, structured prompt
prompt = """Analyze this kitchen image and provide:
1. Room dimensions (estimated)
2. Style classification
3. Visible products and materials
4. Condition assessment

Format your response as JSON."""

# Bad: Vague prompt
prompt = "Tell me about this kitchen"
```

### 3. **Error Handling**

```python
try:
    response = await client.generate_text(prompt)
except Exception as e:
    logger.error(f"Gemini API error: {str(e)}")
    # Fallback logic
```

### 4. **Rate Limiting**

- Free tier: 60 requests per minute
- Monitor usage with `client.count_tokens()`
- Implement caching for repeated queries

### 5. **Safety Settings**

```python
# Safety settings are enabled by default
# Blocks harmful content in 4 categories:
# - Hate speech
# - Dangerous content
# - Sexually explicit
# - Harassment
```

---

## Performance Optimization

### 1. **Caching**

```python
# Cache frequently used results
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_product_recommendations(query: str):
    return await client.generate_text(f"Find products for: {query}")
```

### 2. **Batch Processing**

```python
# Process multiple images in parallel
import asyncio

images = ["kitchen1.jpg", "kitchen2.jpg", "kitchen3.jpg"]
tasks = [client.analyze_image(img, prompt) for img in images]
results = await asyncio.gather(*tasks)
```

### 3. **Token Management**

```python
# Check token count before sending
token_count = client.count_tokens(prompt)
if token_count > 30000:  # Gemini 2.0 Flash limit
    # Split or summarize prompt
    pass
```

---

## Monitoring & Debugging

### 1. **Logging**

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Logs are automatically generated by GeminiClient
# Check logs for API calls, errors, and performance
```

### 2. **Token Usage Tracking**

```python
# Track token usage for cost estimation
total_tokens = 0

for prompt in prompts:
    tokens = client.count_tokens(prompt)
    total_tokens += tokens
    
print(f"Total tokens used: {total_tokens}")
```

### 3. **Response Time Monitoring**

```python
import time

start = time.time()
response = await client.generate_text(prompt)
duration = time.time() - start

logger.info(f"Response time: {duration:.2f}s")
```

---

## Migration Notes

### From Previous Configuration

If you were using different Gemini models before:

**Old:**
- `gemini-2.0-flash-exp` → Now: `gemini-2.0-flash`
- `gemini-2.0-flash-thinking-exp` → Now: `gemini-2.0-flash`
- `gemini-2.0-flash-exp` (Imagen) → Now: `gemini-2.0-flash` (Imagen)

**Changes:**
- All models unified to `gemini-2.0-flash`
- No code changes required (handled by configuration)
- Same API interface and capabilities

---

## Resources

### Official Documentation
- [Gemini API Overview](https://ai.google.dev/gemini-api/docs)
- [Imagen Documentation](https://ai.google.dev/gemini-api/docs/imagen)
- [Image Understanding](https://ai.google.dev/gemini-api/docs/image-understanding)
- [Text Generation](https://ai.google.dev/gemini-api/docs/text-generation)

### API Reference
- [Python SDK](https://github.com/google/generative-ai-python)
- [API Limits](https://ai.google.dev/gemini-api/docs/quota)
- [Pricing](https://ai.google.dev/pricing)

### Community
- [Google AI Forum](https://discuss.ai.google.dev/)
- [GitHub Issues](https://github.com/google/generative-ai-python/issues)

---

**Last Updated:** 2025-11-01

