import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MessageSquare, FolderUp, BarChart2, PlusCircle, Trash2, Clock } from 'lucide-react';

export interface ChatSession {
  id: string;
  title: string;
  timestamp: number;
  userRole: string;
}

interface SidebarProps {
  sessions?: ChatSession[];
  activeSessionId?: string;
  onSelectSession?: (id: string) => void;
  onNewSession?: () => void;
  onDeleteSession?: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions = [],
  activeSessionId = '',
  onSelectSession,
  onNewSession,
  onDeleteSession
}) => {
  const { isDarkMode } = useAuth();

  return (
    <aside style={{
      width: '240px',
      background: isDarkMode ? '#1e1e2d' : '#f8fafc',
      color: isDarkMode ? '#e2e8f0' : '#1e293b',
      borderRight: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
      padding: '1.2rem 1rem',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      height: 'calc(100vh - 60px)',
      boxSizing: 'border-box'
    }}>
      <div>
        {/* New Chat Button */}
        <button
          onClick={onNewSession}
          style={{
            width: '100%',
            padding: '0.7rem 1rem',
            background: 'linear-gradient(135deg, #0066cc 0%, #0284c7 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '8px',
            fontWeight: '600',
            fontSize: '0.9rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            boxShadow: '0 2px 6px rgba(0,102,204,0.25)',
            marginBottom: '1.2rem'
          }}
        >
          <PlusCircle size={18} /> Start New Chat
        </button>

        {/* Primary Navigation Links */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1.5rem' }}>
          <NavLink
            to="/"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '0.88rem',
              fontWeight: '500',
              color: isActive 
                ? '#0066cc' 
                : isDarkMode ? '#cbd5e1' : '#475569',
              background: isActive 
                ? (isDarkMode ? '#1e293b' : '#e0f2fe') 
                : 'transparent'
            })}
          >
            <MessageSquare size={16} /> Assistant Chat
          </NavLink>

          <NavLink
            to="/upload"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '0.88rem',
              fontWeight: '500',
              color: isActive 
                ? '#0066cc' 
                : isDarkMode ? '#cbd5e1' : '#475569',
              background: isActive 
                ? (isDarkMode ? '#1e293b' : '#e0f2fe') 
                : 'transparent'
            })}
          >
            <FolderUp size={16} /> Knowledge Base
          </NavLink>

          <NavLink
            to="/dashboard"
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              padding: '0.6rem 0.8rem',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '0.88rem',
              fontWeight: '500',
              color: isActive 
                ? '#0066cc' 
                : isDarkMode ? '#cbd5e1' : '#475569',
              background: isActive 
                ? (isDarkMode ? '#1e293b' : '#e0f2fe') 
                : 'transparent'
            })}
          >
            <BarChart2 size={16} /> Admin Analytics
          </NavLink>
        </nav>

        {/* Task B3: Recent Conversation History List */}
        <div style={{ borderTop: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0', paddingTop: '1rem' }}>
          <div style={{
            fontSize: '0.75rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            color: isDarkMode ? '#94a3b8' : '#64748b',
            marginBottom: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}>
            <Clock size={13} /> Recent Sessions ({sessions.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '240px', overflowY: 'auto' }}>
            {sessions.length === 0 ? (
              <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic', padding: '0.4rem' }}>
                No past sessions saved.
              </span>
            ) : (
              sessions.map((s) => {
                const isSelected = s.id === activeSessionId;
                return (
                  <div
                    key={s.id}
                    onClick={() => onSelectSession?.(s.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.5rem 0.6rem',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.82rem',
                      background: isSelected 
                        ? (isDarkMode ? '#2b2b3d' : '#e2e8f0') 
                        : 'transparent',
                      color: isSelected 
                        ? '#0066cc' 
                        : isDarkMode ? '#cbd5e1' : '#475569'
                    }}
                  >
                    <span style={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '140px',
                      fontWeight: isSelected ? 'bold' : 'normal'
                    }}>
                      💬 {s.title}
                    </span>

                    {onDeleteSession && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(s.id);
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#ef4444',
                          cursor: 'pointer',
                          opacity: 0.7,
                          padding: '0.1rem'
                        }}
                        title="Delete Session"
                      >
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* System Footer Status */}
      <div style={{ fontSize: '0.72rem', color: isDarkMode ? '#64748b' : '#94a3b8', borderTop: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0', paddingTop: '0.8rem' }}>
        <strong>Enterprise RAG Platform</strong>
        <div>Phase 5 Release Build 5.1</div>
      </div>
    </aside>
  );
};
