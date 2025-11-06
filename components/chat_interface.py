"""
Chat Interface Component
Claude-like conversational UI for home queries
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


API_BASE_URL = "http://localhost:8000/api/digital-twin"


def _format_int_or_dash(val: Any) -> str:
    """Return thousands-formatted int or '—' if None/invalid."""
    try:
        if val is None:
            return "—"
        # Accept ints and floats but display as int with thousands sep
        return f"{int(val):,}"
    except Exception:
        return "—"


def _format_pct_or_dash(val: Any) -> str:
    """Return percentage string (0-100%) or '—' if None/invalid.

    Accepts values in [0,1] or already in [0,100].
    """
    try:
        if val is None:
            return "—"
        fval = float(val)
        pct = fval * 100.0 if 0.0 <= fval <= 1.0 else fval
        return f"{pct:.0f}%"
    except Exception:
        return "—"


def show_chat_interface():
    """Display the UI with visual selection on top and chat below."""

    # Ensure home data is loaded
    if st.session_state.home_id and not st.session_state.home_data:
        with st.spinner("Loading your home data..."):
            st.session_state.home_data = fetch_home_data(st.session_state.home_id)

    # Initialize selection state
    st.session_state.setdefault('selected_floor_index', None)
    st.session_state.setdefault('selected_floor_plan_id', None)
    st.session_state.setdefault('selected_room_id', None)
    st.session_state.setdefault('selected_room_image_ids', set())
    st.session_state.setdefault('room_cache', {})  # room_id -> details

    # Sidebar with home context
    with st.sidebar:
        show_home_context_sidebar()

    # Top: Floor plan and images selector
    show_visual_selector()

    # Divider before chat
    st.markdown("---")

    # Main chat area below selectors
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div style=\"text-align: center; padding: 1rem 0 0.5rem 0;\">
        <h1 style=\"margin: 0;\">💬 Chat with HomeVision AI</h1>
        <p style=\"color: #666; margin-top: 0.25rem;\">Your questions will use the selected room/images (if any)</p>
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    display_chat_history()

    # Show suggested prompts if no chat history
    if not st.session_state.chat_history:
        show_suggested_prompts()

    # Chat input at the bottom
    show_chat_input()

    st.markdown('</div>', unsafe_allow_html=True)


def show_home_context_sidebar():
    """Show home information and quick actions in sidebar."""
    
    st.markdown("### 🏠 Your Home")
    
    if st.session_state.home_id:
        # Fetch home data if not already loaded
        if not st.session_state.home_data:
            st.session_state.home_data = fetch_home_data(st.session_state.home_id)
        
        data = st.session_state.home_data
        
        if data:
            # Home name
            st.markdown(f"**{data.get('basic_info', {}).get('name', 'My Home')}**")
            
            # Quick stats
            st.markdown("---")
            st.markdown("#### 📊 Quick Stats")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rooms", data.get('total_rooms', 0))
                st.metric("Images", data.get('total_images', 0))
            with col2:
                sq_ft_raw = data.get('basic_info', {}).get('square_footage')
                st.metric("Sq Ft", _format_int_or_dash(sq_ft_raw))
                completeness_raw = data.get('digital_twin_completeness')
                st.metric("Complete", _format_pct_or_dash(completeness_raw))
            
            # Quick actions
            st.markdown("---")
            st.markdown("#### ⚡ Quick Actions")
            
            if st.button("📐 View Floor Plan", use_container_width=True):
                add_system_message("Here's your floor plan visualization...")
                # TODO: Show floor plan
            
            if st.button("📸 View All Images", use_container_width=True):
                add_system_message("Here are all your room images...")
                # TODO: Show images
            
            if st.button("🎨 Open Design Studio", use_container_width=True):
                add_system_message("Opening design studio...")
                # TODO: Open design studio
            
            if st.button("📊 View Full Report", use_container_width=True):
                add_system_message("Generating comprehensive home report...")
                # TODO: Generate report
            
            # Settings
            st.markdown("---")
            if st.button("⚙️ Setup New Home", use_container_width=True):
                if st.confirm("Start fresh with a new home?"):
                    st.session_state.current_view = 'setup'
                    st.session_state.setup_step = 1
                    st.rerun()
    else:
        st.warning("No home connected")
        if st.button("🏡 Set Up Home", use_container_width=True):
            st.session_state.current_view = 'setup'
            st.rerun()


def display_chat_history():
    """Display all chat messages."""
    
    for message in st.session_state.chat_history:
        role = message['role']
        content = message['content']
        timestamp = message.get('timestamp', '')
        
        if role == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <div style="font-weight: 600; margin-bottom: 0.5rem;">You</div>
                <div>{content}</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.5rem;">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div style="font-weight: 600; margin-bottom: 0.5rem; color: #667eea;">🏠 HomeVision AI</div>
                <div>{content}</div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 0.5rem;">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)


def show_suggested_prompts():
    """Show suggested prompts to get started."""
    
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem;">
            Here are some things you can ask me:
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💡 What materials are in my selected room?", use_container_width=True):
            handle_user_message("What materials are in my selected room?")
        
        if st.button("🔧 What fixtures need replacement?", use_container_width=True):
            handle_user_message("What fixtures need replacement?")
        
        if st.button("📐 Show me details for the selected floor", use_container_width=True):
            handle_user_message("Show me details for the selected floor")
    
    with col2:
        if st.button("🎨 Suggest improvements for my selected room", use_container_width=True):
            handle_user_message("Suggest improvements for my selected room")
        
        if st.button("💰 Estimate renovation costs", use_container_width=True):
            handle_user_message("Estimate renovation costs for my home")
        
        if st.button("🏠 Give me a summary of my home", use_container_width=True):
            handle_user_message("Give me a summary of my home")


def show_chat_input():
    """Show the chat input field."""
    
    # Create a form for the chat input
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Ask me anything about your home...",
                label_visibility="collapsed",
                key="chat_input"
            )
        
        with col2:
            submitted = st.form_submit_button("Send", use_container_width=True, type="primary")
        
        if submitted and user_input:
            handle_user_message(user_input)
            st.rerun()


def handle_user_message(message: str):
    """Process user message and generate AI response."""
    
    # Add user message to history
    timestamp = datetime.now().strftime("%I:%M %p")
    st.session_state.chat_history.append({
        'role': 'user',
        'content': message,
        'timestamp': timestamp
    })
    
    # Generate AI response (augment with current selection context)
    with st.spinner("🤖 Thinking..."):
        context = build_selection_context()
        if context:
            message_with_ctx = f"[CONTEXT] {context}\n\n{message}"
        else:
            message_with_ctx = message
        response = generate_ai_response(message_with_ctx)
    
    # Add AI response to history
    st.session_state.chat_history.append({
        'role': 'assistant',
        'content': response,
        'timestamp': timestamp
    })


def generate_ai_response(user_message: str) -> str:
    """
    Generate AI response based on user message and home data using LangChain agent.
    """

    # Fetch home data
    home_data = st.session_state.home_data
    home_id = st.session_state.home_id

    # Debug: Check if we have home data
    if not home_data:
        st.warning("⚠️ No home data loaded. Fetching now...")
        home_data = fetch_home_data(home_id)
        st.session_state.home_data = home_data

    # Prepare conversation history (last 10 messages)
    conversation_history = st.session_state.chat_history[-10:] if st.session_state.chat_history else []

    try:
        # Call the AI chat endpoint
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": user_message,
                "home_id": home_id,
                "conversation_history": conversation_history
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'I apologize, but I could not generate a response.')
        else:
            return f"I encountered an error (Status {response.status_code}). Please try again."

    except requests.exceptions.Timeout:
        return "The request timed out. Please try asking a simpler question."
    except Exception as e:
        st.error(f"Error communicating with AI: {str(e)}")
        # Fallback to simple responses
        return generate_fallback_response(user_message, home_data)


def generate_fallback_response(user_message: str, home_data: Optional[Dict[str, Any]]) -> str:
    """
    Generate fallback response if AI endpoint fails.
    Simple keyword-based responses using home data.
    """

    if not home_data:
        return "I don't have any information about your home yet. Please complete the setup process first."

    # Simple keyword-based responses
    message_lower = user_message.lower()
    
    # Kitchen queries
    if 'kitchen' in message_lower:
        rooms = home_data.get('rooms', [])
        kitchen_rooms = [r for r in rooms if 'kitchen' in r.get('room_type', '').lower()]
        
        if kitchen_rooms:
            kitchen = kitchen_rooms[0]
            materials = kitchen.get('materials', [])
            fixtures = kitchen.get('fixtures', [])
            
            response = f"**Your Kitchen Analysis:**\n\n"
            response += f"I found {len(materials)} materials and {len(fixtures)} fixtures in your kitchen.\n\n"
            
            if materials:
                response += "**Materials:**\n"
                for mat in materials[:5]:
                    response += f"- {mat.get('name', 'Unknown')}: {mat.get('category', 'N/A')}\n"
            
            if fixtures:
                response += "\n**Fixtures:**\n"
                for fix in fixtures[:5]:
                    response += f"- {fix.get('name', 'Unknown')}: {fix.get('type', 'N/A')}\n"
            
            return response
        else:
            return "I couldn't find a kitchen in your floor plan. Would you like to upload more images?"
    
    # Floor plan queries
    elif 'floor plan' in message_lower or 'layout' in message_lower:
        total_rooms = home_data.get('total_rooms', 0)
        rooms = home_data.get('rooms', [])
        
        response = f"**Your Floor Plan:**\n\n"
        response += f"Your home has {total_rooms} rooms:\n\n"
        
        for idx, room in enumerate(rooms[:10], 1):
            room_type = room.get('room_type', 'Unknown').replace('_', ' ').title()
            dimensions = room.get('dimensions', {})
            area = dimensions.get('area_sqft', 'N/A')
            response += f"{idx}. {room_type} - {area} sq ft\n"
        
        return response
    
    # Summary queries
    elif 'summary' in message_lower or 'overview' in message_lower:
        basic_info = home_data.get('basic_info', {})

        response = f"**Home Summary:**\n\n"
        response += f"**Name:** {basic_info.get('name', 'N/A')}\n"
        response += f"**Type:** {basic_info.get('home_type', 'N/A').replace('_', ' ').title()}\n"
        sq_ft_summary = basic_info.get('square_footage')
        response += f"**Size:** {_format_int_or_dash(sq_ft_summary)} sq ft\n"
        response += f"**Bedrooms:** {basic_info.get('num_bedrooms', 0)}\n"
        response += f"**Bathrooms:** {basic_info.get('num_bathrooms', 0)}\n"
        response += f"**Year Built:** {basic_info.get('year_built', 'N/A')}\n\n"
        response += f"**Digital Twin Status:**\n"
        response += f"- Total Rooms: {home_data.get('total_rooms', 0)}\n"
        response += f"- Images Uploaded: {home_data.get('total_images', 0)}\n"
        completeness = home_data.get('digital_twin_completeness')
        response += f"- Completeness: {_format_pct_or_dash(completeness)}\n"

        return response
    
    # Improvement suggestions
    elif 'improve' in message_lower or 'suggest' in message_lower or 'recommend' in message_lower:
        return """**Improvement Suggestions:**

Based on your home data, here are some recommendations:

1. **Kitchen Upgrade** - Consider updating countertops and backsplash for a modern look
2. **Bathroom Refresh** - Replace old fixtures with water-efficient models
3. **Lighting Enhancement** - Add LED lighting for energy savings
4. **Flooring Update** - Refinish hardwood floors or install new flooring

Would you like detailed information about any of these suggestions?"""
    
    # Cost estimates
    elif 'cost' in message_lower or 'estimate' in message_lower or 'budget' in message_lower:
        sq_ft = home_data.get('basic_info', {}).get('square_footage') or 2000

        return f"""**Renovation Cost Estimates:**

Based on your home size ({sq_ft:,} sq ft):

- **Minor Kitchen Remodel:** $15,000 - $25,000
- **Bathroom Renovation:** $10,000 - $20,000
- **Flooring Replacement:** $8,000 - $15,000
- **Painting (Interior):** $3,000 - $6,000
- **Lighting Upgrades:** $2,000 - $5,000

**Total Estimated Range:** $38,000 - $71,000

These are rough estimates. Would you like a detailed breakdown for any specific area?"""
    
    # Default response
    else:
        return f"""I understand you're asking about: "{user_message}"

I can help you with:
- 🏠 Home details and summaries
- 📐 Floor plan information
- 🎨 Material and fixture details
- 💡 Improvement suggestions
- 💰 Cost estimates
- 🔍 Room-specific queries

Could you rephrase your question or choose from the suggestions above?"""


def build_selection_context() -> str:
    """Build a compact text context from current visual selection for the chat.

    Returns a string like:
      Selected floor: 2 (floor_plan_id=...); room_id=...; image_ids=[...]
    or empty string if nothing selected.
    """
    parts: List[str] = []
    sf = st.session_state.get('selected_floor_index')
    if sf is not None:
        parts.append(f"Selected floor: {sf}")
    fpid = st.session_state.get('selected_floor_plan_id')
    if fpid:
        parts.append(f"floor_plan_id={fpid}")
    rid = st.session_state.get('selected_room_id')
    if rid:
        parts.append(f"room_id={rid}")
    img_ids = list(st.session_state.get('selected_room_image_ids') or [])
    if img_ids:
        parts.append(f"image_ids={img_ids}")
    return "; ".join(parts)


def show_visual_selector():
    """Render floor plan thumbnails and a room image gallery selector above the chat."""
    data = st.session_state.home_data
    if not data:
        st.info("Set up your home to see floor plans and images here.")
        return

    st.markdown("### 🗺️ Floor plans and room images")

    # Floor plans row
    fps: List[Dict[str, Any]] = (data.get('floor_plans') or [])
    if fps:
        cols = st.columns(max(2, min(4, len(fps))))
        for i, fp in enumerate(fps):
            with cols[i % len(cols)]:
                img = fp.get('image_url') or fp.get('image_uri') or ''
                name = fp.get('name') or f"Floor {fp.get('floor_level', '?')}"
                st.caption(name)
                if img:
                    st.image(img, use_column_width=True)
                sel = st.button(
                    f"Select Floor {fp.get('floor_level', '')}",
                    key=f"sel_fp_{i}",
                    use_container_width=True
                )
                if sel:
                    st.session_state.selected_floor_index = fp.get('floor_level')
                    st.session_state.selected_floor_plan_id = fp.get('id') or fp.get('floor_plan_id')
    else:
        st.info("No floor plans yet. Upload or analyze a floor plan to enable per-floor selection.")

    # Rooms grid for selected floor (or all)
    rooms: List[Dict[str, Any]] = (data.get('rooms') or [])
    sfi = st.session_state.get('selected_floor_index')
    if sfi is not None:
        rooms = [r for r in rooms if (r.get('floor_level') == sfi)]

    if not rooms:
        st.info("No rooms found for this floor. Analyze a floor plan first.")
        return

    st.markdown("#### Rooms")
    grid_cols = st.columns(3)
    for idx, room in enumerate(rooms):
        with grid_cols[idx % 3]:
            st.markdown(f"**{room.get('name') or room.get('room_type')}**")
            st.caption(f"Type: {room.get('room_type')} • Floor: {room.get('floor_level')}")
            selected = st.button("Use this room", key=f"use_room_{room.get('id')}", use_container_width=True)
            if selected:
                st.session_state.selected_room_id = room.get('id')
                st.session_state.selected_room_image_ids = set()

            # If this room is selected, show images gallery
            if st.session_state.get('selected_room_id') == room.get('id'):
                show_room_images_gallery(room.get('id'))


def show_room_images_gallery(room_id: str):
    """Load (and cache) room details to show image thumbnails with selection."""
    cache: Dict[str, Any] = st.session_state.room_cache
    if room_id not in cache:
        with st.spinner("Loading room images..."):
            try:
                resp = requests.get(f"{API_BASE_URL}/rooms/{room_id}")
                if resp.status_code == 200:
                    cache[room_id] = resp.json()
                else:
                    st.warning(f"Could not load room details (status {resp.status_code})")
                    cache[room_id] = {"images": []}
            except Exception as e:
                st.error(f"Error loading room details: {e}")
                cache[room_id] = {"images": []}

    details = cache.get(room_id, {})
    imgs: List[Dict[str, Any]] = details.get('images') or []
    if not imgs:
        st.info("No images for this room yet. Upload some in the setup flow.")
        return

    st.markdown("##### Images")
    cols = st.columns(4)
    current = set(st.session_state.get('selected_room_image_ids') or [])
    for i, img in enumerate(imgs):
        with cols[i % 4]:
            if img.get('image_url'):
                st.image(img.get('image_url'), use_column_width=True)
            toggled = st.checkbox(
                f"Select",
                key=f"sel_img_{room_id}_{img.get('id')}",
                value=(img.get('id') in current)
            )
            if toggled:
                current.add(img.get('id'))
            else:
                current.discard(img.get('id'))
    # Save updated selection
    st.session_state.selected_room_image_ids = current


def add_system_message(content: str):
    """Add a system message to chat history."""
    timestamp = datetime.now().strftime("%I:%M %p")
    st.session_state.chat_history.append({
        'role': 'assistant',
        'content': content,
        'timestamp': timestamp
    })
    st.rerun()


def fetch_home_data(home_id: str) -> Optional[Dict[str, Any]]:
    """Fetch complete home data from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/homes/{home_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching home data: {str(e)}")
        return None

