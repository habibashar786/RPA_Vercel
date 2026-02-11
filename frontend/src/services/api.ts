import axios, { AxiosError } from 'axios';

// API Base URL - empty string means use relative paths (same domain on Vercel)
const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

console.log('API Service initialized with URL:', API_URL || '(relative paths)');

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
  withCredentials: false,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status} from ${response.config.url}`);
    return response;
  },
  (error: AxiosError) => {
    console.error(`[API] Error from ${error.config?.url}:`, error.message);
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
    return Promise.reject(error);
  }
);

// ============================================
// TYPE DEFINITIONS
// ============================================

export type SubscriptionTier = 'free' | 'non_permanent' | 'permanent';

export interface ProposalRequest {
  topic: string;
  key_points: string[];
  citation_style?: 'harvard' | 'apa' | 'mla' | 'chicago';
  target_word_count?: number;
  student_name?: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_stage: string | null;
  stages_completed: string[];
  message: string;
  created_at?: string;
  updated_at?: string;
  error: string | null;
}

export interface ProposalGenerationResponse {
  job_id: string;
  topic: string;
  status: string;
  message: string;
  progress: number;
  current_stage: string | null;
  estimated_time_minutes: number;
}

export interface ProposalSection {
  title: string;
  content: string;
  word_count?: number;
}

export interface ProposalResponse {
  request_id: string;
  topic: string;
  status: string;
  word_count: number;
  sections: ProposalSection[];
  generated_at: string;
  citation_style: string;
  validation?: {
    valid: boolean;
    issues: string[];
    corrections: string[];
  };
}

export interface WorkflowStatus {
  workflow_id: string;
  status: string;
  progress: number;
  current_stage: string | null;
  agents: AgentStatus[];
  completed_tasks: number;
  total_tasks: number;
}

export interface AgentStatus {
  name: string;
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress?: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  picture?: string;
  subscription_tier: SubscriptionTier;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user: UserProfile;
}

export interface SubscriptionTierInfo {
  id: SubscriptionTier;
  name: string;
  price: number;
  features: string[];
  limitations: string[];
}

// ============================================
// API FUNCTIONS
// ============================================

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getSystemStatus = async () => {
  const response = await api.get('/api/system/status');
  return response.data;
};

// ============================================
// PROPOSAL API
// ============================================

export const proposalApi = {
  generate: async (request: ProposalRequest): Promise<ProposalGenerationResponse> => {
    console.log('[proposalApi] Generating proposal:', request.topic);
    const response = await api.post('/api/proposals/generate', request);
    return response.data;
  },

  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    console.log(`[proposalApi] Polling job: ${jobId.substring(0, 8)}...`);
    try {
      const response = await fetch(`${API_URL}/api/proposals/jobs/${jobId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      console.log(`[proposalApi] Status: ${data.status}, ${data.progress}%`);
      return data;
    } catch (error: any) {
      console.error(`[proposalApi] Poll error:`, error.message);
      throw error;
    }
  },

  getJobResult: async (jobId: string) => {
    const response = await api.get(`/api/proposals/jobs/${jobId}/result`);
    return response.data;
  },

  listJobs: async (limit: number = 20) => {
    const response = await api.get(`/api/proposals/jobs?limit=${limit}`);
    return response.data;
  },

  getPreview: async (requestId: string, subscriptionTier: SubscriptionTier = 'permanent') => {
    const response = await api.get(`/api/proposals/${requestId}/preview?subscription_tier=${subscriptionTier}`);
    return response.data;
  },

  export: async (requestId: string, format: 'pdf' | 'docx' | 'markdown', subscriptionTier: SubscriptionTier = 'permanent'): Promise<Blob> => {
    const response = await api.get(`/api/proposals/${requestId}/export/${format}?subscription_tier=${subscriptionTier}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  download: async (requestId: string, format: 'pdf' | 'docx' | 'markdown', subscriptionTier: SubscriptionTier = 'permanent'): Promise<void> => {
    const blob = await proposalApi.export(requestId, format, subscriptionTier);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const extensions = { pdf: 'pdf', docx: 'docx', markdown: 'md' };
    link.download = `${requestId.slice(0, 8)}_proposal.${extensions[format]}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  list: async (page: number = 1, limit: number = 10) => {
    const response = await api.get(`/api/proposals?page=${page}&limit=${limit}`);
    return response.data;
  },
};

// ============================================
// AUTH API
// ============================================

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const response = await api.post('/api/auth/login', { email, password });
    if (typeof window !== 'undefined' && response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    return response.data;
  },

  loginWithGoogle: async (credential: string): Promise<LoginResponse> => {
    const response = await api.post('/api/auth/google', { credential });
    if (typeof window !== 'undefined' && response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    return response.data;
  },

  register: async (email: string, password: string, name: string): Promise<LoginResponse> => {
    const response = await api.post('/api/auth/signup', { email, password, name });
    return response.data;
  },

  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  verifyToken: async () => {
    try {
      const response = await api.get('/api/auth/verify');
      return response.data;
    } catch {
      return { valid: false };
    }
  },

  logout: async (): Promise<void> => {
    try { await api.post('/api/auth/logout'); } catch {}
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
    }
  },
};

// ============================================
// SUBSCRIPTION API
// ============================================

export const subscriptionApi = {
  getTiers: async (): Promise<{ tiers: SubscriptionTierInfo[] }> => {
    const response = await api.get('/api/subscription/tiers');
    return response.data;
  },

  upgrade: async (tier: SubscriptionTier) => {
    const response = await api.post(`/api/subscription/upgrade?tier=${tier}`);
    return response.data;
  },
};

// ============================================
// AGENTS API
// ============================================

export const agentsApi = {
  list: async () => {
    const response = await api.get('/agents');
    return response.data;
  },
};

// ============================================
// HEALTH API
// ============================================

export const healthApi = {
  check: checkHealth,
  listAgents: agentsApi.list,
};

// ============================================
// TEST API
// ============================================

export const testApi = {
  testLLM: async () => {
    const response = await api.get('/api/test/llm');
    return response.data;
  },
};

export default api;
