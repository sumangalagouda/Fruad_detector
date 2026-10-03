import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle unauthorized responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
};

export const caseApi = {
  list: (status) => api.get('/cases', { params: { status } }),
  get: (caseId) => api.get(`/cases/${caseId}`),
  create: (data) => api.post('/cases', data),
  update: (caseId, data) => api.put(`/cases/${caseId}`, data),
  delete: (caseId) => api.delete(`/cases/${caseId}`),
  getAccounts: (caseId) => api.get(`/cases/${caseId}/accounts`),
  addAccount: (caseId, data) => api.post(`/cases/${caseId}/accounts`, data),
};

export const statementApi = {
  list: (caseId) => api.get(`/cases/${caseId}/statements`),
  get: (statementId) => api.get(`/statements/${statementId}`),
  upload: (caseId, formData) =>
    api.post(`/cases/${caseId}/statements/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
};

export const transactionApi = {
  list: (caseId, params) => api.get(`/cases/${caseId}/transactions`, { params }),
  search: (caseId, queryParams) => api.post(`/cases/${caseId}/transactions/search`, queryParams),
  get: (transactionId) => api.get(`/transactions/${transactionId}`),
};

export const detectorApi = {
  analyze: (caseId, customConfigs = {}) => api.post(`/cases/${caseId}/analyze`, customConfigs),
  getDetectors: (caseId) => api.get(`/cases/${caseId}/detectors`),
  getSuspicious: (caseId, detector) => api.get(`/cases/${caseId}/suspicious-transactions`, { params: { detector } }),
};

export const graphApi = {
  getFundFlow: (caseId, refresh = false) => api.get(`/cases/${caseId}/fund-flow`, { params: { refresh } }),
  getCircularFlows: (caseId, refresh = false) => api.get(`/cases/${caseId}/circular-flows`, { params: { refresh } }),
  getLayering: (caseId, refresh = false) => api.get(`/cases/${caseId}/layering`, { params: { refresh } }),
  getMoneyTrail: (caseId, transactionId = null, refresh = false) =>
    api.get(`/cases/${caseId}/money-trail`, { params: { transaction_id: transactionId, refresh } }),
};

export const aiApi = {
  investigate: (caseId, question, investigationId = null) =>
    api.post(`/cases/${caseId}/investigate`, { question, investigation_id: investigationId }),
  getInvestigations: (caseId) => api.get(`/cases/${caseId}/investigations`),
  getInvestigation: (investigationId) => api.get(`/investigations/${investigationId}`),
  submitFeedback: (investigationId, data) => api.post(`/investigations/${investigationId}/feedback`, data),
};

export const reportApi = {
  generate: (caseId, title = null) => api.post(`/cases/${caseId}/reports`, { title }),
  list: (caseId) => api.get(`/cases/${caseId}/reports`),
  get: (reportId) => api.get(`/reports/${reportId}`),
};

export const auditApi = {
  getCaseLogs: (caseId) => api.get(`/cases/${caseId}/audit-logs`),
  getAllLogs: () => api.get('/audit-logs'),
};

export default api;
