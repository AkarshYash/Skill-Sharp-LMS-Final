import api from '@/lib/api';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'faculty' | 'student';
  avatar?: string;
  student_type?: 'school' | 'college';
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  login: (email: string, password: string, twoFaCode?: string) => Promise<any>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isLoading: false,

      login: async (email, password, twoFaCode) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post('/auth/login', { email, password, twoFaCode });
          if (data.requires2FA) return { requires2FA: true };
          localStorage.setItem('accessToken', data.accessToken);
          localStorage.setItem('refreshToken', data.refreshToken);
          set({ user: data.user, accessToken: data.accessToken, isLoading: false });
          return data;
        } catch (err: any) {
          set({ isLoading: false });
          throw err;
        }
      },

      register: async (formData) => {
        set({ isLoading: true });
        try {
          await api.post('/auth/register', formData);
          set({ isLoading: false });
        } catch (err) {
          set({ isLoading: false });
          throw err;
        }
      },

      logout: async () => {
        try { await api.post('/auth/logout'); } catch {}
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        set({ user: null, accessToken: null });
      },

      updateUser: (data) => set((state) => ({ user: state.user ? { ...state.user, ...data } : null }))
    }),
    { name: 'auth-store', partialize: (state) => ({ user: state.user, accessToken: state.accessToken }) }
  )
);
