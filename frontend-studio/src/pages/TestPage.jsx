import React from 'react'

const TestPage = ({ homeId, homes = [] }) => {
  return (
    <div style={{ padding: '40px' }}>
      <h1>Test Page</h1>
      <p>Home ID: {homeId}</p>
      <p>Number of homes: {homes.length}</p>
      <pre>{JSON.stringify(homes, null, 2)}</pre>
    </div>
  )
}

export default TestPage

