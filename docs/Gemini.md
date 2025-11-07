# HomeView AI — Gemini Integration Guide (Official Docs + Patterns)

This page is our single source of truth for how we integrate Google’s Gemini API in HomeView AI. All links point to the official documentation. Keep this page up‑to‑date as we add capabilities.

## Core official docs
- Core Gemini API: https://ai.google.dev/gemini-api/docs
- Thinking / Reasoning: https://ai.google.dev/gemini-api/docs/thinking
- Structured output (JSON): https://ai.google.dev/gemini-api/docs/structured-output
- Function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Long context: https://ai.google.dev/gemini-api/docs/long-context
- Google Search grounding: https://ai.google.dev/gemini-api/docs/google-search
- Maps grounding: https://ai.google.dev/gemini-api/docs/maps-grounding
- URL context: https://ai.google.dev/gemini-api/docs/url-context
- File search: https://ai.google.dev/gemini-api/docs/file-search
- Imagen (text-to-image): https://ai.google.dev/gemini-api/docs/imagen
- Image generation/editing (Gemini native): https://ai.google.dev/gemini-api/docs/image-generation
- Image understanding (Vision): https://ai.google.dev/gemini-api/docs/image-understanding

## Model choices we use
- Text: gemini-2.5-flash (fast) or gemini-2.5-pro (higher quality when needed)
- Vision understanding: gemini-2.5-flash (multimodal)
- Image generation & editing: gemini-2.5-flash-image (native image model)
- Embeddings: models/text-embedding-004

Notes:
- Use Gemini native image editing for “preserve original, change X” tasks. Avoid Imagen for editing; Imagen is text-to-image.
- Prefer structured outputs for any JSON response we display or store.

## Where things live in code
- Gemini client wrapper: backend/integrations/gemini/client.py
  - Image editing: edit_image()
  - Image understanding: analyze_design()
  - Grounded products: suggest_products_with_grounding() (uses Google Search tool + structured output)
- Transformation API: backend/api/design.py
  - Endpoints: /api/v1/design/transform-prompted, /transform-prompted-upload
  - Drift guard and strict-mode prompting
  - Calls Gemini for image editing and product grounding

## Patterns and snippets (Python)

### 1) Google Search grounding (official SDK)
Reference: https://ai.google.dev/gemini-api/docs/google-search

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)
grounding_tool = types.Tool(google_search=types.GoogleSearch())

config = types.GenerateContentConfig(
    tools=[grounding_tool],
    temperature=0.3,
)
# IMPORTANT: Do NOT set response_mime_type when using tools (google_search).
# If you need structure, instruct the model to return JSON in text and parse it,
# or use function calling (without google_search) as a fallback.

resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=(
        "Suggest 3 sage-green wall paint products with buy URLs. "
        "Return ONLY JSON: {\"products\":[{\"name\":string,\"url\":string}]}"
    ),
    config=config,
)
print(resp.text)  # JSON-like text to be parsed
```

### 2) Structured output (force JSON)
Reference: https://ai.google.dev/gemini-api/docs/structured-output

```python
from google import genai
client = genai.Client(api_key=GEMINI_API_KEY)

schema = {
  "type": "object",
  "properties": {
    "colors": {"type": "array", "items": {"type": "string"}},
    "styles": {"type": "array", "items": {"type": "string"}},
  },
  "required": ["colors"]
}

resp = client.models.generate_content(
  model="gemini-2.5-flash",
  contents="Extract colors and styles in JSON from this description...",
  config={
    "response_mime_type": "application/json",
    "response_json_schema": schema,
  },
)
print(resp.text)
```

### 3) Native image editing (preserve original)
Reference: https://ai.google.dev/gemini-api/docs/image-generation

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=GEMINI_API_KEY)
img = Image.open("room.jpg")

resp = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[img, "Repaint walls to soft sage green. Preserve everything else exactly."],
    config=types.GenerateContentConfig(response_modalities=["Image"]),
)
# Extract inline image from response.candidates[0].content.parts
```

## Best practices
- Always reference official docs linked above for the latest syntax and supported models.
- For product suggestions: use Google Search grounding + structured output to guarantee URLs.
- Preserve original images: constrain prompts explicitly and keep drift guard enabled in API.
- Use lower temperatures for analysis/extraction.
- Validate all model JSON before using it.

## Env configuration
- GOOGLE_API_KEY or GEMINI_API_KEY must be set (backend service)
- Consider enabling a per-env drift threshold (e.g., DESIGN_DRIFT_THRESHOLD) if needed

## Future additions
- Function calling for agent workflows: https://ai.google.dev/gemini-api/docs/function-calling
- URL context for retailer catalogs: https://ai.google.dev/gemini-api/docs/url-context
- File search for large spec documents: https://ai.google.dev/gemini-api/docs/file-search
- Maps grounding for contractor discovery: https://ai.google.dev/gemini-api/docs/maps-grounding

