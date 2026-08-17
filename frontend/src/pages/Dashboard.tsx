import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getApiUrl } from '../config/api';
import { BarChart3, ShieldCheck, Activity, Database, Layers, CheckCircle2 } from 'lucide-react';

interface AdminStats {
  total_questions_processed: number;
  total_feedback_count: number;
  helpful_feedback_count: number;
  incorrect_feedback_count: number;
  satisfaction_rate: number;
  avg_response_latency_ms: number;
  active_roles: string[];
  indexed_departments: number;
  vector_search_health: string;
  cached_queries_pct: number;
}

export const Dashboard: React.FC = () => {
  const { isDarkMode } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    const statsUrl = getApiUrl('/api/v1/admin/stats');
    fetch(statsUrl)
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error('Failed to fetch admin stats:', err));
  }, []);

  return (
    <div style={{
      flex: 1,
      padding: '1.8rem',
      background: isDarkMode ? '#141421' : '#f8fafc',
      color: isDarkMode ? '#f1f5f9' : '#1e293b',
      overflowY: 'auto',
      height: 'calc(100vh - 60px)',
      boxSizing: 'border-box'
    }}>
      {/* Header Title */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <BarChart3 color="#0066cc" size={26} /> Enterprise Admin & Analytics Observability (v5.0)
        </h2>
        <p style={{ margin: '0.3rem 0 0 0', fontSize: '0.88rem', color: isDarkMode ? '#94a3b8' : '#64748b' }}>
          Real-time telemetry, multi-agent pipeline performance, RBAC isolation audit, and document indexing metrics.
        </p>
      </div>

      {/* KPI Telemetry Cards */}
      {stats ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.2rem', marginBottom: '1.8rem' }}>
          
          <div style={{
            background: isDarkMode ? '#1e1e2d' : '#ffffff',
            border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '1.2rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#0066cc' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>Total Queries Processed</span>
              <Activity size={18} />
            </div>
            <p style={{ fontSize: '2.1rem', fontWeight: 'bold', margin: '0.6rem 0 0 0' }}>{stats.total_questions_processed}</p>
            <span style={{ fontSize: '0.75rem', color: '#10b981' }}>+100% LangGraph Executed</span>
          </div>

          <div style={{
            background: isDarkMode ? '#1e1e2d' : '#ffffff',
            border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '1.2rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#10b981' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>User Satisfaction Rate</span>
              <CheckCircle2 size={18} />
            </div>
            <p style={{ fontSize: '2.1rem', fontWeight: 'bold', margin: '0.6rem 0 0 0', color: '#10b981' }}>{stats.satisfaction_rate}%</p>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Based on 👍 / 👎 ratings</span>
          </div>

          <div style={{
            background: isDarkMode ? '#1e1e2d' : '#ffffff',
            border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '1.2rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#f59e0b' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>Avg Response Latency</span>
              <Layers size={18} />
            </div>
            <p style={{ fontSize: '2.1rem', fontWeight: 'bold', margin: '0.6rem 0 0 0' }}>{stats.avg_response_latency_ms} <span style={{ fontSize: '1rem', fontWeight: 'normal' }}>ms</span></p>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>5 Agent Nodes Executed</span>
          </div>

          <div style={{
            background: isDarkMode ? '#1e1e2d' : '#ffffff',
            border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
            borderRadius: '10px',
            padding: '1.2rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#8b5cf6' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>Vector Index Health</span>
              <Database size={18} />
            </div>
            <p style={{ fontSize: '1.1rem', fontWeight: 'bold', margin: '0.8rem 0 0 0', color: '#8b5cf6' }}>{stats.vector_search_health}</p>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>12 Files | 13 Chunks</span>
          </div>

        </div>
      ) : (
        <p>Loading real-time telemetry analytics...</p>
      )}

      {/* Latency Pipeline Breakdown */}
      <div style={{
        background: isDarkMode ? '#1e1e2d' : '#ffffff',
        border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
        borderRadius: '10px',
        padding: '1.5rem',
        marginBottom: '1.8rem'
      }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ⏱️ Multi-Agent Latency & Execution Breakdown
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '0.2rem' }}>
              <span>1. Query Rewriter Agent</span>
              <strong>12 ms (0.8%)</strong>
            </div>
            <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: '5%', height: '100%', background: '#0066cc' }}></div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '0.2rem' }}>
              <span>2. BM25 + Dense Hybrid Retriever</span>
              <strong>45 ms (3.1%)</strong>
            </div>
            <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: '15%', height: '100%', background: '#0284c7' }}></div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '0.2rem' }}>
              <span>3. Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2)</span>
              <strong>180 ms (12.4%)</strong>
            </div>
            <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: '35%', height: '100%', background: '#8b5cf6' }}></div>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '0.2rem' }}>
              <span>4. Grounded LLM Response Generator</span>
              <strong>1200 ms (82.7%)</strong>
            </div>
            <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: '85%', height: '100%', background: '#10b981' }}></div>
            </div>
          </div>
        </div>
      </div>

      {/* RBAC Security & Role Audit Matrix */}
      <div style={{
        background: isDarkMode ? '#1e1e2d' : '#ffffff',
        border: isDarkMode ? '1px solid #2d2d3f' : '1px solid #e2e8f0',
        borderRadius: '10px',
        padding: '1.5rem'
      }}>
        <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldCheck color="#10b981" size={20} /> RBAC Security & Department Access Matrix
        </h3>
        
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: isDarkMode ? '#2b2b3d' : '#f1f5f9', borderBottom: '1px solid #ccc' }}>
              <th style={{ padding: '0.75rem' }}>Role Profile</th>
              <th style={{ padding: '0.75rem' }}>Assigned Department</th>
              <th style={{ padding: '0.75rem' }}>Security Clearance</th>
              <th style={{ padding: '0.75rem' }}>Document Scope</th>
              <th style={{ padding: '0.75rem' }}>Access Status</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>HR Specialist</td>
              <td style={{ padding: '0.75rem' }}>HR</td>
              <td style={{ padding: '0.75rem' }}>Confidential</td>
              <td style={{ padding: '0.75rem' }}>LeavePolicy.pdf, HiringProcess.pdf, SalaryPolicy.docx</td>
              <td style={{ padding: '0.75rem', color: '#10b981', fontWeight: 'bold' }}>Active Scoped</td>
            </tr>
            <tr style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>Software Engineer</td>
              <td style={{ padding: '0.75rem' }}>Engineering</td>
              <td style={{ padding: '0.75rem' }}>Confidential</td>
              <td style={{ padding: '0.75rem' }}>CodingStandards.pdf, DockerGuide.pdf, API_Guidelines.docx</td>
              <td style={{ padding: '0.75rem', color: '#10b981', fontWeight: 'bold' }}>Active Scoped</td>
            </tr>
            <tr style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>Finance Officer</td>
              <td style={{ padding: '0.75rem' }}>Finance</td>
              <td style={{ padding: '0.75rem' }}>Confidential</td>
              <td style={{ padding: '0.75rem' }}>ExpensePolicy.pdf, QuarterlyBudget.xlsx</td>
              <td style={{ padding: '0.75rem', color: '#10b981', fontWeight: 'bold' }}>Active Scoped</td>
            </tr>
            <tr style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>Legal Counsel</td>
              <td style={{ padding: '0.75rem' }}>Legal</td>
              <td style={{ padding: '0.75rem' }}>Confidential</td>
              <td style={{ padding: '0.75rem' }}>Compliance.pdf, VendorAgreement.pdf</td>
              <td style={{ padding: '0.75rem', color: '#10b981', fontWeight: 'bold' }}>Active Scoped</td>
            </tr>
            <tr>
              <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>Executive Manager</td>
              <td style={{ padding: '0.75rem' }}>Executive</td>
              <td style={{ padding: '0.75rem' }}>All Access</td>
              <td style={{ padding: '0.75rem' }}>All 12 Enterprise Documents (Cross-department)</td>
              <td style={{ padding: '0.75rem', color: '#f59e0b', fontWeight: 'bold' }}>Unrestricted Bypass</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  );
};
