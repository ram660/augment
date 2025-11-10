# Chat Image Generation Improvements

## Problem Statement

The current chat experience is too text-heavy and generic, similar to ChatGPT. For a home improvement platform, **visual results are critical**. Users expect to see:
- Before/after visualizations
- Design mockups
- Material comparisons
- Step-by-step visual guides
- Room transformations

## Current State

### ✅ What We Have
- **Gemini Imagen API integration** (`backend/integrations/gemini/client.py`)
- **ImagenService** for image generation (`backend/services/imagen_service.py`)
- **DesignTransformationService** for room transformations (`backend/services/design_transformation_service.py`)
- **Design API endpoints** (`backend/api/design.py`)
- **Design Studio** with canvas interface (`frontend-studio/`)

### ❌ What's Missing
- **Chat workflow doesn't call image generation services**
- **No automatic image generation based on user intent**
- **Suggested actions don't trigger visual results**
- **No image upload handling in chat**
- **No before/after comparisons in chat responses**

## Proposed Solution

### 1. Enhanced Intent Classification

Add visual-specific intents to the chat workflow:

```python
# New intents to add:
- "design_visualization"  # User wants to see design options
- "before_after"          # User wants to see transformations
- "material_comparison"   # User wants to compare materials visually
- "step_visualization"    # User wants visual step-by-step guide
```

**Trigger phrases:**
- "show me", "visualize", "what would it look like"
- "can you generate", "create a mockup", "design options"
- "before and after", "transformation", "redesign"
- "compare", "options", "variations"

### 2. Image Generation Node in Chat Workflow

Add a new node to `backend/workflows/chat_workflow.py`:

```python
async def generate_visuals(self, state: ChatState) -> ChatState:
    """Generate visual content based on intent and context."""
    
    intent = state.get("intent")
    user_message = state.get("user_message")
    
    # Check if visual generation is needed
    if intent not in ["design_visualization", "before_after", "material_comparison"]:
        return state
    
    # Check if user uploaded an image
    uploaded_image = state.get("uploaded_image_path")
    
    if not uploaded_image:
        # Generate from scratch based on description
        result = await self._generate_from_description(state)
    else:
        # Transform existing image
        result = await self._transform_image(state, uploaded_image)
    
    state["generated_images"] = result.get("images", [])
    state["visual_aids"] = result.get("visual_aids", [])
    
    return state
```

### 3. Image Upload Support in Chat

**Backend changes:**
- Add `image` field to `ChatMessageRequest` in `backend/api/chat.py`
- Handle multipart/form-data in chat endpoint
- Save uploaded images to `uploads/chat/{conversation_id}/`
- Pass image path to chat workflow

**Frontend changes:**
- Add image upload button to chat input
- Show image preview before sending
- Display uploaded images in chat history

### 4. Visual Response Format

Modify chat response to include images:

```python
class ChatMessageResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str  # Text response
    intent: str
    suggested_actions: List[dict] = []
    
    # NEW: Visual content
    images: List[dict] = []  # Generated/transformed images
    visual_aids: List[dict] = []  # Diagrams, comparisons, etc.
    
    metadata: dict = {}
```

**Image format:**
```python
{
    "type": "generated" | "before_after" | "comparison" | "diagram",
    "url": "/uploads/chat/...",
    "thumbnail_url": "/uploads/chat/.../thumb.jpg",
    "caption": "Modern bathroom design with subway tiles",
    "metadata": {
        "transformation_type": "style_transfer",
        "style": "modern",
        "generation_time_ms": 3500
    }
}
```

### 5. Automatic Image Generation Triggers

**Scenario 1: User describes a room**
```
User: "I want to refresh my small bathroom. It's 5x8 feet. The vanity is okay but everything else looks dated."

Bot Response:
- Text: "I can help you visualize some refresh options..."
- Action: Automatically generate 3-4 design variations
- Images: [modern_bathroom_1.jpg, modern_bathroom_2.jpg, ...]
```

**Scenario 2: User uploads a photo**
```
User: [uploads bathroom photo] "Here's my bathroom. Can you show me what it would look like with modern finishes?"

Bot Response:
- Text: "Here are some modern design options for your bathroom..."
- Action: Transform uploaded image with different styles
- Images: [before_after_1.jpg, before_after_2.jpg, ...]
```

**Scenario 3: User asks for material comparison**
```
User: "What would subway tiles vs. large format tiles look like in my bathroom?"

Bot Response:
- Text: "Here's a comparison of subway tiles and large format tiles..."
- Action: Generate side-by-side comparisons
- Images: [subway_tiles.jpg, large_format.jpg, comparison.jpg]
```

### 6. Integration with Design Studio

Add a "Open in Design Studio" button for generated images:

```python
suggested_actions.append({
    "action": "open_in_studio",
    "label": "Open in Design Studio",
    "description": "Edit and refine this design in the full studio",
    "data": {
        "image_url": generated_image_url,
        "room_id": room_id,
        "transformation_params": {...}
    }
})
```

## Implementation Plan

### Phase 1: Core Image Generation (Week 1)
- [ ] Add image upload support to chat endpoint
- [ ] Add `generate_visuals` node to chat workflow
- [ ] Integrate ImagenService with chat workflow
- [ ] Update ChatMessageResponse to include images
- [ ] Add visual intent classification

### Phase 2: Frontend Integration (Week 2)
- [ ] Add image upload UI to chat input
- [ ] Display generated images in chat messages
- [ ] Add image gallery/lightbox for viewing
- [ ] Add "Open in Design Studio" action
- [ ] Show loading states for image generation

### Phase 3: Advanced Features (Week 3)
- [ ] Before/after comparison view
- [ ] Material comparison side-by-side
- [ ] Image variation carousel
- [ ] Save generated images to user's home
- [ ] Share generated designs

### Phase 4: Optimization (Week 4)
- [ ] Cache generated images
- [ ] Optimize image generation prompts
- [ ] Add image generation progress tracking
- [ ] Implement retry logic for failed generations
- [ ] Add image quality feedback loop

## Example User Journeys

### Journey 1: Bathroom Refresh
```
User: "I want to refresh my bathroom this weekend. Budget is $800."
Bot: "Great! Can you share a photo of your bathroom so I can show you some options?"

User: [uploads photo]
Bot: "Here are 3 design options within your budget:"
     [Shows 3 generated images with different styles]
     "Which style do you prefer?"

User: "I like option 2"
Bot: "Perfect! Here's a detailed plan for that style..."
     [Shows step-by-step visual guide with materials list]
```

### Journey 2: Kitchen Redesign
```
User: "Show me what my kitchen would look like with white cabinets"
Bot: "I'd love to help! Please upload a photo of your current kitchen."

User: [uploads photo]
Bot: "Here's your kitchen with white cabinets:"
     [Shows before/after comparison]
     "Would you like to see other cabinet colors too?"

User: "Yes, show me gray and navy blue"
Bot: [Shows 3 variations: white, gray, navy blue]
     "Here are all three options. The estimated cost for each is..."
```

## Success Metrics

- **Image Generation Rate**: % of conversations that include generated images
- **User Engagement**: Time spent viewing generated images
- **Conversion Rate**: % of users who proceed to Design Studio or request quotes
- **Image Quality**: User feedback on generated images (thumbs up/down)
- **Generation Speed**: Average time to generate images (target: <5 seconds)

## Technical Considerations

### Performance
- Generate images asynchronously to avoid blocking chat response
- Show text response immediately, stream images as they're generated
- Use thumbnail previews for faster loading
- Cache common transformations

### Cost Management
- Track image generation costs per user
- Implement rate limiting (e.g., 10 images per conversation)
- Use lower resolution for previews, full resolution on demand
- Batch similar requests

### Error Handling
- Graceful fallback if image generation fails
- Show text-only response with option to retry
- Log failures for debugging
- Provide alternative suggestions if generation fails

## Next Steps

1. **Review this document** with the team
2. **Prioritize features** based on user feedback
3. **Create detailed technical specs** for Phase 1
4. **Set up tracking** for success metrics
5. **Begin implementation** of Phase 1

