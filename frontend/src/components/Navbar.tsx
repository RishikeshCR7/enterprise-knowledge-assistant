import React, { useState } from 'react';
import { useAuth, MOCK_USER_PROFILES } from '../context/AuthContext';
import { Shield, Moon, Sun, UserCheck, X } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { currentUser, switchUser, isDarkMode, toggleDarkMode } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);

  return (
    <header style={{
      padding: '0.8rem 1.5rem',
      background: isDarkMode ? '#1e1e2d' : '#ffffff',
      color: isDarkMode ? '#ffffff' : '#1a1a1a',
      borderBottom: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
      zIndex: 100
    }}>
      {/* App Branding Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #0066cc 0%, #004499 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontWeight: 'bold',
          fontSize: '1.2rem',
          boxShadow: '0 2px 8px rgba(0,102,204,0.3)'
        }}>
          🧠
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: '700', letterSpacing: '-0.3px' }}>
            Enterprise Knowledge Assistant
          </h2>
          <span style={{ fontSize: '0.75rem', color: isDarkMode ? '#a0a0b0' : '#64748b', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#22c55e', display: 'inline-block' }}></span>
            LangGraph RAG Platform v5.0 Active
          </span>
        </div>
      </div>

      {/* User Identity & Global Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        
        {/* Active Profile Info Box */}
        <div 
          onClick={() => setShowAuthModal(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            background: isDarkMode ? '#2b2b3d' : '#f1f5f9',
            padding: '0.4rem 0.8rem',
            borderRadius: '20px',
            border: isDarkMode ? '1px solid #3d3d52' : '1px solid #cbd5e1',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          title="Click to Switch User Role Profile"
        >
          <span style={{ fontSize: '1.2rem' }}>{currentUser.avatar}</span>
          <div style={{ fontSize: '0.82rem', textAlign: 'left' }}>
            <strong style={{ display: 'block', lineHeight: 1.2 }}>{currentUser.name}</strong>
            <span style={{ fontSize: '0.72rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
              {currentUser.role} ({currentUser.securityClearance})
            </span>
          </div>
          <Shield size={14} color="#0066cc" style={{ marginLeft: '0.2rem' }} />
        </div>

        {/* Switch Profile Action Button */}
        <button
          onClick={() => setShowAuthModal(true)}
          style={{
            background: '#0066cc',
            color: '#ffffff',
            border: 'none',
            borderRadius: '6px',
            padding: '0.45rem 0.85rem',
            fontSize: '0.82rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}
        >
          <UserCheck size={15} /> Switch Identity
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleDarkMode}
          style={{
            background: isDarkMode ? '#2b2b3d' : '#f1f5f9',
            color: isDarkMode ? '#fbbf24' : '#475569',
            border: 'none',
            borderRadius: '50%',
            width: '36px',
            height: '36px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'transform 0.2s ease'
          }}
          title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>

      {/* Role Profile Selector Overlay Modal (Task B1) */}
      {showAuthModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000,
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            background: isDarkMode ? '#1e1e2d' : '#ffffff',
            color: isDarkMode ? '#ffffff' : '#1a1a1a',
            padding: '1.8rem',
            borderRadius: '12px',
            maxWidth: '520px',
            width: '90%',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
            border: isDarkMode ? '1px solid #3d3d52' : '1px solid #e2e8f0'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                👤 Select Enterprise User Identity
              </h3>
              <button 
                onClick={() => setShowAuthModal(false)}
                style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: '0.85rem', color: isDarkMode ? '#a0a0b0' : '#64748b', marginBottom: '1.2rem' }}>
              Select a mock user profile to test Role-Based Access Control (RBAC) isolation and clearance policies across departments.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {MOCK_USER_PROFILES.map((p) => {
                const isActive = currentUser.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => {
                      switchUser(p.id);
                      setShowAuthModal(false);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.8rem',
                      padding: '0.75rem 1rem',
                      borderRadius: '8px',
                      border: isActive 
                        ? '2px solid #0066cc' 
                        : isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
                      background: isActive 
                        ? (isDarkMode ? '#1e293b' : '#eff6ff') 
                        : (isDarkMode ? '#2b2b3d' : '#f8fafc'),
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <span style={{ fontSize: '1.6rem' }}>{p.avatar}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', fontSize: '0.92rem' }}>
                        {p.name} {isActive && <span style={{ color: '#0066cc', fontSize: '0.8rem' }}>(Active)</span>}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
                        {p.title}
                      </div>
                    </div>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      padding: '0.2rem 0.5rem',
                      borderRadius: '12px',
                      background: p.role === 'Executive' ? '#fef3c7' : '#e0f2fe',
                      color: p.role === 'Executive' ? '#92400e' : '#0369a1'
                    }}>
                      {p.role} Clearance
                    </span>
                  </div>
                );
              })}
            </div>

            <button
              onClick={() => setShowAuthModal(false)}
              style={{
                marginTop: '1.2rem',
                width: '100%',
                padding: '0.65rem',
                background: '#334155',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              Done
            </button>
          </div>
        </div>
      )}

    </header>
  );
};
