"""
Setup Flow Component
Multi-step onboarding to collect home data
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any
from datetime import datetime
import time


API_BASE_URL = "http://localhost:8000/api/digital-twin"


def show_setup_flow():
    """Display the multi-step setup flow."""
    
    st.markdown("""
    <div class="chat-container">
        <h1 style="text-align: center; margin-bottom: 2rem;">📋 Set Up Your Home</h1>
        <p style="text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 3rem;">
            Let's collect some information about your home to build your digital twin
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress indicator
    show_progress_indicator()
    
    # Show current step
    if st.session_state.setup_step == 1:
        show_step_1_create_home()
    elif st.session_state.setup_step == 2:
        show_step_2_floor_plan()
    elif st.session_state.setup_step == 3:
        show_step_3_room_images()


def show_progress_indicator():
    """Show progress through setup steps."""
    steps = [
        {"num": 1, "title": "Home Details", "icon": "🏡"},
        {"num": 2, "title": "Floor Plan", "icon": "📐"},
        {"num": 3, "title": "Room Images", "icon": "📸"}
    ]
    
    st.markdown('<div class="setup-progress">', unsafe_allow_html=True)
    
    for step in steps:
        if step["num"] < st.session_state.setup_step:
            status_class = "complete"
            status_icon = "✓"
        elif step["num"] == st.session_state.setup_step:
            status_class = "active"
            status_icon = step["icon"]
        else:
            status_class = ""
            status_icon = step["icon"]
        
        st.markdown(f"""
        <div class="progress-step {status_class}">
            <div style="font-size: 1.5rem; margin-right: 1rem;">{status_icon}</div>
            <div>
                <div style="font-weight: 600;">Step {step["num"]}: {step["title"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def show_step_1_create_home():
    """Step 1: Create home with basic details."""
    
    st.markdown("### 🏡 Step 1: Tell us about your home")
    st.markdown("Provide basic information to get started")
    
    with st.form("create_home_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Home Name *", placeholder="e.g., My Dream Home")
            street = st.text_input("Street Address *", placeholder="123 Main St")
            city = st.text_input("City *", placeholder="San Francisco")
            home_type = st.selectbox("Home Type *", [
                "Single Family", "Condo", "Townhouse", "Multi-Family", "Other"
            ])
        
        with col2:
            province = st.text_input("State/Province *", placeholder="CA")
            postal_code = st.text_input("Postal Code *", placeholder="94102")
            country = st.text_input("Country *", value="USA")
            year_built = st.number_input("Year Built", min_value=1800, max_value=2025, value=2000)
        
        col1, col2 = st.columns(2)
        with col1:
            num_bathrooms = st.number_input("Bathrooms", min_value=0.0, value=2.0, step=0.5)
        with col2:
            pass  # Bedrooms and Square Footage will be inferred from floor plans
        
        st.markdown("---")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("Continue to Floor Plan →", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.current_view = 'welcome'
                st.rerun()
        
        if submitted:
            if not all([name, street, city, province, postal_code, country]):
                st.error("Please fill in all required fields marked with *")
            else:
                with st.spinner("Creating your home..."):
                    result = create_home(
                        name=name,
                        street=street,
                        city=city,
                        province=province,
                        postal_code=postal_code,
                        country=country,
                        home_type=home_type,
                        year_built=year_built,
                        num_bathrooms=num_bathrooms
                    )
                    
                    if result:
                        st.session_state.home_id = result.get('id') or result.get('home_id')
                        st.session_state.home_data = result
                        st.session_state.setup_step = 2
                        st.success("✅ Home created successfully!")
                        time.sleep(1)
                        st.rerun()


def show_step_2_floor_plan():
    """Step 2: Upload and analyze floor plan."""
    
    st.markdown("### 📐 Step 2: Upload your floor plan")
    st.markdown("Upload an image of your floor plan for AI analysis")
    
    uploaded_file = st.file_uploader(
        "Choose floor plan image",
        type=['png', 'jpg', 'jpeg', 'pdf'],
        help="Upload a clear image of your floor plan"
    )
    
    if uploaded_file:
        # Show preview
        if uploaded_file.type != "application/pdf":
            from PIL import Image
            image = Image.open(uploaded_file)
            st.image(image, caption="Floor Plan Preview", use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        floor_level = st.number_input("Floor Level", min_value=1, value=1, step=1)
    with col2:
        floor_name = st.text_input("Floor Name", value=f"Floor {floor_level}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.setup_step = 1
            st.rerun()
    
    with col2:
        if uploaded_file and st.button("🔍 Analyze Floor Plan", type="primary", use_container_width=True):
            with st.spinner("🤖 AI is analyzing your floor plan... This may take 10-30 seconds"):
                result = upload_floor_plan(
                    home_id=st.session_state.home_id,
                    file=uploaded_file,
                    floor_level=floor_level,
                    name=floor_name
                )
                
                if result:
                    st.session_state.room_ids = result.get('room_ids', [])
                    st.success(f"✅ Floor plan analyzed! Detected {result['rooms_created']} rooms")
                    time.sleep(1)
                    st.session_state.setup_step = 3
                    st.rerun()
    
    with col3:
        if st.button("Skip →", use_container_width=True):
            st.session_state.setup_step = 3
            st.rerun()


def show_step_3_room_images():
    """Step 3: Upload room images."""
    
    st.markdown("### 📸 Step 3: Upload room images (Optional)")
    st.markdown("Upload photos of your rooms for detailed analysis")
    
    if not st.session_state.room_ids:
        st.warning("⚠️ No rooms detected from floor plan. You can skip this step or go back to upload a floor plan.")
    else:
        st.info(f"📍 {len(st.session_state.room_ids)} rooms detected from your floor plan")
        
        # Room selection
        room_options = {f"Room {idx + 1}": room_id 
                       for idx, room_id in enumerate(st.session_state.room_ids)}
        selected_room_label = st.selectbox("Select Room", list(room_options.keys()))
        selected_room_id = room_options[selected_room_label]
        
        uploaded_file = st.file_uploader(
            "Choose room image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear photo of the room"
        )
        
        if uploaded_file:
            from PIL import Image
            image = Image.open(uploaded_file)
            st.image(image, caption="Room Image Preview", use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            image_type = st.selectbox("Image Type", ["photo", "render", "sketch"])
        with col2:
            view_angle = st.selectbox("View Angle", ["front", "corner", "wide", "detail"])
        with col3:
            analysis_type = st.selectbox("Analysis Type", ["comprehensive", "quick", "detailed"])
        
        if uploaded_file and st.button("🔍 Analyze Room Image", type="primary", use_container_width=True):
            with st.spinner("🤖 Analyzing room image..."):
                result = upload_room_image(
                    room_id=selected_room_id,
                    file=uploaded_file,
                    image_type=image_type,
                    view_angle=view_angle,
                    analysis_type=analysis_type
                )
                
                if result:
                    st.success(f"✅ Room analyzed! Found {result['materials_created']} materials, "
                             f"{result['fixtures_created']} fixtures, {result['products_created']} products")

        st.markdown("---")
        st.subheader("Bulk upload images")
        st.caption("Upload multiple room photos at once. We'll analyze and auto-link them to rooms.")
        multi_files = st.file_uploader("Select multiple images", type=['png','jpg','jpeg','webp'], accept_multiple_files=True)
        colb1, colb2 = st.columns([1,1])
        with colb1:
            if multi_files and st.button("📤 Bulk analyze & save", type="primary", use_container_width=True):
                with st.spinner("Analyzing and linking images... this may take a minute"):
                    res = bulk_upload_room_images(st.session_state.home_id, multi_files)
                    if res:
                        st.success(f"✅ Saved {res['ingested']} images (skipped {res['skipped']}).")
                        if res.get('errors'):
                            with st.expander("View warnings/errors"):
                                for e in res['errors']:
                                    st.write(f"- {e}")
        with colb2:
            if st.button("⬇️ Export CSV backup", use_container_width=True):
                with st.spinner("Preparing CSV export..."):
                    content = export_home_csv(st.session_state.home_id)
                    if content:
                        st.download_button(
                            label="Download CSV ZIP",
                            data=content,
                            file_name=f"home_{st.session_state.home_id}_export.zip",
                            mime="application/zip",
                            use_container_width=True,
                        )
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.setup_step = 2
            st.rerun()
    
    with col2:
        if st.button("✅ Complete Setup & Start Chatting", type="primary", use_container_width=True):
            st.session_state.setup_complete = True
            st.session_state.current_view = 'chat'
            st.balloons()
            st.rerun()
    
    with col3:
        if st.button("Add More Images", use_container_width=True):
            st.rerun()


# API Functions
def create_home(**kwargs) -> Optional[Dict[str, Any]]:
    """Create a new home via API."""
    try:
        # Map home_type to enum value
        home_type_map = {
            "Single Family": "single_family",
            "Condo": "condo",
            "Townhouse": "townhouse",
            "Multi-Family": "multi_family",
            "Other": "other"
        }
        
        payload = {
            "owner_email": "user@homevision.ai",  # Default email for now
            "name": kwargs['name'],
            "address": {
                "street": kwargs['street'],
                "city": kwargs['city'],
                "province": kwargs['province'],
                "postal_code": kwargs['postal_code'],
                "country": kwargs['country']
            },
            "home_type": home_type_map.get(kwargs['home_type'], 'other'),
            "year_built": kwargs.get('year_built'),
            "num_bathrooms": kwargs.get('num_bathrooms')
        }
        
        response = requests.post(f"{API_BASE_URL}/homes", json=payload)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.HTTPError as e:
        st.error(f"Error creating home: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Error creating home: {str(e)}")
        return None


def upload_floor_plan(home_id: str, file, floor_level: int, name: str) -> Optional[Dict[str, Any]]:
    """Upload and analyze floor plan."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {
            "floor_level": floor_level,
            "name": name
        }
        
        response = requests.post(
            f"{API_BASE_URL}/homes/{home_id}/floor-plans",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading floor plan: {str(e)}")
        return None


def upload_room_image(room_id: str, file, image_type: str, view_angle: str, analysis_type: str) -> Optional[Dict[str, Any]]:
    """Upload and analyze room image."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {
            "image_type": image_type,
            "view_angle": view_angle,
            "analysis_type": analysis_type
        }
        
        response = requests.post(
            f"{API_BASE_URL}/rooms/{room_id}/images",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading room image: {str(e)}")
        return None


def bulk_upload_room_images(home_id: str, files) -> Optional[Dict[str, Any]]:
    """Bulk upload room images via API."""
    try:
        files_payload = [("files", (f.name, f.getvalue(), f.type)) for f in files]
        response = requests.post(
            f"{API_BASE_URL}/homes/{home_id}/bulk-room-images",
            files=files_payload,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error in bulk upload: {str(e)}")
        return None


def export_home_csv(home_id: str) -> Optional[bytes]:
    """Request CSV export and return bytes for download."""
    try:
        resp = requests.get(f"{API_BASE_URL}/homes/{home_id}/export-csv")
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        st.error(f"Error exporting CSV: {str(e)}")
        return None

