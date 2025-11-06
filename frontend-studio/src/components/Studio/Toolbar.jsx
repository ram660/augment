import React from 'react'

function Toolbar({ tool, onToolChange }) {
  const tools = [
    { id: 'select', icon: '🖱️', label: 'Select' },
    { id: 'pan', icon: '✋', label: 'Pan' },
    { id: 'measure', icon: '📏', label: 'Measure' },
    { id: 'annotate', icon: '✏️', label: 'Annotate' },
    { id: 'color', icon: '🎨', label: 'Color Picker' }
  ]

  return (
    <div className="canvas-toolbar">
      {tools.map((t, index) => (
        <React.Fragment key={t.id}>
          <button
            className={`toolbar-btn ${tool === t.id ? 'active' : ''}`}
            onClick={() => onToolChange(t.id)}
            title={t.label}
          >
            {t.icon}
          </button>
          {index === 1 && <div className="toolbar-divider" />}
        </React.Fragment>
      ))}
    </div>
  )
}

export default Toolbar

