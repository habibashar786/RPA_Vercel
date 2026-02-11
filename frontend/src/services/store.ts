import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import {
  ProposalRequest,
  ProposalResponse,
  WorkflowStatus,
  UserProfile,
  SubscriptionTier,
} from '@/services/api';

// ============================================
// PROPOSAL STORE
// ============================================

interface ProposalState {
  currentProposal: any | null;
  workflowStatus: WorkflowStatus | null;
  proposals: ProposalResponse[];
  formData: Partial<ProposalRequest>;
  isGenerating: boolean;
  error: string | null;
  
  setCurrentProposal: (proposal: any | null) => void;
  setWorkflowStatus: (status: WorkflowStatus | null) => void;
  setProposals: (proposals: ProposalResponse[]) => void;
  addProposal: (proposal: ProposalResponse) => void;
  updateFormData: (data: Partial<ProposalRequest>) => void;
  resetFormData: () => void;
  setIsGenerating: (isGenerating: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialFormData: Partial<ProposalRequest> = {
  topic: '',
  key_points: [],
  citation_style: 'harvard',
  target_word_count: 15000,
};

export const useProposalStore = create<ProposalState>((set) => ({
  currentProposal: null,
  workflowStatus: null,
  proposals: [],
  formData: initialFormData,
  isGenerating: false,
  error: null,

  setCurrentProposal: (proposal) => set({ currentProposal: proposal }),
  setWorkflowStatus: (status) => set({ workflowStatus: status }),
  setProposals: (proposals) => set({ proposals }),
  addProposal: (proposal) => set((state) => ({ proposals: [proposal, ...state.proposals] })),
  updateFormData: (data) => set((state) => ({ formData: { ...state.formData, ...data } })),
  resetFormData: () => set({ formData: initialFormData }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),
  setError: (error) => set({ error }),
  reset: () => set({
    currentProposal: null,
    workflowStatus: null,
    formData: initialFormData,
    isGenerating: false,
    error: null,
  }),
}));

// ============================================
// AUTH STORE (with Subscription Tier)
// ============================================

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  subscriptionTier: SubscriptionTier;
  
  setUser: (user: UserProfile | null) => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  setIsLoading: (isLoading: boolean) => void;
  setSubscriptionTier: (tier: SubscriptionTier) => void;
  login: (user: UserProfile) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      subscriptionTier: 'permanent' as SubscriptionTier,

      setUser: (user) => set({
        user,
        isAuthenticated: !!user,
        subscriptionTier: user?.subscription_tier || 'permanent',
      }),
      
      setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
      setIsLoading: (isLoading) => set({ isLoading }),
      setSubscriptionTier: (subscriptionTier) => set({ subscriptionTier }),
      
      login: (user) => set({
        user,
        isAuthenticated: true,
        isLoading: false,
        subscriptionTier: user.subscription_tier || 'permanent',
      }),
      
      logout: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('refresh_token');
        }
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          subscriptionTier: 'free',
        });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => {
        if (typeof window !== 'undefined') return localStorage;
        return { getItem: () => null, setItem: () => {}, removeItem: () => {} };
      }),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        subscriptionTier: state.subscriptionTier,
      }),
    }
  )
);

// ============================================
// UI STORE
// ============================================

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

interface UIState {
  theme: 'dark' | 'light';
  sidebarOpen: boolean;
  activeModal: string | null;
  notifications: Notification[];
  
  setTheme: (theme: 'dark' | 'light') => void;
  toggleTheme: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'dark',
  sidebarOpen: true,
  activeModal: null,
  notifications: [],

  setTheme: (theme) => set({ theme }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  openModal: (activeModal) => set({ activeModal }),
  closeModal: () => set({ activeModal: null }),
  addNotification: (notification) => set((state) => ({
    notifications: [...state.notifications, { ...notification, id: Date.now().toString() }],
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter((n) => n.id !== id),
  })),
  clearNotifications: () => set({ notifications: [] }),
}));

// ============================================
// AUTH CHECK HOOK
// ============================================

export const useAuthCheck = () => {
  const { setIsLoading, setIsAuthenticated, setUser } = useAuthStore();
  
  const checkAuth = async () => {
    setIsLoading(true);
    try {
      if (typeof window === 'undefined') {
        setIsLoading(false);
        return;
      }
      
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setIsAuthenticated(false);
        setUser(null);
        setIsLoading(false);
        return;
      }
      
      const { authApi } = await import('@/services/api');
      const result = await authApi.verifyToken();
      
      if (result.valid) {
        const profile = await authApi.getProfile();
        setUser(profile);
        setIsAuthenticated(true);
      } else {
        setIsAuthenticated(false);
        setUser(null);
        localStorage.removeItem('auth_token');
      }
    } catch {
      setIsAuthenticated(false);
      setUser(null);
      if (typeof window !== 'undefined') localStorage.removeItem('auth_token');
    } finally {
      setIsLoading(false);
    }
  };
  
  return { checkAuth };
};
