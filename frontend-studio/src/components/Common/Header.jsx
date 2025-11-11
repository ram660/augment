import React from 'react'

function Header({ selectedHomeId, onHomeChange, homes }) {
  return (
    <div className="header">
      <div className="header-left">
        <div className="header-title">
          🏠 HomeVision AI Studio
        </div>
      </div>

      <div className="header-right">
        {homes && homes.length > 0 && (
          <select
            className="home-selector"
            value={selectedHomeId || ''}
            onChange={(e) => onHomeChange(e.target.value)}
          >
            {homes.map(home => (
              <option key={home.id} value={home.id}>
                {home.name || home.address || `Home ${home.id.slice(0, 8)}`}
              </option>
            ))}
          </select>
        )}

        <button className="header-btn" title="Settings">
          ⚙️ Settings
        </button>

        <button className="header-btn" title="Help">
          ❓ Help
        </button>
      </div>
    </div>
  )
}

export default Header

