# HomeVision AI Studio

Modern Miro/Figma-style canvas interface for digital twin visualization and design.

## Features

✅ **Infinite Canvas** - Pan, zoom, and navigate freely  
✅ **Interactive Nodes** - Floor plans, rooms, and images as draggable nodes  
✅ **Multi-Select** - Select multiple items (Shift+Click or drag selection box)  
✅ **AI Chat** - Ask questions about selected items  
✅ **Visual Linking** - See connections between images and rooms  
✅ **Layers Panel** - View and manage all canvas elements  
✅ **Minimap** - Navigate large canvases easily  

## Installation

```bash
cd frontend-studio
npm install
```

## Development

```bash
npm run dev
```

The studio will be available at `http://localhost:3000`

Make sure the backend API is running on `http://localhost:8000`

## Usage

### Navigation
- **Pan**: Hold Space + Drag, or use Pan tool (✋)
- **Zoom**: Mouse wheel or use Controls (+/-)
- **Select**: Click on nodes or drag selection box
- **Multi-Select**: Hold Shift + Click multiple nodes

### Tools
- 🖱️ **Select** - Select and move nodes
- ✋ **Pan** - Pan the canvas
- 📏 **Measure** - Measure distances (coming soon)
- ✏️ **Annotate** - Add notes and drawings (coming soon)
- 🎨 **Color Picker** - Pick colors from images (coming soon)

### Chat
1. Select one or more items on the canvas
2. Ask questions in the chat panel
3. AI will respond with context about selected items

Example questions:
- "What materials are in these rooms?"
- "Tell me about this image"
- "Compare the fixtures in these two rooms"

## Architecture

```
frontend-studio/
├── src/
│   ├── components/
│   │   ├── Common/
│   │   │   └── Header.jsx
│   │   └── Studio/
│   │       ├── StudioCanvas.jsx    # Main canvas with React Flow
│   │       ├── Toolbar.jsx         # Tool selection
│   │       ├── Sidebar.jsx         # Layers panel
│   │       ├── ChatPanel.jsx       # AI chat interface
│   │       └── nodes/
│   │           ├── FloorPlanNode.jsx
│   │           ├── RoomNode.jsx
│   │           └── ImageNode.jsx
│   ├── hooks/
│   │   ├── useStudioData.js        # Fetch home data
│   │   └── useChat.js              # Chat API integration
│   └── styles/
│       ├── global.css
│       └── app.css
```

## Tech Stack

- **React 18** - UI framework
- **React Flow** - Canvas and node management
- **Vite** - Build tool and dev server
- **Axios** - HTTP client
- **Zustand** - State management (future)

## API Integration

### Endpoints Used

#### Get Home Data
```
GET /api/digital-twin/homes/{home_id}
```

#### Chat
```
POST /api/digital-twin/chat
Body: {
  message: string,
  home_id: string,
  conversation_history: array,
  context: {
    selected_rooms: string[],
    selected_images: string[]
  }
}
```

## Customization

### Node Types

Create custom nodes in `src/components/Studio/nodes/`:

```jsx
import { Handle, Position } from 'reactflow'

function CustomNode({ data, selected }) {
  return (
    <div className={`custom-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Top} />
      {/* Your content */}
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}
```

Register in `StudioCanvas.jsx`:
```jsx
const nodeTypes = {
  custom: CustomNode
}
```

### Styling

Edit `src/styles/app.css` for global styles  
Edit `src/components/Studio/nodes/nodes.css` for node styles

## Roadmap

### Phase 1: Basic Canvas ✅
- [x] Infinite canvas with pan/zoom
- [x] Floor plan background
- [x] Room nodes
- [x] Image nodes
- [x] Multi-select
- [x] Chat integration

### Phase 2: Enhanced Features (In Progress)
- [ ] Save canvas state to database
- [ ] Auto-arrange images by room
- [ ] Drag images to link to rooms
- [ ] Annotation tools
- [ ] Measurement tools

### Phase 3: Design Studio
- [ ] Color picker from images
- [ ] Material swatches library
- [ ] Product catalog integration
- [ ] Export canvas as image/PDF

### Phase 4: Collaboration
- [ ] Real-time multi-user editing
- [ ] Cursor tracking
- [ ] Comments and feedback

## Troubleshooting

### Canvas not loading
- Check that backend API is running on port 8000
- Check browser console for errors
- Verify home ID exists in database

### Images not displaying
- Check image URLs in database
- Verify CORS settings on backend
- Check network tab for failed requests

### Chat not working
- Verify `/api/digital-twin/chat` endpoint is working
- Check that home_id is valid
- Look for errors in browser console

## Contributing

1. Create a new branch for your feature
2. Make changes and test thoroughly
3. Submit a pull request with description

## License

Proprietary - HomeVision AI

