import React from 'react';

export const Navbar: React.FC = () => {
  return (
    <header style={{ padding: '1rem', borderBottom: '1px solid #ccc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <h2>Enterprise Knowledge Assistant</h2>
      <div>
        <span>Role: <strong>HR / Executive</strong></span>
      </div>
    </header>
  );
};
