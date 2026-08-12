import React, { useEffect, useState } from 'react';
import { getApiUrl } from '../config/api';

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
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    const statsUrl = getApiUrl('/api/v1/admin/stats');
    fetch(statsUrl)
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.error('Failed to fetch admin stats:', err));
  }, []);

  return (
    <div style={{ flex: 1, padding: '1.5rem', fontFamily: 'Inter, sans-serif' }}>
      <h2>📊 Enterprise Admin & Observability Dashboard</h2>
      <p style={{ color: '#666' }}>Real-time telemetry, RBAC policy audit, and system satisfaction analytics.</p>

      {stats ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
          <div style={{ background: '#e3f2fd', border: '1px solid #90caf9', borderRadius: '8px', padding: '1rem' }}>
            <h4 style={{ margin: 0, color: '#1565c0' }}>Total Queries Processed</h4>
            <p style={{ fontSize: '1.8rem', fontWeight: 'bold', margin: '0.5rem 0 0 0' }}>{stats.total_questions_processed}</p>
          </div>

          <div style={{ background: '#e8f5e9', border: '1px solid #a5d6a7', borderRadius: '8px', padding: '1rem' }}>
            <h4 style={{ margin: 0, color: '#2e7d32' }}>User Satisfaction Rate</h4>
            <p style={{ fontSize: '1.8rem', fontWeight: 'bold', margin: '0.5rem 0 0 0' }}>{stats.satisfaction_rate}%</p>
          </div>

          <div style={{ background: '#fff3e0', border: '1px solid #ffe0b2', borderRadius: '8px', padding: '1rem' }}>
            <h4 style={{ margin: 0, color: '#e65100' }}>Avg Pipeline Latency</h4>
            <p style={{ fontSize: '1.8rem', fontWeight: 'bold', margin: '0.5rem 0 0 0' }}>{stats.avg_response_latency_ms} ms</p>
          </div>

          <div style={{ background: '#f3e5f5', border: '1px solid #ce93d8', borderRadius: '8px', padding: '1rem' }}>
            <h4 style={{ margin: 0, color: '#6a1b9a' }}>Vector DB Index Health</h4>
            <p style={{ fontSize: '1rem', fontWeight: 'bold', margin: '0.5rem 0 0 0' }}>{stats.vector_search_health}</p>
          </div>
        </div>
      ) : (
        <p>Loading telemetry stats...</p>
      )}

      <div style={{ marginTop: '2rem', background: '#fafafa', border: '1px solid #e0e0e0', borderRadius: '8px', padding: '1.2rem' }}>
        <h3>🔒 Configured RBAC Role Clearances</h3>
        <ul>
          <li><strong>HR Specialist:</strong> HR Policies, Hiring Process, Remuneration</li>
          <li><strong>Software Engineer:</strong> Coding Standards, API Guidelines, Architecture Guides</li>
          <li><strong>Finance Officer:</strong> Expense Policies, Quarterly Budget Reports</li>
          <li><strong>Legal Counsel:</strong> Vendor Agreements, NDA Contracts, Compliance Policy</li>
          <li><strong>Sales Executive:</strong> Pricing Strategy, Discount Matrices</li>
          <li><strong>Executive Manager:</strong> Cross-department unrestricted clearance</li>
        </ul>
      </div>
    </div>
  );
};
