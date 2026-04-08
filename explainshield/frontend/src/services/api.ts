import axios from 'axios';
import { AuditResult, AuditStats } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

let authToken: string | null = null;
let tokenPromise: Promise<string> | null = null;

const getToken = async (): Promise<string> => {
  if (authToken) return authToken;
  if (tokenPromise) return tokenPromise;
  
  tokenPromise = (async () => {
    const response = await axios.get('http://localhost:8000/api/token');
    authToken = response.data.token;
    return authToken;
  })();
  
  return tokenPromise;
};

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const setAuthToken = (token: string) => {
  authToken = token;
};

api.interceptors.request.use(async (config) => {
  const token = await getToken();
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const claimsService = {
  listClaims: async (limit = 50): Promise<any> => {
    const response = await api.get('/claims', { params: { limit } });
    return response.data;
  },
  
  getClaim: async (claimId: string): Promise<any> => {
    const response = await api.get(`/claims/${claimId}`);
    return response.data;
  },
  
  seedClaims: async (): Promise<any> => {
    const response = await api.post('/claims/seed');
    return response.data;
  },
  
  auditClaim: async (claimId: string): Promise<AuditResult> => {
    const response = await api.post(`/claims/audit/${claimId}`);
    return response.data;
  },
};

export const auditService = {
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
