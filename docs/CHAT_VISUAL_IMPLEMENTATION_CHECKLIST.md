# Chat Visual Enhancement - Implementation Checklist

## Overview
This checklist provides step-by-step instructions to add image generation to the chat experience.

**Estimated Time**: 2-3 days
**Difficulty**: Medium
**Impact**: High

---

## Phase 1: Backend Implementation (Day 1-2)

### Task 1.1: Add Visual Intent Classification
**File**: `backend/workflows/chat_workflow.py`
**Location**: Line 320-365 (in `_classify_intent` method)

- [ ] Add new intents to classification prompt:
  ```python
  - design_visualization: User wants to see design options/mockups
  - before_after: User wants to see transformations
  - material_comparison: User wants to compare materials visually
  - room_redesign: User wants to redesign a space
  ```

- [ ] Update intent detection keywords:
  ```python
  visual_keywords = [
      "show me", "visualize", "what would it look like",
      "can you generate", "create a mockup", "design options",
      "before and after", "transformation", "redesign",
      "compare", "options", "variations"
  ]
  ```

**Test**: Run chat with "show me what my bathroom would look like with modern tiles" - should classify as `design_visualization`

---

### Task 1.2: Implement Image Generation in Multimodal Node
**File**: `backend/workflows/chat_workflow.py`
**Location**: Line 874-876 (replace the TODO comment)

- [ ] Import required services:
  ```python
  from backend.services.design_transformation_service import DesignTransformationService
  from backend.services.imagen_service import ImagenService, ImageGenerationRequest
  ```

- [ ] Add image generation logic:
  ```python
  # 4. Image Generation for design concepts and visual aids
  if intent in ["design_idea", "design_visualization", "before_after", "room_redesign"]:
      try:
          logger.info(f"Generating images for intent: {intent}")
          
          # Check if user uploaded an image
          uploaded_image = state.get("uploaded_image_path")
          
          if uploaded_image:
              # Transform existing image
              design_service = DesignTransformationService()
              style = self._extract_style_from_message(user_message)
              
              images = await design_service.transform_room_style(
                  image=uploaded_image,
                  target_style=style,
                  num_variations=3
              )
              
              generated_images = [
                  {
                      "type": "transformation",
                      "url": img_path,
                      "style": style,
                      "caption": f"{style.title()} style transformation"
                  }
                  for img_path in images
              ]
          else:
              # Generate from description
              imagen_service = ImagenService()
              prompt = self._build_image_generation_prompt(user_message, ai_response)
              
              request = ImageGenerationRequest(
                  prompt=prompt,
                  num_images=3,
                  aspect_ratio="16:9"
              )
              
              result = await imagen_service.generate_images(request)
              
              if result.success:
                  generated_images = [
                      {
                          "type": "generated",
                          "url": img_path,
                          "caption": "AI-generated design concept"
                      }
                      for img_path in result.image_paths
                  ]
          
          logger.info(f"Generated {len(generated_images)} images")
          
      except Exception as e:
          logger.warning(f"Image generation failed: {e}")
          # Continue without images
  ```

**Test**: Send "show me modern bathroom designs" - should generate 3 images

---

### Task 1.3: Add Helper Methods
**File**: `backend/workflows/chat_workflow.py`
**Location**: After `_enrich_with_multimodal` method (around line 907)

- [ ] Add `_extract_style_from_message` method:
  ```python
  def _extract_style_from_message(self, message: str) -> str:
      """Extract design style from user message."""
      message_lower = message.lower()
      
      styles = {
          "modern": ["modern", "contemporary", "minimalist", "sleek"],
          "traditional": ["traditional", "classic", "timeless"],
          "rustic": ["rustic", "farmhouse", "country"],
          "industrial": ["industrial", "loft", "urban"],
          "scandinavian": ["scandinavian", "nordic", "scandi"],
          "bohemian": ["bohemian", "boho", "eclectic"]
      }
      
      for style, keywords in styles.items():
          if any(keyword in message_lower for keyword in keywords):
              return style
      
      return "modern"  # Default
  ```

- [ ] Add `_build_image_generation_prompt` method:
  ```python
  def _build_image_generation_prompt(self, user_message: str, ai_response: str) -> str:
      """Build image generation prompt from conversation context."""
      # Extract room type
      room_type = "room"
      message_lower = user_message.lower()
      
      if "bathroom" in message_lower:
          room_type = "bathroom"
      elif "kitchen" in message_lower:
          room_type = "kitchen"
      elif "bedroom" in message_lower:
          room_type = "bedroom"
      elif "living" in message_lower:
          room_type = "living room"
      
      # Extract style
      style = self._extract_style_from_message(user_message)
      
      # Build detailed prompt
      prompt = f"A beautiful {style} {room_type} interior design. "
      prompt += "Professional photography, well-lit, realistic, high quality, "
      prompt += "interior design magazine style. "
      
      # Add specific details from user message
      if "small" in message_lower:
          prompt += "Compact and space-efficient. "
      if "budget" in message_lower or "affordable" in message_lower:
          prompt += "Cost-effective materials. "
      if "luxury" in message_lower or "high-end" in message_lower:
          prompt += "Premium materials and finishes. "
      
      return prompt
  ```

**Test**: Call methods with sample messages - verify correct style extraction

---

### Task 1.4: Update API Response Model
**File**: `backend/api/chat.py`
**Location**: Line 88-95 (ChatMessageResponse class)

- [ ] Add `generated_images` field:
  ```python
  class ChatMessageResponse(BaseModel):
      """Chat message response."""
      conversation_id: str
      message_id: str
      response: str
      intent: str
      suggested_actions: List[dict] = []
      
      # NEW: Visual content
      generated_images: List[dict] = []  # Generated/transformed images
      youtube_videos: List[dict] = []    # Tutorial videos (already exists)
      web_sources: List[dict] = []       # Product links (already exists)
      
      metadata: dict = {}
  ```

- [ ] Update response construction in `send_message` endpoint (around line 1050):
  ```python
  return ChatMessageResponse(
      conversation_id=str(conversation.id),
      message_id=str(assistant_message.id),
      response=result.get("ai_response", ""),
      intent=result.get("intent", "question"),
      suggested_actions=result.get("suggested_actions", []),
      generated_images=result.get("generated_images", []),  # NEW
      youtube_videos=result.get("youtube_videos", []),
      web_sources=result.get("web_sources", []),
      metadata=result.get("response_metadata", {})
  )
  ```

**Test**: API response includes `generated_images` array

---

### Task 1.5: Add Image Upload Support
**File**: `backend/api/chat.py`
**Location**: Around line 950 (send_message endpoint)

- [ ] Add image upload parameter:
  ```python
  @router.post("/message", response_model=ChatMessageResponse)
  async def send_message(
      request: ChatMessageRequest,
      image: Optional[UploadFile] = File(None),  # NEW
      current_user: Optional[User] = Depends(get_current_user_optional),
      db: AsyncSession = Depends(get_async_db)
  ):
  ```

- [ ] Handle image upload:
  ```python
  # Handle image upload if provided
  uploaded_image_path = None
  if image:
      upload_dir = Path("uploads/chat") / str(conversation.id)
      upload_dir.mkdir(parents=True, exist_ok=True)
      
      file_extension = Path(image.filename).suffix
      image_filename = f"{uuid.uuid4()}{file_extension}"
      image_path = upload_dir / image_filename
      
      # Save image
      with open(image_path, "wb") as f:
          content = await image.read()
          f.write(content)
      
      uploaded_image_path = str(image_path)
      logger.info(f"Saved uploaded image to {uploaded_image_path}")
  ```

- [ ] Pass to workflow:
  ```python
  result = await chat_workflow.execute({
      "user_message": request.message,
      "conversation_id": str(conversation.id),
      "home_id": request.home_id,
      "user_id": str(current_user.id),
      "persona": request.persona,
      "scenario": request.scenario,
      "mode": request.mode,
      "uploaded_image_path": uploaded_image_path,  # NEW
  })
  ```

**Test**: Upload image via API - should save to `uploads/chat/{conversation_id}/`

---

## Phase 2: Frontend Implementation (Day 3)

### Task 2.1: Display Generated Images
**File**: `homeview-frontend/components/chat/ChatMessage.tsx` (or equivalent)

- [ ] Add image grid component:
  ```tsx
  {message.generated_images && message.generated_images.length > 0 && (
    <div className="generated-images-grid">
      {message.generated_images.map((img, idx) => (
        <div key={idx} className="generated-image-card">
          <img 
            src={img.url} 
            alt={img.caption}
            className="generated-image"
          />
          <p className="image-caption">{img.caption}</p>
          <div className="image-actions">
            <button onClick={() => openInStudio(img.url)}>
              Open in Design Studio
            </button>
            <button onClick={() => downloadImage(img.url)}>
              Download
            </button>
          </div>
        </div>
      ))}
    </div>
  )}
  ```

- [ ] Add CSS styling:
  ```css
  .generated-images-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .generated-image-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    overflow: hidden;
  }
  
  .generated-image {
    width: 100%;
    height: auto;
    display: block;
  }
  
  .image-caption {
    padding: 0.5rem;
    font-size: 0.875rem;
    color: #6b7280;
  }
  
  .image-actions {
    padding: 0.5rem;
    display: flex;
    gap: 0.5rem;
  }
  ```

**Test**: Generated images display in chat messages

---

### Task 2.2: Add Image Upload UI
**File**: `homeview-frontend/components/chat/ChatInput.tsx` (or equivalent)

- [ ] Add file input and preview:
  ```tsx
  const [uploadedImage, setUploadedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };
  
  const removeImage = () => {
    setUploadedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  ```

- [ ] Add UI elements:
  ```tsx
  <div className="chat-input-container">
    <input
      type="file"
      accept="image/*"
      onChange={handleImageUpload}
      ref={fileInputRef}
      style={{ display: 'none' }}
    />
    
    {imagePreview && (
      <div className="image-preview">
        <img src={imagePreview} alt="Upload preview" />
        <button onClick={removeImage}>×</button>
      </div>
    )}
    
    <div className="input-row">
      <button 
        onClick={() => fileInputRef.current?.click()}
        className="upload-button"
      >
        📷
      </button>
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Describe your project or upload a photo..."
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  </div>
  ```

**Test**: Upload image - should show preview before sending

---

## Testing Checklist

- [ ] **Unit Tests**: Test helper methods (`_extract_style_from_message`, `_build_image_generation_prompt`)
- [ ] **Integration Tests**: Test full workflow with image generation
- [ ] **API Tests**: Test chat endpoint with and without image upload
- [ ] **Frontend Tests**: Test image display and upload UI
- [ ] **E2E Tests**: Test complete user journey from upload to display

## Sample Test Conversations

1. **Text-only generation**:
   - Input: "Show me modern bathroom designs"
   - Expected: 3 generated images of modern bathrooms

2. **Image transformation**:
   - Input: [uploads bathroom photo] + "Make it modern"
   - Expected: 3 transformed versions of uploaded image

3. **Style comparison**:
   - Input: "Compare modern vs traditional kitchen styles"
   - Expected: 6 images (3 modern + 3 traditional)

## Rollout Plan

1. **Dev Environment**: Test with sample conversations
2. **Staging**: Beta test with internal team
3. **Production (10% users)**: A/B test with small user group
4. **Production (100%)**: Full rollout after validation

## Success Metrics

- [ ] 80%+ of design-related conversations include images
- [ ] Image generation completes in <5 seconds
- [ ] User engagement increases by 200%+
- [ ] Conversion to quotes increases by 150%+

---

**Ready to implement? Start with Task 1.1 and work through sequentially!**

