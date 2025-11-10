import React from 'react'

function Toolbar({ tool, onToolChange, onSave, saving, onAutoArrange }) {
  const tools = [
    { id: 'select', icon: '🖱️', label: 'Select' },
    { id: 'polygon', icon: '⬠', label: 'Polygon Select' },
    { id: 'segment', icon: '🧩', label: 'Segment Select' },
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
      <div className="toolbar-divider" />
      <button className="toolbar-btn" onClick={onAutoArrange} title="Auto-arrange">
        ↻
      </button>
      <button className="toolbar-btn" onClick={onSave} title="Save canvas" disabled={saving}>
        {saving ? '💾…' : '💾'}
      </button>
    </div>
  )
}

export default Toolbar

