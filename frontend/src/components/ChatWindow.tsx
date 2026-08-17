import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getApiUrl } from '../config/api';
import { Download, Copy, Sparkles, Send, CheckCircle2 } from 'lucide-react';

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
  latency_ms: number;
  detail: string;
  timestamp: number;
}

export interface Message {
  id: string;
  sender: 'User' | 'Assistant' | 'System';
  text: string;
  rewrittenQuery?: string;
  sources?: Source[];
  confidenceScore?: number;
  traces?: TraceStep[];
  userFeedback?: number;
  timestamp?: string;
}

interface ChatWindowProps {
  currentSessionId?: string;
  onSaveSession?: (sessionId: string, firstQuestion: string, messages: Message[]) => void;
  initialMessages?: Message[];
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  currentSessionId,
  onSaveSession,
  initialMessages
}) => {
  const { currentUser, isDarkMode } = useAuth();
  const [question, setQuestion] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeAgentStatus, setActiveAgentStatus] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [copiedNotification, setCopiedNotification] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>(() => {
    if (initialMessages && initialMessages.length > 0) return initialMessages;
    return [
      {
        id: 'msg_init',
        sender: 'System',
        text: `Enterprise Knowledge Assistant initialized for ${currentUser.name} (${currentUser.role} Role | ${currentUser.securityClearance} Clearance). Role-Based Access Control active.`,
        timestamp: new Date().toLocaleTimeString()
      }
    ];
  });

  useEffect(() => {
    if (initialMessages && initialMessages.length > 0) {
      setMessages(initialMessages);
    }
  }, [initialMessages]);

  // Handle Send Question
  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isStreaming) return;

    const currentQ = question.trim();
    setQuestion('');
    setIsStreaming(true);

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsgId = `msg_${Date.now()}_u`;
    const assistantMsgId = `msg_${Date.now()}_a`;

    // Extract recent history memory
    const recentHistory = messages
      .filter((m) => m.sender === 'User' || m.sender === 'Assistant')
      .slice(-4)
      .map((m) => ({
        role: m.sender === 'User' ? 'user' : 'assistant',
        content: m.text
      }));

    const newMessages: Message[] = [
      ...messages,
      { id: userMsgId, sender: 'User', text: currentQ, timestamp: timeStr },
      {
        id: assistantMsgId,
        sender: 'Assistant',
        text: '',
        sources: [],
        traces: [],
        rewrittenQuery: '',
        confidenceScore: 0,
        timestamp: timeStr
      }
    ];

    setMessages(newMessages);

    try {
      const streamUrl = getApiUrl('/api/v1/chat/stream');
      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: currentQ,
          role: currentUser.role,
          department: currentUser.department,
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

                // Notify parent to persist session
                if (onSaveSession) {
                  onSaveSession(currentSessionId || `sess_${Date.now()}`, currentQ, updated);
                }

                return updated;
              });
            } catch {
              // Ignore parse errors
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

  // Submit Feedback
  const submitFeedback = async (msgId: string, questionText: string, answerText: string, rating: number) => {
    try {
      const feedbackUrl = getApiUrl('/api/v1/feedback');
      await fetch(feedbackUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: questionText,
          answer: answerText,
          rating: rating,
          user_id: currentUser.id,
          role: currentUser.role
        })
      });

      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, userFeedback: rating } : m))
      );
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  // Task B4: Export Transcript to Markdown (.md)
  const handleExportMarkdown = () => {
    let mdContent = `# Enterprise Knowledge Assistant Transcript\n\n`;
    mdContent += `**User Profile:** ${currentUser.name} (${currentUser.role} Role | ${currentUser.department} Dept)\n`;
    mdContent += `**Export Date:** ${new Date().toLocaleString()}\n\n---\n\n`;

    messages.forEach((m) => {
      if (m.sender === 'User') {
        mdContent += `### 💬 User Question:\n${m.text}\n\n`;
      } else if (m.sender === 'Assistant') {
        mdContent += `### 🤖 Assistant Answer (Confidence: ${m.confidenceScore || '90'}%):\n${m.text}\n\n`;
        if (m.sources && m.sources.length > 0) {
          mdContent += `**Cited Sources:**\n`;
          m.sources.forEach((s) => {
            mdContent += `- **${s.title}** (${s.department} Dept - ${s.security_level})\n`;
          });
          mdContent += `\n`;
        }
        mdContent += `---\n\n`;
      }
    });

    const blob = new Blob([mdContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `EKA_Transcript_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Task B4: Copy Sources to Clipboard
  const handleCopyCitations = () => {
    const lastAssistantMsg = [...messages].reverse().find((m) => m.sender === 'Assistant' && m.sources && m.sources.length > 0);
    if (!lastAssistantMsg || !lastAssistantMsg.sources) {
      alert('No cited sources available to copy.');
      return;
    }

    const citationsText = lastAssistantMsg.sources
      .map((s, idx) => `[Source ${idx + 1}] Title: ${s.title} | Department: ${s.department} | Clearance: ${s.security_level}`)
      .join('\n');

    navigator.clipboard.writeText(citationsText);
    setCopiedNotification('Citations copied to clipboard!');
    setTimeout(() => setCopiedNotification(null), 3000);
  };

  // Download Individual Source Passage (.txt)
  const handleDownloadSource = (src: Source) => {
    let content = `Document Title: ${src.title}\n`;
    content += `Department: ${src.department}\n`;
    content += `Security Level: ${src.security_level}\n`;
    content += `Document ID: ${src.doc_id || 'doc_ref'}\n\n`;
    content += `==========================================\n`;
    content += `        EXTRACTED PASSAGE CONTENT         \n`;
    content += `==========================================\n\n`;
    content += `${src.text || 'Official enterprise document passage retrieved matching query.'}\n`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${src.title.replace(/[^a-zA-Z0-9_-]/g, '_')}_Citation.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      flex: 1,
      padding: '1.5rem 1.5rem 2.5rem 1.5rem',
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 70px)',
      boxSizing: 'border-box',
      background: isDarkMode ? '#141421' : '#f8fafc',
      color: isDarkMode ? '#f1f5f9' : '#1e293b'
    }}>

      {/* User Context & Action Header Bar (Integration 1 & Task B4) */}
      <div style={{
        marginBottom: '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: isDarkMode ? '#1e1e2d' : '#ffffff',
        padding: '0.75rem 1.2rem',
        borderRadius: '10px',
        border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.03)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span style={{ fontSize: '1.4rem' }}>{currentUser.avatar}</span>
          <div>
            <strong style={{ fontSize: '0.9rem', display: 'block' }}>{currentUser.name} ({currentUser.title})</strong>
            <span style={{ fontSize: '0.78rem', color: isDarkMode ? '#a0a0b0' : '#64748b' }}>
              Department Scope: <strong>{currentUser.department}</strong> | Security Clearance: <strong>{currentUser.securityClearance}</strong>
            </span>
          </div>
        </div>

        {/* Task B4: Export Action Controls */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleCopyCitations}
            style={{
              background: isDarkMode ? '#2b2b3d' : '#f1f5f9',
              color: isDarkMode ? '#cbd5e1' : '#475569',
              border: '1px solid #ccc',
              borderRadius: '6px',
              padding: '0.4rem 0.7rem',
              fontSize: '0.8rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem'
            }}
            title="Copy all cited document sources"
          >
            <Copy size={14} /> Copy Citations
          </button>

          <button
            onClick={handleExportMarkdown}
            style={{
              background: '#0066cc',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              padding: '0.4rem 0.75rem',
              fontSize: '0.8rem',
              fontWeight: 'bold',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem'
            }}
          >
            <Download size={14} /> Export Markdown (.md)
          </button>
        </div>
      </div>

      {/* Copy Notification Toast */}
      {copiedNotification && (
        <div style={{
          background: '#10b981',
          color: '#fff',
          padding: '0.4rem 0.8rem',
          borderRadius: '6px',
          fontSize: '0.82rem',
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem'
        }}>
          <CheckCircle2 size={16} /> {copiedNotification}
        </div>
      )}

      {/* Main Messages Container */}
      <div style={{
        flex: 1,
        border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
        borderRadius: '10px',
        padding: '1.2rem',
        marginBottom: '1rem',
        overflowY: 'auto',
        background: isDarkMode ? '#1a1a29' : '#ffffff'
      }}>
        {messages.map((m) => (
          <div key={m.id} style={{
            marginBottom: '1.4rem',
            background: isDarkMode ? '#242438' : '#f8fafc',
            border: isDarkMode ? '1px solid #33334d' : '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '1.1rem'
          }}>

            {/* Header: Sender & Confidence Score Badge (Task B3) */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontWeight: 'bold', fontSize: '0.92rem', color: m.sender === 'User' ? '#0066cc' : m.sender === 'Assistant' ? '#10b981' : '#64748b' }}>
                  {m.sender === 'User' ? `💬 ${currentUser.name}` : m.sender === 'Assistant' ? '🤖 Enterprise Assistant' : '⚙️ System'}
                </span>
                {m.timestamp && <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>• {m.timestamp}</span>}
              </div>

              {m.sender === 'Assistant' && m.confidenceScore ? (
                <span style={{
                  fontSize: '0.78rem',
                  fontWeight: 'bold',
                  padding: '0.2rem 0.65rem',
                  borderRadius: '12px',
                  background: m.confidenceScore > 85 ? '#dcfce7' : '#fef3c7',
                  color: m.confidenceScore > 85 ? '#15803d' : '#b45309',
                  border: `1px solid ${m.confidenceScore > 85 ? '#86efac' : '#fde047'}`
                }}>
                  🟢 {m.confidenceScore}% Confidence Score
                </span>
              ) : null}
            </div>

            {/* Rewritten Query Badge */}
            {m.rewrittenQuery && (
              <div style={{
                fontSize: '0.82rem',
                background: isDarkMode ? '#1e1e2d' : '#e0f2fe',
                color: isDarkMode ? '#93c5fd' : '#0369a1',
                padding: '0.4rem 0.7rem',
                borderRadius: '6px',
                marginBottom: '0.8rem',
                border: isDarkMode ? '1px solid #2b2b3d' : '1px solid #bae6fd'
              }}>
                🔍 <strong>Agent Query Optimization:</strong> "{m.rewrittenQuery}"
              </div>
            )}

            {/* Message Text */}
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6', fontSize: '0.95rem' }}>{m.text}</div>

            {/* Multi-Agent Telemetry Details */}
            {m.traces && m.traces.length > 0 && (
              <details style={{ marginTop: '0.8rem', fontSize: '0.82rem', background: isDarkMode ? '#1e1e2d' : '#f1f5f9', padding: '0.5rem 0.8rem', borderRadius: '6px' }}>
                <summary style={{ cursor: 'pointer', fontWeight: '600', color: '#0066cc' }}>
                  🛠️ Multi-Agent Execution Telemetry ({m.traces.length} steps)
                </summary>
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  {m.traces.map((tr, tIdx) => (
                    <div key={tIdx} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed #ccc', paddingBottom: '0.2rem' }}>
                      <span>▶ <strong>{tr.node}:</strong> {tr.detail}</span>
                      <span style={{ color: '#888', marginLeft: '1rem' }}>⏱️ {tr.latency_ms} ms</span>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {/* Cited Sources Cards */}
            {m.sources && m.sources.length > 0 && (
              <div style={{ marginTop: '1rem', paddingTop: '0.8rem', borderTop: isDarkMode ? '1px solid #33334d' : '1px solid #e2e8f0' }}>
                <strong style={{ fontSize: '0.88rem' }}>📚 Grounded Citations (Click to view or download passage):</strong>
                <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginTop: '0.5rem' }}>
                  {m.sources.map((src, sIdx) => (
                    <div
                      key={sIdx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        background: isDarkMode ? '#1e293b' : '#eff6ff',
                        border: isDarkMode ? '1px solid #334155' : '1px solid #bfdbfe',
                        borderRadius: '6px',
                        padding: '0.3rem 0.6rem',
                        fontSize: '0.82rem'
                      }}
                    >
                      <button
                        onClick={() => setSelectedSource(src)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: isDarkMode ? '#93c5fd' : '#1d4ed8',
                          cursor: 'pointer',
                          textAlign: 'left',
                          padding: 0,
                          fontWeight: '500'
                        }}
                      >
                        📄 <strong>{src.title}</strong> ({src.department})
                        <span style={{ marginLeft: '0.4rem', opacity: 0.8 }}>Clearance: {src.security_level}</span>
                      </button>

                      <button
                        onClick={() => handleDownloadSource(src)}
                        style={{
                          background: '#0066cc',
                          color: '#ffffff',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '0.2rem 0.4rem',
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.2rem'
                        }}
                        title="Download Document Passage Text File"
                      >
                        <Download size={12} /> Download
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Feedback Buttons */}
            {m.sender === 'Assistant' && m.text && (
              <div style={{ marginTop: '0.8rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>Was this answer helpful?</span>
                <button
                  onClick={() => submitFeedback(m.id, messages[messages.length - 2]?.text || '', m.text, 1)}
                  style={{
                    background: m.userFeedback === 1 ? '#4ade80' : isDarkMode ? '#2b2b3d' : '#fff',
                    color: m.userFeedback === 1 ? '#000' : 'inherit',
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
                    background: m.userFeedback === -1 ? '#f87171' : isDarkMode ? '#2b2b3d' : '#fff',
                    color: m.userFeedback === -1 ? '#fff' : 'inherit',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    padding: '0.2rem 0.5rem',
                    cursor: 'pointer'
                  }}
                >
                  👎 Incorrect
                </button>
                {m.userFeedback && <span style={{ fontSize: '0.8rem', color: '#10b981' }}>Saved!</span>}
              </div>
            )}

          </div>
        ))}
      </div>

      {/* Streaming Agent Status Indicator */}
      {isStreaming && (
        <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: '#0066cc', fontStyle: 'italic', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Sparkles size={16} /> {activeAgentStatus || '⚙️ Processing multi-agent pipeline...'}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSend} style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '1rem',
        background: isDarkMode ? '#1e1e2d' : '#ffffff',
        padding: '0.8rem',
        borderRadius: '10px',
        border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)'
      }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={`Ask a question as ${currentUser.name} (${currentUser.role} Role)...`}
          disabled={isStreaming}
          style={{
            flex: 1,
            padding: '0.75rem',
            borderRadius: '6px',
            border: isDarkMode ? '1px solid #3d3d52' : '1px solid #cbd5e1',
            background: isDarkMode ? '#2b2b3d' : '#ffffff',
            color: isDarkMode ? '#ffffff' : '#1a1a1a',
            fontSize: '0.95rem'
          }}
        />
        <button
          type="submit"
          disabled={isStreaming}
          style={{
            padding: '0.75rem 1.5rem',
            borderRadius: '6px',
            cursor: 'pointer',
            background: '#0066cc',
            color: '#fff',
            border: 'none',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}
        >
          <Send size={16} /> {isStreaming ? 'Thinking...' : 'Send'}
        </button>
      </form>

      {/* Source Viewer Modal Overlay */}
      {selectedSource && (
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
          backdropFilter: 'blur(3px)'
        }}>
          <div style={{
            background: isDarkMode ? '#1e1e2d' : '#ffffff',
            color: isDarkMode ? '#ffffff' : '#1a1a1a',
            padding: '1.8rem',
            borderRadius: '12px',
            maxWidth: '650px',
            width: '90%',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}>
            <h3 style={{ marginTop: 0 }}>📄 {selectedSource.title}</h3>
            <p><strong>Department:</strong> {selectedSource.department} | <strong>Security Level:</strong> {selectedSource.security_level}</p>
            <p><strong>Document ID:</strong> {selectedSource.doc_id || 'doc_ref'}</p>
            <div style={{
              background: isDarkMode ? '#2b2b3d' : '#f8fafc',
              padding: '1rem',
              borderRadius: '6px',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              whiteSpace: 'pre-wrap',
              border: isDarkMode ? '1px solid #3d3d52' : '1px solid #e2e8f0'
            }}>
              {selectedSource.text || 'Official enterprise document passage retrieved matching query.'}
            </div>
            <div style={{ marginTop: '1.2rem', display: 'flex', gap: '0.8rem', justifyContent: 'flex-end' }}>
              <button
                onClick={() => handleDownloadSource(selectedSource)}
                style={{
                  padding: '0.55rem 1rem',
                  background: '#0066cc',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  fontSize: '0.85rem'
                }}
              >
                <Download size={14} /> Download Passage (.txt)
              </button>
              <button
                onClick={() => setSelectedSource(null)}
                style={{
                  padding: '0.55rem 1rem',
                  background: '#334155',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}
              >
                Close Source Viewer
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
