/**
 * Service d'authentification Supabase pour Léonie.
 *
 * Gère:
 * - Login/Logout
 * - Récupération utilisateur actuel
 * - Token JWT
 * - Auth state changes
 */

import { createClient, AuthChangeEvent, Session } from '@supabase/supabase-js';
import type { User } from '../types';

// Variables d'environnement injectées par Vite au moment du build
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables. Check .env.local file.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

/**
 * Connexion avec email et mot de passe.
 */
export const login = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw new Error(error.message);
  }

  return data;
};

/**
 * Inscription (création compte).
 */
export const signup = async (email: string, password: string, metadata?: { nom?: string; prenom?: string }) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadata,
    },
  });

  if (error) {
    throw new Error(error.message);
  }

  return data;
};

/**
 * Déconnexion.
 */
export const logout = async () => {
  const { error } = await supabase.auth.signOut();
  if (error) {
    throw new Error(error.message);
  }
};

/**
 * Récupère l'utilisateur actuellement connecté.
 */
export const getCurrentUser = async (): Promise<User | null> => {
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error) {
    console.error('Error getting current user:', error);
    return null;
  }

  return user as User | null;
};

/**
 * Récupère le token JWT de la session actuelle.
 */
export const getToken = async (): Promise<string | null> => {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  return session?.access_token || null;
};

/**
 * Écoute les changements d'état d'authentification.
 */
export const onAuthStateChange = (
  callback: (event: AuthChangeEvent, session: Session | null) => void
) => {
  return supabase.auth.onAuthStateChange(callback);
};

/**
 * Vérifie si l'utilisateur est admin.
 */
export const isAdmin = (user: User | null): boolean => {
  if (!user) return false;

  // Vérifier dans les metadata
  return user.user_metadata?.role === 'admin';
};
