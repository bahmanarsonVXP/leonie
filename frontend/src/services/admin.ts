/**
 * Service API pour l'administration (admin seulement).
 *
 * Endpoints:
 * - GET /api/admin/courtiers - Liste courtiers
 * - POST /api/admin/courtiers - Créer courtier
 * - GET /api/admin/courtiers/:id - Détail courtier
 * - PATCH /api/admin/courtiers/:id - Mise à jour courtier
 */

import { apiClient } from './api';
import type { Courtier, CreateCourtierRequest, UpdateCourtierRequest } from '../types';

/**
 * Liste tous les courtiers (admin seulement).
 */
export const listCourtiers = async (): Promise<Courtier[]> => {
  const response = await apiClient.get<Courtier[]>('/admin/courtiers');
  return response.data;
};

/**
 * Crée un nouveau courtier (admin seulement).
 */
export const createCourtier = async (data: CreateCourtierRequest): Promise<Courtier> => {
  const response = await apiClient.post<Courtier>('/admin/courtiers', data);
  return response.data;
};

/**
 * Récupère les détails d'un courtier (admin seulement).
 */
export const getCourtier = async (courtierId: string): Promise<Courtier> => {
  const response = await apiClient.get<Courtier>(`/admin/courtiers/${courtierId}`);
  return response.data;
};

/**
 * Met à jour un courtier (admin seulement).
 */
export const updateCourtier = async (
  courtierId: string,
  updates: UpdateCourtierRequest
): Promise<Courtier> => {
  const response = await apiClient.patch<Courtier>(`/admin/courtiers/${courtierId}`, updates);
  return response.data;
};

/**
 * Désactive/Active un courtier.
 */
export const toggleCourtierActif = async (courtierId: string, actif: boolean): Promise<Courtier> => {
  return updateCourtier(courtierId, { actif });
};
