/**
 * Client API Axios pour l'API backend Léonie.
 *
 * Configure:
 * - Base URL
 * - Headers
 * - Intercepteurs pour JWT automatique
 * - Gestion erreurs globale
 */

import axios, { AxiosError } from 'axios';
import { getToken } from './auth';
import type { ApiError } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Instance axios configurée pour l'API Léonie.
 */
export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 secondes
});

/**
 * Intercepteur de requêtes : Ajoute automatiquement le JWT dans les headers.
 */
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const token = await getToken();

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting token for request:', error);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Intercepteur de réponses : Gestion globale des erreurs.
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // 401 Unauthorized -> Redirection vers login
    if (error.response?.status === 401) {
      console.warn('Unauthorized request, redirecting to login...');
      window.location.href = '/login';
    }

    // 403 Forbidden
    if (error.response?.status === 403) {
      console.error('Forbidden:', error.response.data?.detail);
    }

    // 500 Internal Server Error
    if (error.response?.status === 500) {
      console.error('Server error:', error.response.data?.detail);
    }

    return Promise.reject(error);
  }
);

/**
 * Helper pour extraire le message d'erreur d'une réponse API.
 */
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as ApiError | undefined;
    return apiError?.detail || error.message || 'Une erreur est survenue';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Une erreur inconnue est survenue';
};
