/**
 * Context React pour l'authentification.
 *
 * Fournit l'état d'authentification global à toute l'application.
 * Gère automatiquement les changements d'état auth (login/logout).
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import type { User } from '../types';
import * as authService from '../services/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Récupérer l'utilisateur au chargement initial
    authService
      .getCurrentUser()
      .then((user) => {
        setUser(user);
      })
      .catch((error) => {
        console.error('Error loading user:', error);
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });

    // Écouter les changements d'état auth
    const {
      data: { subscription },
    } = authService.onAuthStateChange((event, session) => {
      console.log('Auth state changed:', event);
      setUser((session?.user as User) || null);
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const { user } = await authService.login(email, password);
      setUser(user as User);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      setUser(null);
    } catch (error) {
      throw error;
    }
  };

  const isAdmin = authService.isAdmin(user);

  const value: AuthContextType = {
    user,
    loading,
    isAdmin,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook personnalisé pour utiliser le context d'authentification.
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};
