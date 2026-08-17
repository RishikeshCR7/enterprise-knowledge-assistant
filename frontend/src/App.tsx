import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar, ChatSession } from './components/Sidebar';
import { ChatWindow, Message } from './components/ChatWindow';
import { UploadPage } from './pages/UploadPage';
import { Dashboard } from './pages/Dashboard';

export const AppContent: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem('eka_chat_sessions');
    if (saved) {
      try { return JSON.parse(saved); } catch {}
    }
    return [];
  });

  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    const savedSessions = localStorage.getItem('eka_chat_sessions');
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions);
        if (parsed.length > 0) return parsed[0].id;
      } catch {}
    }
    return `sess_${Date.now()}`;
  });

  const [activeMessages, setActiveMessages] = useState<Message[]>([]);

  // Load session messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      const savedMsgs = localStorage.getItem(`eka_msgs_${activeSessionId}`);
      if (savedMsgs) {
        try {
          setActiveMessages(JSON.parse(savedMsgs));
        } catch {}
      } else {
        setActiveMessages([]);
      }
    }
  }, [activeSessionId]);

  // Save or update session
  const handleSaveSession = (sessionId: string, firstQuestion: string, messages: Message[]) => {
    const targetSessionId = sessionId || activeSessionId || `sess_${Date.now()}`;
    if (targetSessionId !== activeSessionId) {
      setActiveSessionId(targetSessionId);
    }

    setActiveMessages(messages);
    localStorage.setItem(`eka_msgs_${targetSessionId}`, JSON.stringify(messages));

    setSessions((prev) => {
      const exists = prev.find((s) => s.id === targetSessionId);
      if (exists) return prev;

      const newSession: ChatSession = {
        id: targetSessionId,
        title: firstQuestion.length > 25 ? firstQuestion.slice(0, 25) + '...' : firstQuestion,
        timestamp: Date.now(),
        userRole: 'Active User'
      };
      const updated = [newSession, ...prev];
      localStorage.setItem('eka_chat_sessions', JSON.stringify(updated));
      return updated;
    });
  };

  // Start new session
  const handleNewSession = () => {
    const newId = `sess_${Date.now()}`;
    setActiveSessionId(newId);
    setActiveMessages([]);
  };

  // Delete session
  const handleDeleteSession = (sessionId: string) => {
    const updated = sessions.filter((s) => s.id !== sessionId);
    setSessions(updated);
    localStorage.setItem('eka_chat_sessions', JSON.stringify(updated));
    localStorage.removeItem(`eka_msgs_${sessionId}`);

    if (activeSessionId === sessionId) {
      const remainingId = updated.length > 0 ? updated[0].id : `sess_${Date.now()}`;
      setActiveSessionId(remainingId);
      setActiveMessages([]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'sans-serif' }}>
      <Navbar />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={(id) => setActiveSessionId(id)}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
        />
        <main style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          <Routes>
            <Route
              path="/"
              element={
                <ChatWindow
                  key={activeSessionId}
                  currentSessionId={activeSessionId}
                  onSaveSession={handleSaveSession}
                  initialMessages={activeMessages}
                />
              }
            />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

export default App;
