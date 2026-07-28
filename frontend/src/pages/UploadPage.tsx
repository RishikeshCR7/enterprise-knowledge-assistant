import React from 'react';

export const UploadPage: React.FC = () => {
  return (
    <div style={{ flex: 1, padding: '1rem' }}>
      <h3>Upload Page Placeholder</h3>
      <p>Document lifecycle ingestion endpoint: POST /api/v1/documents/upload</p>
      <input type="file" disabled />
      <button disabled style={{ marginLeft: '0.5rem' }}>Upload (Dev A Integration)</button>
    </div>
  );
};
