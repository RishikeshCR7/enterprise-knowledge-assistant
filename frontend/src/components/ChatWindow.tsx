import React, { useState } from 'react';

<<<<<<< Updated upstream
=======
interface Source {
  source_id: number;
  title: string;
  department: string;
  security_level: string;
  doc_id?: string;
  score?: number;
  chunk_count?: number;
}

interface Message {
  sender: 'User' | 'Assistant' | 'System';
  text: string;
  rewrittenQuery?: string;
  confidenceScore?: number;
  latencyMs?: number;
  sources?: Source[];
  steps?: string[];
}

>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
=======
    const startTime = performance.now();
    // Add user question
    setMessages((prev) => [...prev, { sender: 'User', text: currentQ }]);
    setIsStreaming(true);

    // Placeholder assistant message with initial agent pipeline steps
    setMessages((prev) => [
      ...prev,
      {
        sender: 'Assistant',
        text: '',
        sources: [],
        rewrittenQuery: '',
        confidenceScore: undefined,
        steps: ['🔍 Classifying intent & rewriting query...']
      }
    ]);

>>>>>>> Stashed changes
    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: currentQ, role: 'HR', department: 'HR' })
      });
<<<<<<< Updated upstream
      const data = await res.json();
      setMessages((prev) => [...prev, { sender: 'Assistant', text: data.answer || 'Coming Soon' }]);
=======

      if (!response.ok || !response.body) {
        throw new Error('Streaming connection failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let streamedText = '';
      let extractedSources: Source[] = [];
      let rewritten = '';
      let confidence: number | undefined = undefined;

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
                confidence = parsed.confidence_score;
              } else if (parsed.type === 'token') {
                streamedText += parsed.content;
              }

              const elapsedMs = Math.round(performance.now() - startTime);
              const pipelineSteps = [
                `✓ Query Rewritten: "${rewritten.slice(0, 50)}..."`,
                `✓ Hybrid Search (Vector + BM25 RRF) Passed RBAC`,
                `✓ Cross-Encoder Reranked Top Chunks`,
                `✓ Grounded Generation Completed`
              ];

              // Update assistant message state live
              setMessages((prev) => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx].sender === 'Assistant') {
                  updated[lastIdx] = {
                    sender: 'Assistant',
                    text: streamedText,
                    rewrittenQuery: rewritten,
                    confidenceScore: confidence,
                    latencyMs: elapsedMs,
                    sources: extractedSources,
                    steps: pipelineSteps
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
>>>>>>> Stashed changes
    } catch {
      setMessages((prev) => [...prev, { sender: 'Assistant', text: 'Error connecting to backend API.' }]);
    }
  };

  return (
    <div style={{ flex: 1, padding: '1rem', display: 'flex', flexDirection: 'column' }}>
      <h3>Chat Window Placeholder</h3>
      <div style={{ flex: 1, border: '1px solid #eee', padding: '1rem', marginBottom: '1rem', overflowY: 'auto' }}>
        {messages.map((m, idx) => (
<<<<<<< Updated upstream
          <div key={idx} style={{ marginBottom: '0.5rem' }}>
            <strong>{m.sender}:</strong> {m.text}
=======
          <div key={idx} style={{ marginBottom: '1.2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontWeight: 'bold', color: m.sender === 'User' ? '#0066cc' : m.sender === 'Assistant' ? '#2e7d32' : '#666' }}>
                {m.sender}:
              </div>
              {m.sender === 'Assistant' && (
                <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
                  {m.latencyMs && (
                    <span style={{ fontSize: '0.75rem', color: '#666' }}>⏱️ {(m.latencyMs / 1000).toFixed(2)}s</span>
                  )}
                  {m.confidenceScore !== undefined && (
                    <span style={{ background: '#e8f5e9', color: '#2e7d32', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.78rem', fontWeight: 'bold' }}>
                      🎯 Confidence: {m.confidenceScore}%
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Agent Execution Pipeline Stepper */}
            {m.steps && m.steps.length > 0 && (
              <div style={{ background: '#f0f4f8', padding: '0.5rem 0.8rem', borderRadius: '6px', fontSize: '0.78rem', color: '#444', margin: '0.4rem 0' }}>
                {m.steps.map((st, sIdx) => (
                  <div key={sIdx} style={{ lineHeight: '1.4' }}>{st}</div>
                ))}
              </div>
            )}

            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5', marginTop: '0.4rem' }}>{m.text}</div>

            {/* Deduplicated Cited Sources Cards */}
            {m.sources && m.sources.length > 0 && (
              <div style={{ marginTop: '0.8rem', paddingTop: '0.5rem', borderTop: '1px dashed #ccc' }}>
                <strong style={{ fontSize: '0.88rem' }}>📚 Cited Sources ({m.sources.length} Unique Document{m.sources.length > 1 ? 's' : ''}):</strong>
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
>>>>>>> Stashed changes
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
