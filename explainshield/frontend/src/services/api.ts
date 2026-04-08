import axios from 'axios';
import { AuditResult, AuditStats } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

// In-memory token storage (per user request)
let authToken: string | null = null;

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Set hardcoded token for demo (In real app, this is set after login)
export const setAuthToken = (token: string) => {
  authToken = token;
};

api.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

export const auditService = {
  auditClaim: async (features: any, decision: string, confidence: number): Promise<AuditResult> => {
    const response = await api.post('/claims/audit', {
      input_features: features,
      model_decision: decision,
      model_confidence: confidence,
    });
    return response.data;
  },

  getAuditLogs: async (limit = 10): Promise<any[]> => {
    const response = await api.get('/audit/logs', { params: { limit } });
    return response.data;
  },

  getStats: async (): Promise<AuditStats> => {
    const response = await api.get('/audit/stats');
    return response.data;
  },

  getComplianceReport: async (): Promise<any> => {
    const response = await api.get('/audit/compliance-report');
    return response.data;
  },

  getCrdiReport: async (): Promise<any> => {
    const response = await api.get('/audit/crdi-report');
    return response.data;
  },

  uploadModel: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/onboarding/upload-model', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};
