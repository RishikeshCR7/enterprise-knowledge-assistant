import React, { useState } from 'react';

export const ChatWindow: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Array<{ sender: string; text: string }>>([
    { sender: 'System', text: 'Hello Enterprise AI' }
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setMessages((prev) => [...prev, { sender: 'User', text: question }]);
    const currentQ = question;
    setQuestion('');

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: currentQ, role: 'HR', department: 'HR' })
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { sender: 'Assistant', text: data.answer || 'Coming Soon' }]);
    } catch {
      setMessages((prev) => [...prev, { sender: 'Assistant', text: 'Error connecting to backend API.' }]);
    }
  };

  return (
    <div style={{ flex: 1, padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <h3>Chat Window Placeholder</h3>
      <div style={{ flex: 1, border: '1px solid #eee', padding: '1rem', marginBottom: '1rem', overflowY: 'auto' }}>
        {messages.map((m, idx) => (
          <div key={idx} style={{ marginBottom: '0.5rem' }}>
            <strong>{m.sender}:</strong> {m.text}
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          style={{ flex: 1, padding: '0.5rem' }}
        />
        <button type="submit" style={{ padding: '0.5rem 1rem' }}>Send</button>
      </form>
    </div>
  );
};
