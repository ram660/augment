# HomeView AI Streamlit App - Technical Architecture

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                              │
│              http://localhost:8501                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Application                           │
│         (streamlit_homeview_chat.py)                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Session State Management                             │  │
│  │ - User authentication (JWT token)                    │  │
│  │ - Conversation history                               │  │
│  │ - Design transformations                             │  │
│  │ - Navigation state                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Multi-Page Navigation                                │  │
│  │ - Sidebar with page selection                        │  │
│  │ - Authentication status display                      │  │
│  │ - Backend connection status                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Page Renderers (10 pages)                            │  │
│  │ - _render_chat_page()                                │  │
│  │ - _render_design_studio_page()                       │  │
│  │ - _render_digital_twin_page()                        │  │
│  │ - _render_journey_page()                             │  │
│  │ - _render_products_page()                            │  │
│  │ - _render_documents_page()                           │  │
│  │ - _render_intelligence_page()                        │  │
│  │ - _render_monitoring_page()                          │  │
│  │ - _render_admin_page()                               │  │
│  │ - _render_login_page()                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API Client Functions                                 │  │
│  │ - _call_chat() - Streaming chat                      │  │
│  │ - _execute_design_transformation() - Image transform │  │
│  │ - _execute_action() - Action execution               │  │
│  │ - _get_auth_headers() - JWT token handling           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/REST
                     │ (JSON + Multipart)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend                                 │
│         (backend/main.py)                                    │
│              http://localhost:8000                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Middleware Stack                                     │  │
│  │ - CORS Middleware (allow all origins)                │  │
│  │ - Rate Limiting Middleware                           │  │
│  │ - Monitoring Middleware                              │  │
│  │ - Exception Handlers                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API Routers (9 routers)                              │  │
│  │ - /api/v1/auth - Authentication                      │  │
│  │ - /api/v1/chat - Chat & streaming                    │  │
│  │ - /api/v1/design - Image transformations             │  │
│  │ - /api/v1/digital-twin - Home management             │  │
│  │ - /api/v1/journey - Project tracking                 │  │
│  │ - /api/v1/products - Product catalog                 │  │
│  │ - /api/v1/documents - Document parsing               │  │
│  │ - /api/v1/intelligence - AI insights                 │  │
│  │ - /api/v1/monitoring - Health checks                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Services & Integrations                              │  │
│  │ - Gemini Client (image generation, analysis)         │  │
│  │ - Google Grounding (product search)                  │  │
│  │ - Database (PostgreSQL + SQLAlchemy)                 │  │
│  │ - Authentication (JWT tokens)                        │  │
│  │ - File Storage (uploads, generated images)           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow Examples

### Chat Request Flow
```
1. User types message in Streamlit
2. _call_chat() builds payload with message, conversation_id, etc.
3. POST to /api/v1/chat/stream-multipart with optional file
4. Backend processes with ChatWorkflow
5. Streaming response via Server-Sent Events (SSE)
6. Streamlit displays chunks in real-time
```

### Design Transformation Flow
```
1. User uploads image in Design Studio
2. Image converted to base64 data URL
3. _execute_design_transformation() builds JSON payload
4. POST to /api/v1/design/transform-{type}-upload
5. Backend:
   - Decodes base64 image
   - Enhances quality if needed
   - Calls Gemini for transformation
   - Gets product recommendations via Google Grounding
   - Returns PromptedTransformUploadResponse
6. Streamlit displays before/after comparison
7. Shows product recommendations
8. Saves to design_history
```

---

## 🔐 Authentication Flow

### Guest Mode
```
1. User accesses app without login
2. _get_auth_headers() returns empty dict
3. Backend uses get_current_user_optional
4. Creates default test user for development
5. All guest-mode endpoints work
```

### Authenticated Mode
```
1. User clicks "Login" in sidebar
2. Enters credentials in login form
3. POST to /api/v1/auth/login
4. Backend returns JWT token
5. Token stored in st.session_state.access_token
6. _get_auth_headers() includes "Authorization: Bearer {token}"
7. All authenticated endpoints work
```

---

## 📊 Data Flow

### Image Transformation
```
Streamlit                          Backend
   │                                 │
   ├─ Read image file                │
   ├─ Convert to base64              │
   ├─ Create data URL                │
   ├─ POST JSON with image_data_url──┼──> Decode base64
   │                                 ├─> Enhance quality
   │                                 ├─> Call Gemini API
   │                                 ├─> Get product recommendations
   │                                 ├─> Encode results to base64
   │<─ Return PromptedTransformUploadResponse
   ├─ Display before/after
   ├─ Show products
   └─ Save to history
```

---

## 🛠️ Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Streamlit | Multi-page UI |
| Backend | FastAPI | REST API |
| Database | PostgreSQL | Data persistence |
| ORM | SQLAlchemy | Database abstraction |
| Auth | JWT | Token-based authentication |
| AI | Google Gemini | Image generation, analysis |
| Search | Google Grounding | Product recommendations |
| Streaming | SSE | Real-time responses |
| File Upload | Multipart | Image/document uploads |

---

## 📝 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/chat/stream-multipart` | POST | Streaming chat with files |
| `/api/v1/design/transform-*-upload` | POST | Image transformations |
| `/api/v1/digital-twin/homes` | GET/POST | Home management |
| `/api/v1/journey/start` | POST | Start journey |
| `/api/v1/products/` | GET | Product catalog |
| `/api/v1/documents/parse` | POST | Document parsing |
| `/api/v1/intelligence/generate-image` | POST | Image generation |
| `/api/v1/monitoring/health` | GET | Health check |
| `/api/v1/auth/login` | POST | User login |

---

## 🎯 Design Principles

1. **Guest-First**: All features accessible without login
2. **Streaming**: Real-time responses for better UX
3. **Error Handling**: Graceful degradation on failures
4. **Modular**: Each page is independent
5. **Responsive**: Works on different screen sizes
6. **Accessible**: Clear navigation and feedback

---

## 🚀 Performance Considerations

- **Streaming**: Chat responses stream in real-time
- **Caching**: Session state reduces redundant API calls
- **Async**: Backend uses async/await for concurrency
- **Rate Limiting**: Protects backend from overload
- **Monitoring**: Tracks slow requests and errors

