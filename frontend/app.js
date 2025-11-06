// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/digital-twin';
const STUDIO_DATA_URL = `${API_BASE_URL}/studio/data`;

// Global state
let currentHomeId = null;
let currentRoomIds = [];

// Utility Functions
function showResult(elementId, type, message, data = null) {
    const resultDiv = document.getElementById(elementId);
    resultDiv.className = `result ${type}`;
    
    let html = `<h3>${message}</h3>`;
    if (data) {
        html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
    
    resultDiv.innerHTML = html;
}

function showLoading(button, show = true) {
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');
    
    if (show) {
        button.disabled = true;
        if (btnText) btnText.style.display = 'none';
        if (spinner) spinner.style.display = 'block';
    } else {
        button.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (spinner) spinner.style.display = 'none';
    }
}

// Step 1: Create Home
document.getElementById('createHomeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        owner_email: document.getElementById('ownerEmail').value,
        name: document.getElementById('homeName').value,
        address: {
            street: document.getElementById('street').value,
            city: document.getElementById('city').value,
            province: document.getElementById('province').value,
            postal_code: document.getElementById('postalCode').value,
            country: 'Canada'
        },
        home_type: 'single_family',
        year_built: parseInt(document.getElementById('yearBuilt').value),
        square_footage: parseInt(document.getElementById('squareFootage').value),
        num_bedrooms: parseInt(document.getElementById('bedrooms').value),
        num_bathrooms: parseFloat(document.getElementById('bathrooms').value)
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/homes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentHomeId = data.id;
        
        showResult('homeResult', 'success', '✅ Home Created Successfully!', {
            id: data.id,
            name: data.name,
            address: data.address
        });
        
        // Show next section
        document.getElementById('floorPlanSection').style.display = 'block';
        document.getElementById('digitalTwinSection').style.display = 'block';
        
    } catch (error) {
        showResult('homeResult', 'error', '❌ Error Creating Home', {
            error: error.message
        });
    }
});

// Step 2: Upload Floor Plan
document.getElementById('floorPlanFile').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('floorPlanPreview').innerHTML = 
                `<img src="${e.target.result}" alt="Floor Plan Preview">`;
        };
        reader.readAsDataURL(file);
    }
});

document.getElementById('uploadFloorPlanForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!currentHomeId) {
        showResult('floorPlanResult', 'error', '❌ Please create a home first!');
        return;
    }
    
    const fileInput = document.getElementById('floorPlanFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showResult('floorPlanResult', 'error', '❌ Please select a floor plan image!');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('floor_level', document.getElementById('floorLevel').value);
    formData.append('name', document.getElementById('floorName').value);
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    showLoading(submitBtn, true);
    
    try {
        showResult('floorPlanResult', 'info', '🔄 Analyzing floor plan with Gemini AI... This may take a moment.');
        
        const response = await fetch(`${API_BASE_URL}/homes/${currentHomeId}/floor-plans`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentRoomIds = data.room_ids || [];
        
        showResult('floorPlanResult', 'success', '✅ Floor Plan Analyzed Successfully!', {
            floor_plan_id: data.floor_plan_id,
            rooms_created: data.rooms_created,
            room_ids: data.room_ids,
            message: data.message
        });
        
        // Show room images section if rooms were created
        if (currentRoomIds.length > 0) {
            displayRoomsList();
            document.getElementById('roomImagesSection').style.display = 'block';
        }
        
        // Refresh digital twin
        loadDigitalTwin();
        
    } catch (error) {
        showResult('floorPlanResult', 'error', '❌ Error Analyzing Floor Plan', {
            error: error.message
        });
    } finally {
        showLoading(submitBtn, false);
    }
});

// Display rooms list for image upload
function displayRoomsList() {
    const roomsList = document.getElementById('roomsList');
    
    if (currentRoomIds.length === 0) {
        roomsList.innerHTML = '<p>No rooms available. Upload a floor plan first.</p>';
        return;
    }
    
    roomsList.innerHTML = currentRoomIds.map((roomId, index) => `
        <div class="room-card">
            <h3>Room ${index + 1}</h3>
            <form class="room-upload-form" data-room-id="${roomId}">
                <div class="form-group">
                    <label>Room Image:</label>
                    <input type="file" accept="image/*" required>
                </div>
                <div class="form-group">
                    <label>Analysis Type:</label>
                    <select>
                        <option value="comprehensive">Comprehensive</option>
                        <option value="quick">Quick</option>
                        <option value="detailed">Detailed</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-success">
                    <span class="btn-text">Analyze Room</span>
                    <span class="spinner" style="display: none;"></span>
                </button>
            </form>
            <div id="roomResult${index}" class="result"></div>
        </div>
    `).join('');
    
    // Add event listeners to room upload forms
    document.querySelectorAll('.room-upload-form').forEach((form, index) => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await uploadRoomImage(form, index);
        });
    });
}

// Upload room image
async function uploadRoomImage(form, index) {
    const roomId = form.dataset.roomId;
    const fileInput = form.querySelector('input[type="file"]');
    const analysisType = form.querySelector('select').value;
    const file = fileInput.files[0];
    
    if (!file) {
        showResult(`roomResult${index}`, 'error', '❌ Please select an image!');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('analysis_type', analysisType);
    
    const submitBtn = form.querySelector('button[type="submit"]');
    showLoading(submitBtn, true);
    
    try {
        showResult(`roomResult${index}`, 'info', '🔄 Analyzing room image with Gemini AI...');
        
        const response = await fetch(`${API_BASE_URL}/rooms/${roomId}/images`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        showResult(`roomResult${index}`, 'success', '✅ Room Image Analyzed Successfully!', {
            image_id: data.image_id,
            materials_created: data.materials_created,
            fixtures_created: data.fixtures_created,
            products_created: data.products_created,
            message: data.message
        });
        
        // Refresh digital twin
        loadDigitalTwin();
        
    } catch (error) {
        showResult(`roomResult${index}`, 'error', '❌ Error Analyzing Room Image', {
            error: error.message
        });
    } finally {
        showLoading(submitBtn, false);
    }
}

// Load and display digital twin
async function loadDigitalTwin() {
    if (!currentHomeId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/homes/${currentHomeId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayDigitalTwin(data);
        
    } catch (error) {
        showResult('digitalTwinResult', 'error', '❌ Error Loading Digital Twin', {
            error: error.message
        });
    }
}

// Display digital twin data
function displayDigitalTwin(data) {
    const resultDiv = document.getElementById('digitalTwinResult');
    
    const completeness = (data.digital_twin_completeness || 0) * 100;
    
    let html = `
        <div class="digital-twin-data">
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="label">Home Type</div>
                    <div class="value">${data.home_type || 'N/A'}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Total Rooms</div>
                    <div class="value">${data.total_rooms || 0}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Total Images</div>
                    <div class="value">${data.total_images || 0}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Square Footage</div>
                    <div class="value">${data.square_footage || 'N/A'}</div>
                </div>
            </div>
            
            <div>
                <strong>Digital Twin Completeness:</strong>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${completeness}%">
                        ${completeness.toFixed(1)}%
                    </div>
                </div>
            </div>
    `;
    
    if (data.rooms && data.rooms.length > 0) {
        html += '<div class="room-list"><h3>Rooms:</h3>';
        
        data.rooms.forEach(room => {
            html += `
                <div class="room-item">
                    <h4>${room.name} (${room.room_type})</h4>
                    <div class="room-details">
                        <div class="room-detail"><strong>Dimensions:</strong> ${room.length || 'N/A'}' × ${room.width || 'N/A'}' × ${room.height || 'N/A'}'</div>
                        <div class="room-detail"><strong>Area:</strong> ${room.area || 'N/A'} sq ft</div>
                        <div class="room-detail"><strong>Style:</strong> ${room.style || 'N/A'}</div>
                        <div class="room-detail"><strong>Condition:</strong> ${room.condition_score || 'N/A'}/10</div>
                    </div>
            `;
            
            if (room.materials && room.materials.length > 0) {
                html += '<div class="materials-list"><h5>Materials:</h5>';
                room.materials.forEach(mat => {
                    html += `<span class="item-tag">${mat.material_type} (${mat.category})</span>`;
                });
                html += '</div>';
            }
            
            if (room.fixtures && room.fixtures.length > 0) {
                html += '<div class="fixtures-list"><h5>Fixtures:</h5>';
                room.fixtures.forEach(fix => {
                    html += `<span class="item-tag">${fix.fixture_type}</span>`;
                });
                html += '</div>';
            }
            
            if (room.products && room.products.length > 0) {
                html += '<div class="products-list"><h5>Products:</h5>';
                room.products.forEach(prod => {
                    html += `<span class="item-tag">${prod.product_type}</span>`;
                });
                html += '</div>';
            }
            
            html += '</div>';
        });
        
        html += '</div>';
    }
    
    html += '</div>';
    
    resultDiv.innerHTML = html;
    resultDiv.className = 'result info';
}

// Refresh digital twin button
document.getElementById('refreshDigitalTwin').addEventListener('click', loadDigitalTwin);

// =====================
// Studio (CSV-backed)
// =====================

let studioState = {
    data: null,
    zoom: 1,
    positions: {}, // image_id -> {x,y}
    filterFloor: 'all',
    filterRoom: 'all',
};

// Open Studio (skip setup)
document.getElementById('openStudioBtn').addEventListener('click', async () => {
    // Hide setup sections and show Studio
    document.getElementById('floorPlanSection').style.display = 'none';
    document.getElementById('roomImagesSection').style.display = 'none';
    document.getElementById('digitalTwinSection').style.display = 'none';
    document.getElementById('homeResult').innerHTML = '';
    document.getElementById('studioSection').style.display = 'block';
    await loadStudioData();
});

async function loadStudioData() {
    try {
        const res = await fetch(STUDIO_DATA_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        studioState.data = data;
        initStudioFilters();
        renderStudio();
    } catch (e) {
        console.error(e);
        alert('Failed to load studio data. Ensure backend is running and enriched CSVs exist.');
    }
}

function initStudioFilters() {
    const floorSel = document.getElementById('studioFloorFilter');
    const roomSel = document.getElementById('studioRoomFilter');
    const floors = new Set();
    (studioState.data.rooms || []).forEach(r => { if (r.floor_level !== undefined && r.floor_level !== null) floors.add(String(r.floor_level)); });
    floorSel.innerHTML = `<option value="all">All Floors</option>` + Array.from(floors).sort().map(f => `<option value="${f}">${f}</option>`).join('');

    roomSel.innerHTML = `<option value="all">All Rooms</option>` + (studioState.data.rooms || []).map(r => `<option value="${r.id}">${r.name || r.room_type}</option>`).join('');

    floorSel.onchange = () => { studioState.filterFloor = floorSel.value; renderStudio(); };
    roomSel.onchange = () => { studioState.filterRoom = roomSel.value; renderStudio(); };
    document.getElementById('resetFilters').onclick = () => { studioState.filterFloor = 'all'; studioState.filterRoom = 'all'; floorSel.value = 'all'; roomSel.value = 'all'; renderStudio(); };

    document.getElementById('zoomIn').onclick = () => setZoom(studioState.zoom * 1.1);
    document.getElementById('zoomOut').onclick = () => setZoom(studioState.zoom / 1.1);
    document.getElementById('zoomReset').onclick = () => setZoom(1);
}

function setZoom(z) {
    studioState.zoom = Math.min(3, Math.max(0.3, z));
    const canvas = document.getElementById('studioCanvas');
    canvas.style.transform = `scale(${studioState.zoom})`;
}

function renderStudio() {
    if (!studioState.data) return;
    const { rooms, room_images, image_analyses } = studioState.data;
    const canvas = document.getElementById('studioCanvas');
    const list = document.getElementById('studioImageList');
    canvas.innerHTML = '';
    list.innerHTML = '';

    let filteredRooms = rooms;
    if (studioState.filterFloor !== 'all') {
        filteredRooms = filteredRooms.filter(r => String(r.floor_level) === studioState.filterFloor);
    }
    if (studioState.filterRoom !== 'all') {
        filteredRooms = filteredRooms.filter(r => r.id === studioState.filterRoom);
    }

    // Images for filtered rooms
    const images = [];
    filteredRooms.forEach(r => {
        (r.images || []).forEach(im => images.push({ ...im, room: r }));
    });

    // Sidebar list
    images.forEach(im => {
        const item = document.createElement('div');
        item.className = 'thumb';
        item.innerHTML = `<img src="${im.image_url || ''}" alt=""><div class="meta"><div>${im.room?.name || im.room?.room_type || 'Room'}</div><div>${im.view_angle || ''}</div></div>`;
        item.onclick = () => focusImageOnCanvas(im);
        list.appendChild(item);
    });

    // Canvas draggables
    const cols = 4; // initial grid placement
    images.forEach((im, idx) => {
        const div = document.createElement('div');
        div.className = 'draggable-image';
        div.dataset.imageId = im.id;
        div.style.left = (studioState.positions[im.id]?.x ?? ((idx % cols) * 240 + 20)) + 'px';
        div.style.top = (studioState.positions[im.id]?.y ?? (Math.floor(idx / cols) * 240 + 20)) + 'px';
        div.innerHTML = `<img src="${im.image_url || ''}" alt=""><div class="caption">${im.room?.name || im.room?.room_type || 'Room'}</div>`;
        enableDrag(div);

        // Expand modal on double click
        div.ondblclick = () => openImageModal(im, image_analyses);
        canvas.appendChild(div);
    });

    // Ensure current zoom applied
    setZoom(studioState.zoom);
}

function enableDrag(el) {
    let startX=0, startY=0, origX=0, origY=0, dragging=false;
    el.addEventListener('mousedown', (e) => {
        dragging = true;
        startX = e.clientX; startY = e.clientY;
        origX = parseInt(el.style.left||'0',10); origY = parseInt(el.style.top||'0',10);
        el.style.cursor = 'grabbing';
        e.preventDefault();
    });
    window.addEventListener('mousemove', (e) => {
        if (!dragging) return;
        const dx = (e.clientX - startX) / studioState.zoom;
        const dy = (e.clientY - startY) / studioState.zoom;
        const nx = origX + dx; const ny = origY + dy;
        el.style.left = nx + 'px';
        el.style.top = ny + 'px';
    });
    window.addEventListener('mouseup', () => {
        if (!dragging) return;
        dragging = false;
        el.style.cursor = 'grab';
        const id = el.dataset.imageId;
        studioState.positions[id] = { x: parseInt(el.style.left,10), y: parseInt(el.style.top,10) };
    });
}

function openImageModal(im, analysesMap) {
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('modalImage');
    const modalMeta = document.getElementById('modalMeta');
    document.getElementById('modalClose').onclick = () => modal.style.display = 'none';
    modal.onclick = (e) => { if (e.target === modal) modal.style.display = 'none'; };

    modalImg.src = im.image_url || '';
    // find analysis by room_image_id
    const analyses = Object.values(analysesMap || {}).filter(a => a.room_image_id === im.id);
    modalMeta.textContent = JSON.stringify({ image: im, analyses }, null, 2);
    modal.style.display = 'flex';
}

function focusImageOnCanvas(im) {
    const el = document.querySelector(`.draggable-image[data-image-id="${im.id}"]`);
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
    el.style.boxShadow = '0 0 0 3px #667eea';
    setTimeout(() => { el.style.boxShadow = '0 4px 8px rgba(0,0,0,0.05)'; }, 1200);
}

