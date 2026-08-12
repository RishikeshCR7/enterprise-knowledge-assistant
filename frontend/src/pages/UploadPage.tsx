import React, { useState, useEffect } from 'react';
import { Upload, FileText, CheckCircle, Trash2, Shield, RefreshCw } from 'lucide-react';

interface DocItem {
  doc_id: string;
  title: string;
  department: string;
  security_level: string;
  allowed_roles: string[];
  owner: string;
  file_type: string;
  chunk_count: number;
}

export const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('HR');
  const [securityLevel, setSecurityLevel] = useState('Internal');
  const [allowedRoles, setAllowedRoles] = useState<string[]>(['HR', 'Executive']);
  const [owner, setOwner] = useState('HR Admin');
  const [tags, setTags] = useState('policy, guidelines');

  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<string>('');
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [filterDept, setFilterDept] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/v1/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to fetch document list:', err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleRoleToggle = (role: string) => {
    if (allowedRoles.includes(role)) {
      setAllowedRoles(allowedRoles.filter(r => r !== role));
    } else {
      setAllowedRoles([...allowedRoles, role]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setIsUploading(true);
    setUploadSuccess(null);
    setUploadStep('1/4 Parsing File & OCR...');

    const formData = new FormData();
    formData.append('file', file);
    if (title.trim()) formData.append('title', title.trim());
    formData.append('department', department);
    formData.append('security_level', securityLevel);
    formData.append('allowed_roles', allowedRoles.join(','));
    formData.append('owner', owner);

    try {
      setTimeout(() => setUploadStep('2/4 Chunking Text (Recursive Splitter)...'), 800);
      setTimeout(() => setUploadStep('3/4 Generating Vector Embeddings (384d)...'), 1600);
      setTimeout(() => setUploadStep('4/4 Indexing into ChromaDB Store...'), 2400);

      const res = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      const result = await res.json();
      setUploadSuccess(`Successfully ingested "${result.metadata.title}" into ChromaDB (${result.chunk_count} chunks created).`);
      setFile(null);
      setTitle('');
      fetchDocuments();
    } catch (err: any) {
      alert(`Error uploading document: ${err.message}`);
    } finally {
      setIsUploading(false);
      setUploadStep('');
    }
  };

  const handleDelete = async (docId: string) => {
    if (!window.confirm(`Are you sure you want to delete document ${docId}?`)) return;
    try {
      const res = await fetch(`/api/v1/documents/${docId}`, { method: 'DELETE' });
      if (res.ok) {
        fetchDocuments();
      }
    } catch (err) {
      console.error('Delete document failed:', err);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesDept = filterDept === 'ALL' || doc.department === filterDept;
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) || doc.owner.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesDept && matchesSearch;
  });

  return (
    <div style={{ flex: 1, padding: '1.5rem', background: '#f8f9fa', overflowY: 'auto' }}>
      <h2 style={{ marginBottom: '0.3rem', color: '#1a1a1a' }}>📁 Enterprise Document Management Console</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        Upload, metadata tag, parse, chunk, embed, and manage enterprise documents in ChromaDB vector store.
      </p>

      {/* Grid: Upload Form + Document List */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr', gap: '1.5rem' }}>
        
        {/* Left Column: Upload & Metadata Tagging Form */}
        <div style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
          <h3 style={{ marginBottom: '1rem', borderBottom: '2px solid #0066cc', paddingBottom: '0.4rem', color: '#0066cc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Upload size={20} /> Upload New Enterprise Document
          </h3>

          <form onSubmit={handleUpload}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.3rem' }}>Document File (PDF, DOCX, XLSX, TXT):</label>
              <input
                type="file"
                accept=".pdf,.docx,.xlsx,.txt"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                required
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
              />
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.3rem' }}>Document Title (Optional):</label>
              <input
                type="text"
                placeholder="e.g. Q2 2026 Financial Performance Report"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.3rem' }}>Department:</label>
                <select value={department} onChange={(e) => setDepartment(e.target.value)} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}>
                  <option value="HR">HR</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Finance">Finance</option>
                  <option value="Legal">Legal</option>
                  <option value="Sales">Sales</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.3rem' }}>Security Clearance:</label>
                <select value={securityLevel} onChange={(e) => setSecurityLevel(e.target.value)} style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}>
                  <option value="Public">Public</option>
                  <option value="Internal">Internal</option>
                  <option value="Confidential">Confidential</option>
                  <option value="Restricted">Restricted</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.3rem' }}>Allowed RBAC Roles:</label>
              <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                {['HR', 'Engineering', 'Finance', 'Legal', 'Sales', 'Executive'].map((role) => (
                  <label key={role} style={{ fontSize: '0.82rem', background: allowedRoles.includes(role) ? '#e3f2fd' : '#f0f0f0', padding: '0.3rem 0.6rem', borderRadius: '4px', cursor: 'pointer', border: '1px solid #ccc' }}>
                    <input
                      type="checkbox"
                      checked={allowedRoles.includes(role)}
                      onChange={() => handleRoleToggle(role)}
                      style={{ marginRight: '0.3rem' }}
                    />
                    {role}
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.2rem' }}>
              <div>
                <label style={{ display: 'block', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.3rem' }}>Owner / Author:</label>
                <input
                  type="text"
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '0.3rem' }}>Tags (comma-separated):</label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #ccc', borderRadius: '4px' }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isUploading || !file}
              style={{
                width: '100%', padding: '0.75rem', background: isUploading ? '#ccc' : '#0066cc', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: isUploading ? 'not-allowed' : 'pointer'
              }}
            >
              {isUploading ? uploadStep : '🚀 Start Ingestion Pipeline'}
            </button>

            {uploadSuccess && (
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#e8f5e9', color: '#2e7d32', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} /> {uploadSuccess}
              </div>
            )}
          </form>
        </div>

        {/* Right Column: Indexed Documents Table */}
        <div style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ color: '#0066cc', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={20} /> Indexed Knowledge Base ({documents.length})
            </h3>
            <button onClick={fetchDocuments} style={{ padding: '0.4rem 0.8rem', background: '#f0f0f0', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem' }}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>

          {/* Filters */}
          <div style={{ display: 'flex', gap: '0.8rem', marginBottom: '1rem' }}>
            <input
              type="text"
              placeholder="Search documents by title..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ flex: 1, padding: '0.4rem 0.6rem', border: '1px solid #ccc', borderRadius: '4px', fontSize: '0.85rem' }}
            />

            <select value={filterDept} onChange={(e) => setFilterDept(e.target.value)} style={{ padding: '0.4rem', border: '1px solid #ccc', borderRadius: '4px', fontSize: '0.85rem' }}>
              <option value="ALL">All Departments</option>
              <option value="HR">HR</option>
              <option value="Engineering">Engineering</option>
              <option value="Finance">Finance</option>
              <option value="Legal">Legal</option>
              <option value="Sales">Sales</option>
            </select>
          </div>

          {/* Document Table */}
          <div style={{ overflowX: 'auto', maxHeight: '480px', overflowY: 'auto', border: '1px solid #eee', borderRadius: '6px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ background: '#f0f4f8', borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '0.6rem' }}>Document Title</th>
                  <th style={{ padding: '0.6rem' }}>Dept</th>
                  <th style={{ padding: '0.6rem' }}>Clearance</th>
                  <th style={{ padding: '0.6rem' }}>Chunks</th>
                  <th style={{ padding: '0.6rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: '1rem', textAlign: 'center', color: '#888' }}>
                      No documents found matching filter.
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => (
                    <tr key={doc.doc_id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '0.6rem', fontWeight: 'bold' }}>
                        📄 {doc.title}
                        <div style={{ fontSize: '0.72rem', color: '#888', fontWeight: 'normal' }}>ID: {doc.doc_id.slice(0, 12)}... | Owner: {doc.owner}</div>
                      </td>
                      <td style={{ padding: '0.6rem' }}>
                        <span style={{ background: '#e3f2fd', color: '#0066cc', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                          {doc.department}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem' }}>
                        <span style={{ background: doc.security_level === 'Confidential' ? '#fff3e0' : doc.security_level === 'Public' ? '#e8f5e9' : '#f5f5f5', color: doc.security_level === 'Confidential' ? '#e65100' : '#2e7d32', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                          <Shield size={10} style={{ marginRight: '2px' }} /> {doc.security_level}
                        </span>
                      </td>
                      <td style={{ padding: '0.6rem', textAlign: 'center', fontWeight: 'bold' }}>
                        {doc.chunk_count || 1}
                      </td>
                      <td style={{ padding: '0.6rem' }}>
                        <button
                          onClick={() => handleDelete(doc.doc_id)}
                          style={{ background: '#ffebee', color: '#c62828', border: 'none', padding: '0.3rem 0.5rem', borderRadius: '4px', cursor: 'pointer' }}
                          title="Delete Document"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
};

export default UploadPage;
