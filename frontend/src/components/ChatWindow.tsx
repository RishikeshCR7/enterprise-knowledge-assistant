import React, { useState } from 'react';

interface Source {
  source_id: number;
  title: string;
  department: string;
  security_level: string;
  doc_id?: string;
  score?: number;
}

interface Message {
  sender: 'User' | 'Assistant' | 'System';
  text: string;
  rewrittenQuery?: string;
  sources?: Source[];
}

export const ChatWindow: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [userRole, setUserRole] = useState('HR');
  const [department, setDepartment] = useState('HR');
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'System', text: 'Welcome to Enterprise Knowledge Assistant RAG Portal.' }
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isStreaming) return;

    const currentQ = question.trim();
    setQuestion('');

    // Add user question
    setMessages((prev) => [...prev, { sender: 'User', text: currentQ }]);
    setIsStreaming(true);

    // Placeholder assistant message
    const assistantIndex = messages.length + 1;
    setMessages((prev) => [
      ...prev,
      { sender: 'Assistant', text: '', sources: [], rewrittenQuery: '' }
    ]);

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: currentQ,
          role: userRole,
          department: department
        })
      });

      if (!response.ok || !response.body) {
        throw new Error('Streaming connection failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let streamedText = '';
      let extractedSources: Source[] = [];
      let rewritten = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (dataStr === '[DONE]') break;

            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.type === 'metadata') {
                rewritten = parsed.rewritten_query || '';
                extractedSources = parsed.sources || [];
              } else if (parsed.type === 'token') {
                streamedText += parsed.content;
              }

              // Update assistant message state live
              setMessages((prev) => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx].sender === 'Assistant') {
                  updated[lastIdx] = {
                    sender: 'Assistant',
                    text: streamedText,
                    rewrittenQuery: rewritten,
                    sources: extractedSources
                  };
                }
                return updated;
              });
            } catch {
              // Ignore partial JSON chunks
            }
          }
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { sender: 'Assistant', text: 'Error connecting to streaming server API.' }
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div style={{ flex: 1, padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Role & Department selector */}
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <label>
          <strong>User Role: </strong>
          <select value={userRole} onChange={(e) => setUserRole(e.target.value)} style={{ padding: '0.3rem' }}>
            <option value="HR">HR</option>
            <option value="Engineering">Engineering</option>
            <option value="Finance">Finance</option>
            <option value="Legal">Legal</option>
            <option value="Sales">Sales</option>
            <option value="Executive">Executive</option>
          </select>
        </label>
        <label>
          <strong>Department: </strong>
          <select value={department} onChange={(e) => setDepartment(e.target.value)} style={{ padding: '0.3rem' }}>
            <option value="HR">HR</option>
            <option value="Engineering">Engineering</option>
            <option value="Finance">Finance</option>
            <option value="Legal">Legal</option>
            <option value="Sales">Sales</option>
          </select>
        </label>
      </div>

      {/* Messages Scroll View */}
      <div style={{ flex: 1, border: '1px solid #ddd', borderRadius: '8px', padding: '1rem', marginBottom: '1rem', overflowY: 'auto', background: '#fafafa' }}>
        {messages.map((m, idx) => (
          <div key={idx} style={{ marginBottom: '1.2rem' }}>
            <div style={{ fontWeight: 'bold', color: m.sender === 'User' ? '#0066cc' : m.sender === 'Assistant' ? '#2e7d32' : '#666' }}>
              {m.sender}:
            </div>

            {m.rewrittenQuery && (
              <div style={{ fontSize: '0.85rem', fontStyle: 'italic', color: '#666', marginTop: '0.2rem', marginBottom: '0.4rem' }}>
                🔍 Rewritten Query: "{m.rewrittenQuery}"
              </div>
            )}

            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{m.text}</div>

            {/* Sources Cards (Task B5 Integration) */}
            {m.sources && m.sources.length > 0 && (
              <div style={{ marginTop: '0.8rem', paddingTop: '0.5rem', borderTop: '1px dashed #ccc' }}>
                <strong style={{ fontSize: '0.9rem' }}>📚 Cited Sources:</strong>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.4rem' }}>
                  {m.sources.map((src, sIdx) => (
                    <div key={sIdx} style={{ background: '#fff', border: '1px solid #bbb', borderRadius: '6px', padding: '0.4rem 0.8rem', fontSize: '0.82rem' }}>
                      📄 <strong>{src.title}</strong> ({src.department})
                      <span style={{ marginLeft: '0.4rem', color: '#888' }}>Clearance: {src.security_level}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Chat Input Form */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask enterprise assistant..."
          disabled={isStreaming}
          style={{ flex: 1, padding: '0.75rem', borderRadius: '6px', border: '1px solid #ccc' }}
        />
        <button type="submit" disabled={isStreaming} style={{ padding: '0.75rem 1.5rem', borderRadius: '6px', cursor: 'pointer', background: '#0066cc', color: '#fff', border: 'none' }}>
          {isStreaming ? 'Thinking...' : 'Send'}
        </button>
      </form>
    </div>
  );
};
