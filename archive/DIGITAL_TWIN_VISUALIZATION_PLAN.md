> Archived notice (2025-11-03)
>
> This document has been archived. Visualization and image-tagging features are reflected in code and current docs under `docs/`. See: docs/INDEX.md

# Digital Twin Visualization & Image Tagging Plan

## Overview
This document outlines the implementation plan for:
1. **Image-to-Room Tagging**: Relate uploaded room images to floor plan rooms
2. **Isometric Floor Plan Visualization**: 3D isometric view of the floor plan
3. **Image Gallery Display**: Show all customer-provided images organized by room
4. **Design Studio Integration**: Allow customers to select images for editing

---

## Phase 1: Image-to-Room Relationship & Tagging

### Current State
- Floor plans are analyzed and rooms are created in the database
- Room images are uploaded separately without explicit room assignment
- No automatic matching between uploaded images and floor plan rooms

### Implementation Steps

#### 1.1 Update Room Image Upload Flow
**File**: `backend/api/digital_twin.py`

Add optional `room_id` parameter to room image upload:
```python
@router.post("/rooms/{room_id}/images")
async def upload_room_image(
    room_id: str,
    file: UploadFile,
    room_type_hint: Optional[str] = None,  # NEW: Help AI identify room
    view_angle: Optional[str] = None,      # NEW: front, corner, ceiling, etc.
    db: AsyncSession = Depends(get_db)
):
    # Existing upload logic
    # AI will analyze image and confirm it matches the room
```

#### 1.2 AI-Powered Image-to-Room Matching
**File**: `backend/agents/digital_twin/room_analysis_agent.py`

Enhance the room analysis agent to:
1. Analyze the uploaded image
2. Extract room features (materials, fixtures, layout)
3. Compare with existing floor plan rooms
4. Suggest best matching room based on:
   - Room type (kitchen, bathroom, bedroom, etc.)
   - Approximate dimensions
   - Features detected (e.g., kitchen has appliances, bathroom has fixtures)
   - User-provided hints

**New Method**:
```python
async def match_image_to_room(
    self,
    image_path: str,
    available_rooms: List[Dict],
    room_type_hint: Optional[str] = None
) -> Dict:
    """
    Match an uploaded image to a room from the floor plan.
    
    Returns:
        {
            "matched_room_id": str,
            "confidence": float,
            "reasoning": str,
            "detected_room_type": str,
            "alternative_matches": List[Dict]
        }
    """
```

#### 1.3 Update Database Schema
**File**: `backend/models/home.py`

Add fields to `RoomImage` model:
```python
class RoomImage(Base, TimestampMixin):
    # Existing fields...
    
    # NEW: Matching metadata
    auto_matched = Column(Boolean, default=False)  # Was this auto-matched by AI?
    match_confidence = Column(Float)  # Confidence score of the match
    match_reasoning = Column(Text)  # Why AI matched this image to this room
    user_confirmed = Column(Boolean, default=False)  # Did user confirm the match?
    view_angle = Column(String(100))  # front, corner, ceiling, detail, etc.
```

#### 1.4 Update Streamlit UI
**File**: `streamlit_app.py`

Add room selection to image upload:
```python
def show_room_images_page():
    # After uploading floor plan, show detected rooms
    if st.session_state.get('room_ids'):
        st.subheader("📸 Upload Room Images")
        
        # Option 1: Manual room selection
        selected_room = st.selectbox(
            "Select Room (or let AI auto-match)",
            options=["Auto-detect"] + room_names
        )
        
        # Option 2: Batch upload with auto-matching
        uploaded_files = st.file_uploader(
            "Upload multiple room images",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for file in uploaded_files:
                # AI will analyze and suggest room match
                # User can confirm or override
```

---

## Phase 2: Isometric Floor Plan Visualization

### Goal
Create a 3D isometric view of the floor plan showing:
- Room layouts in 3D
- Walls, doors, windows
- Room labels
- Clickable rooms to view associated images

### Technology Options

#### Option A: Three.js (Recommended)
**Pros**: 
- Full 3D control
- Interactive camera
- Can add textures, lighting
- Large ecosystem

**Implementation**:
1. Convert floor plan data to 3D coordinates
2. Create wall meshes from room boundaries
3. Add floor and ceiling planes
4. Render doors and windows
5. Add room labels
6. Make rooms clickable

#### Option B: SVG Isometric Projection
**Pros**:
- Lighter weight
- Easier to implement
- Good for simple floor plans

**Implementation**:
1. Transform 2D coordinates to isometric projection
2. Draw walls as parallelograms
3. Add depth with shading
4. Render in SVG

#### Option C: Plotly 3D (Quick Start)
**Pros**:
- Python-native
- Works well with Streamlit
- Built-in interactivity

**Implementation**:
```python
import plotly.graph_objects as go

def create_isometric_floor_plan(rooms_data):
    """Create 3D isometric view using Plotly."""
    fig = go.Figure()
    
    for room in rooms_data:
        # Create 3D box for each room
        x, y, z = room['location']['x'], room['location']['y'], 0
        length, width = room['dimensions']['length_ft'], room['dimensions']['width_ft']
        
        # Add room as 3D mesh
        fig.add_trace(go.Mesh3d(
            x=[x, x+length, x+length, x, x, x+length, x+length, x],
            y=[y, y, y+width, y+width, y, y, y+width, y+width],
            z=[0, 0, 0, 0, 8, 8, 8, 8],  # 8ft ceiling height
            i=[0, 0, 0, 1, 1, 2],
            j=[1, 2, 4, 2, 5, 3],
            k=[2, 3, 5, 3, 6, 6],
            name=room['name'],
            opacity=0.7
        ))
    
    # Set isometric camera view
    fig.update_layout(
        scene=dict(
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            aspectmode='data'
        ),
        title="3D Floor Plan - Isometric View"
    )
    
    return fig
```

### Implementation Steps

#### 2.1 Create Floor Plan Converter
**File**: `backend/services/floor_plan_3d_converter.py`

```python
class FloorPlan3DConverter:
    """Convert 2D floor plan data to 3D coordinates for visualization."""
    
    def convert_to_3d(self, floor_plan_data: Dict) -> Dict:
        """
        Convert floor plan analysis to 3D visualization data.
        
        Returns:
            {
                "rooms": [...],  # 3D room meshes
                "walls": [...],  # Wall segments
                "doors": [...],  # Door positions
                "windows": [...],  # Window positions
                "bounds": {...}  # Overall dimensions
            }
        """
```

#### 2.2 Add Visualization Endpoint
**File**: `backend/api/digital_twin.py`

```python
@router.get("/homes/{home_id}/visualization/3d")
async def get_3d_visualization(
    home_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get 3D visualization data for floor plan."""
    # Fetch floor plan analysis
    # Convert to 3D coordinates
    # Return visualization-ready data
```

#### 2.3 Update Streamlit Digital Twin Page
**File**: `streamlit_app.py`

```python
def show_digital_twin_page():
    st.title("🏠 Digital Twin Visualization")
    
    # Tab 1: 3D Isometric View
    tab1, tab2, tab3 = st.tabs([
        "🎨 3D Floor Plan",
        "📸 Room Images",
        "📊 Analysis Data"
    ])
    
    with tab1:
        st.subheader("Isometric Floor Plan View")
        
        # Fetch 3D visualization data
        viz_data = get_3d_visualization(home_id)
        
        # Create Plotly 3D figure
        fig = create_isometric_floor_plan(viz_data)
        
        # Display interactive 3D plot
        st.plotly_chart(fig, use_container_width=True)
        
        # Room selector below the 3D view
        st.subheader("Select a room to view images")
        selected_room = st.selectbox(
            "Room",
            options=[r['name'] for r in viz_data['rooms']]
        )
    
    with tab2:
        st.subheader("📸 All Room Images")
        
        # Group images by room
        for room in rooms:
            with st.expander(f"{room['name']} ({len(room['images'])} images)"):
                cols = st.columns(3)
                for idx, img in enumerate(room['images']):
                    with cols[idx % 3]:
                        st.image(img['url'], caption=img['view_angle'])
                        if st.button(f"Edit", key=f"edit_{img['id']}"):
                            st.session_state.selected_image = img['id']
                            st.session_state.page = "design_studio"
                            st.rerun()
```

---

## Phase 3: Image Gallery & Organization

### Implementation

#### 3.1 Room Image Gallery Component
**File**: `streamlit_app.py`

```python
def render_room_image_gallery(room_data: Dict):
    """Render image gallery for a specific room."""
    st.subheader(f"📸 {room_data['name']} Images")
    
    images = room_data.get('images', [])
    
    if not images:
        st.info("No images uploaded for this room yet.")
        return
    
    # Display images in grid
    cols = st.columns(3)
    for idx, img in enumerate(images):
        with cols[idx % 3]:
            st.image(img['url'], use_column_width=True)
            
            # Image metadata
            st.caption(f"View: {img.get('view_angle', 'Unknown')}")
            st.caption(f"Uploaded: {img.get('created_at', 'N/A')}")
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎨 Edit", key=f"edit_{img['id']}"):
                    navigate_to_design_studio(img['id'])
            with col2:
                if st.button("🔍 Analyze", key=f"analyze_{img['id']}"):
                    show_image_analysis(img['id'])
```

---

## Phase 4: Design Studio Integration

### Goal
Allow customers to select an image and transition to design studio for editing.

### Implementation

#### 4.1 Add Design Studio Page
**File**: `streamlit_app.py`

```python
def show_design_studio_page():
    """Design studio for editing room images."""
    st.title("🎨 Design Studio")
    
    if 'selected_image' not in st.session_state:
        st.warning("Please select an image from the Digital Twin view.")
        return
    
    image_id = st.session_state.selected_image
    
    # Load image data
    image_data = get_room_image(image_id)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Original Image")
        st.image(image_data['url'], use_column_width=True)
        
        # Design tools will go here
        st.subheader("Design Tools")
        
        tool = st.selectbox(
            "Select Tool",
            ["Change Wall Color", "Replace Flooring", "Add Furniture", 
             "Change Lighting", "Virtual Staging"]
        )
        
        if tool == "Change Wall Color":
            color = st.color_picker("Select Wall Color")
            if st.button("Apply"):
                # Call AI to change wall color
                pass
    
    with col2:
        st.subheader("Room Info")
        st.write(f"**Room**: {image_data['room_name']}")
        st.write(f"**Type**: {image_data['room_type']}")
        st.write(f"**Dimensions**: {image_data['dimensions']}")
        
        st.subheader("AI Analysis")
        st.write("**Detected Materials:**")
        for material in image_data.get('materials', []):
            st.write(f"- {material}")
        
        st.write("**Detected Fixtures:**")
        for fixture in image_data.get('fixtures', []):
            st.write(f"- {fixture}")
```

---

## Implementation Priority

### Phase 1 (Week 1): Core Functionality
1. ✅ Fix RoomType enum (DONE)
2. Add image-to-room matching logic
3. Update database schema for image matching
4. Basic Streamlit UI for room selection

### Phase 2 (Week 2): Visualization
1. Implement Plotly 3D isometric view
2. Create floor plan 3D converter
3. Add visualization endpoint
4. Integrate into Streamlit

### Phase 3 (Week 3): Gallery & UX
1. Build room image gallery component
2. Add image organization by room
3. Improve UI/UX for image browsing

### Phase 4 (Week 4): Design Studio
1. Create design studio page
2. Add basic editing tools
3. Integrate AI image editing
4. Add save/export functionality

---

## Technical Dependencies

### Python Packages
```bash
pip install plotly  # For 3D visualization
pip install pillow  # Image processing
pip install numpy   # Coordinate transformations
```

### Frontend (if using Three.js)
```bash
npm install three
npm install @react-three/fiber
npm install @react-three/drei
```

---

## Next Steps

1. **Immediate**: Test the fixed RoomType enum with floor plan upload
2. **Short-term**: Implement image-to-room matching
3. **Medium-term**: Build isometric visualization
4. **Long-term**: Complete design studio integration
