/**
 * Helper to construct full API endpoints dynamically for development and cloud deployments (Vercel / Railway / Render).
 */
export const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL || '').replace(/\/$/, '');

export const getApiUrl = (path: string): string => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${cleanPath}`;
};
