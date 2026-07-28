import React from 'react';
import { Link } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  return (
    <aside style={{ width: '200px', borderRight: '1px solid #ccc', padding: '1rem' }}>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <Link to="/">Chat Window</Link>
        <Link to="/upload">Upload Page</Link>
        <Link to="/dashboard">Dashboard</Link>
      </nav>
    </aside>
  );
};
