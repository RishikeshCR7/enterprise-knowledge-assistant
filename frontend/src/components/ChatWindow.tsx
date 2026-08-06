import React, { useState } from 'react';

interface Source {
  source_id: number;
  title: string;
  department: string;
  security_level: string;
  doc_id?: string;
  score?: number;
  text?: string;
}

interface TraceStep {
  node: string;
  status: string;
  latency_ms: float;
  detail: string;
  timestamp: float;
}

interface Message {
  id: string;
  sender: 'User' | 'Assistant' | 'System';
  text: string;
  rewrittenQuery?: string;
  sources?: Source[];
  confidenceScore?: number;
  traces?: TraceStep[];
  userFeedback?: number; // 1 for helpful, -1 for incorrect
}

export const ChatWindow: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [userRole, setUserRole] = useState('HR');
  const [department, setDepartment] = useState('HR');
  const [isStreaming, setIsStreaming] = useState(false);

  // Source Viewer Modal State (Task B2)
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);

  // Multi-Agent Live Execution Status
  const [activeAgentStatus, setActiveAgentStatus] = useState<string>('');

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg_init',
      sender: 'System',
      text: 'Enterprise Knowledge Assistant initialized. Role-Based Access Control (RBAC) and Multi-Agent Orchestration active.'
    }
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isStreaming) return;

    const currentQ = question.trim();
    setQuestion('');
    setIsStreaming(true);

    const userMsgId = `msg_${Date.now()}_u`;
    const assistantMsgId = `msg_${Date.now()}_a`;

    // Extract recent conversation memory history (Integration 2)
    const recentHistory = messages
      .filter((m) => m.sender === 'User' || m.sender === 'Assistant')
      .slice(-4)
      .map((m) => ({
        role: m.sender === 'User' ? 'user' : 'assistant',
        content: m.text
      }));

    // Add user message
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'User', text: currentQ }
    ]);

    // Add empty assistant message placeholder
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        sender: 'Assistant',
        text: '',
        sources: [],
        traces: [],
        rewrittenQuery: '',
        confidenceScore: 0
      }
    ]);

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: currentQ,
          role: userRole,
          department: department,
          chat_history: recentHistory
        })
      });

      if (!response.ok || !response.body) {
        throw new Error('Connection failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let streamedText = '';
      let extractedSources: Source[] = [];
      let rewritten = '';
      let confidence = 90;
      const accumulatedTraces: TraceStep[] = [];

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
              if (parsed.type === 'trace') {
                const tr: TraceStep = parsed.data;
                accumulatedTraces.push(tr);
                setActiveAgentStatus(`⚙️ ${tr.node}: ${tr.detail}`);
              } else if (parsed.type === 'metadata') {
                rewritten = parsed.rewritten_query || '';
                extractedSources = parsed.sources || [];
                confidence = parsed.confidence_score || 90;
                setActiveAgentStatus('✨ Streaming tokens...');
              } else if (parsed.type === 'token') {
                streamedText += parsed.content;
              }

              // Live state update
              setMessages((prev) => {
                const updated = [...prev];
                const targetIdx = updated.findIndex((m) => m.id === assistantMsgId);
                if (targetIdx !== -1) {
                  updated[targetIdx] = {
                    ...updated[targetIdx],
                    text: streamedText,
                    rewrittenQuery: rewritten,
                    sources: extractedSources,
                    confidenceScore: confidence,
                    traces: [...accumulatedTraces]
                  };
                }
                return updated;
              });
            } catch {
              // Ignore chunk parse errors
            }
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const updated = [...prev];
        const targetIdx = updated.findIndex((m) => m.id === assistantMsgId);
        if (targetIdx !== -1) {
          updated[targetIdx] = {
            ...updated[targetIdx],
            text: 'Error communicating with enterprise assistant backend.'
          };
        }
        return updated;
      });
    } finally {
      setIsStreaming(false);
      setActiveAgentStatus('');
    }
  };

  const submitFeedback = async (msgId: string, questionText: string, answerText: string, rating: number) => {
    try {
      await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: questionText,
          answer: answerText,
          rating: rating,
          user_id: 'usr_demo',
          role: userRole
        })
      });

      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, userFeedback: rating } : m))
      );
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  return (
    <div style={{ flex: 1, padding: '1.5rem', display: 'flex', flexDirection: 'column', height: '100%', fontFamily: 'Inter, sans-serif' }}>
      
      {/* Role & Department Selection Bar (Integration 1) */}
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center', background: '#eef2f6', padding: '0.75rem 1rem', borderRadius: '8px' }}>
        <label>
          <strong style={{ fontSize: '0.9rem' }}>👤 Active User Role: </strong>
          <select value={userRole} onChange={(e) => { setUserRole(e.target.value); setDepartment(e.target.value); }} style={{ padding: '0.4rem 0.8rem', borderRadius: '4px', border: '1px solid #ccc' }}>
            <option value="HR">HR Specialist</option>
            <option value="Engineering">Software Engineer</option>
            <option value="Finance">Finance Officer</option>
            <option value="Legal">Legal Counsel</option>
            <option value="Sales">Sales Executive</option>
            <option value="Executive">Executive Manager (All Access)</option>
          </select>
        </label>
        <span style={{ fontSize: '0.85rem', color: '#555' }}>
          🔒 Security Filter: <strong>{userRole} Department & Authorized Docs Only</strong>
        </span>
      </div>

      {/* Main Messages View */}
      <div style={{ flex: 1, border: '1px solid #e0e0e0', borderRadius: '8px', padding: '1.2rem', marginBottom: '1rem', overflowY: 'auto', background: '#fafafa' }}>
        {messages.map((m) => (
          <div key={m.id} style={{ marginBottom: '1.5rem', background: '#fff', border: '1px solid #e8e8e8', borderRadius: '8px', padding: '1rem' }}>
            
            {/* Sender & Confidence Badge (Task B3) */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 'bold', color: m.sender === 'User' ? '#0066cc' : m.sender === 'Assistant' ? '#2e7d32' : '#666' }}>
                {m.sender === 'User' ? '💬 You' : m.sender === 'Assistant' ? '🤖 Enterprise Assistant' : '⚙️ System'}
              </span>

              {m.sender === 'Assistant' && m.confidenceScore ? (
                <span style={{
                  fontSize: '0.8rem',
                  fontWeight: 'bold',
                  padding: '0.2rem 0.6rem',
                  borderRadius: '12px',
                  background: m.confidenceScore > 85 ? '#e8f5e9' : '#fff3e0',
                  color: m.confidenceScore > 85 ? '#2e7d32' : '#e65100',
                  border: `1px solid ${m.confidenceScore > 85 ? '#a5d6a7' : '#ffe0b2'}`
                }}>
                  🟢 {m.confidenceScore}% Confidence Score
                </span>
              ) : null}
            </div>

            {/* Rewritten Query Subtitle (Task B1) */}
            {m.rewrittenQuery && (
              <div style={{ fontSize: '0.82rem', background: '#f5f5f5', padding: '0.4rem 0.6rem', borderRadius: '4px', color: '#555', marginBottom: '0.8rem' }}>
                🔍 <strong>Agent Query Optimization:</strong> "{m.rewrittenQuery}"
              </div>
            )}

            {/* Message Body */}
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', fontSize: '0.95rem' }}>{m.text}</div>

            {/* Multi-Agent Trace Viewer (Task B1) */}
            {m.traces && m.traces.length > 0 && (
              <details style={{ marginTop: '0.8rem', fontSize: '0.82rem', background: '#f8f9fa', padding: '0.5rem 0.8rem', borderRadius: '6px', border: '1px solid #eee' }}>
                <summary style={{ cursor: 'pointer', fontWeight: '600', color: '#0066cc' }}>
                  🛠️ Multi-Agent Execution Telemetry ({m.traces.length} steps)
                </summary>
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {m.traces.map((tr, tIdx) => (
                    <div key={tIdx} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #eee', paddingBottom: '0.2rem' }}>
                      <span>▶ <strong>{tr.node}:</strong> {tr.detail}</span>
                      <span style={{ color: '#888', marginLeft: '1rem' }}>⏱️ {tr.latency_ms} ms</span>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {/* Sources Cards (Task B2 & B5) */}
            {m.sources && m.sources.length > 0 && (
              <div style={{ marginTop: '1rem', paddingTop: '0.8rem', borderTop: '1px solid #eee' }}>
                <strong style={{ fontSize: '0.88rem', color: '#333' }}>📚 Grounded Citations (Click to view passage):</strong>
                <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                  {m.sources.map((src, sIdx) => (
                    <button
                      key={sIdx}
                      onClick={() => setSelectedSource(src)}
                      style={{
                        background: '#e3f2fd',
                        border: '1px solid #90caf9',
                        borderRadius: '6px',
                        padding: '0.4rem 0.8rem',
                        fontSize: '0.82rem',
                        cursor: 'pointer',
                        textAlign: 'left'
                      }}
                    >
                      📄 <strong>{src.title}</strong> ({src.department})
                      <span style={{ marginLeft: '0.4rem', color: '#555' }}>Clearance: {src.security_level}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Feedback Loop Buttons (Task B4) */}
            {m.sender === 'Assistant' && m.text && (
              <div style={{ marginTop: '0.8rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: '#777' }}>Was this answer helpful?</span>
                <button
                  onClick={() => submitFeedback(m.id, messages[messages.length - 2]?.text || '', m.text, 1)}
                  style={{
                    background: m.userFeedback === 1 ? '#c8e6c9' : '#fff',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    padding: '0.2rem 0.5rem',
                    cursor: 'pointer'
                  }}
                >
                  👍 Helpful
                </button>
                <button
                  onClick={() => submitFeedback(m.id, messages[messages.length - 2]?.text || '', m.text, -1)}
                  style={{
                    background: m.userFeedback === -1 ? '#ffcdd2' : '#fff',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    padding: '0.2rem 0.5rem',
                    cursor: 'pointer'
                  }}
                >
                  👎 Incorrect
                </button>
                {m.userFeedback && <span style={{ fontSize: '0.8rem', color: '#2e7d32' }}>Thanks for feedback!</span>}
              </div>
            )}

          </div>
        ))}
      </div>

      {/* Active Streaming Agent Status Indicator */}
      {isStreaming && (
        <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: '#0066cc', fontStyle: 'italic' }}>
          {activeAgentStatus || '⚙️ Processing multi-agent pipeline...'}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about HR, Engineering, Finance, Legal policies..."
          disabled={isStreaming}
          style={{ flex: 1, padding: '0.75rem', borderRadius: '6px', border: '1px solid #ccc', fontSize: '0.95rem' }}
        />
        <button
          type="submit"
          disabled={isStreaming}
          style={{ padding: '0.75rem 1.5rem', borderRadius: '6px', cursor: 'pointer', background: '#0066cc', color: '#fff', border: 'none', fontWeight: 'bold' }}
        >
          {isStreaming ? 'Thinking...' : 'Send'}
        </button>
      </form>

      {/* Task B2 Source Viewer Modal Overlay */}
      {selectedSource && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', width: '90%', maxHeight: '80vh', overflowY: 'auto' }}>
            <h3 style={{ marginTop: 0 }}>📄 {selectedSource.title}</h3>
            <p><strong>Department:</strong> {selectedSource.department} | <strong>Security Level:</strong> {selectedSource.security_level}</p>
            <p><strong>Document ID:</strong> {selectedSource.doc_id || 'doc_ref'}</p>
            <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '6px', fontFamily: 'monospace', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}>
              {selectedSource.text || 'Official enterprise document passage retrieved matching query.'}
            </div>
            <button onClick={() => setSelectedSource(null)} style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#333', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
              Close Source Viewer
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
