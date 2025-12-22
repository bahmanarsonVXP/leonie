/**
 * Service API pour la gestion des dossiers clients.
 *
 * Endpoints:
 * - GET /api/dossiers - Liste dossiers
 * - GET /api/dossiers/:id - Détail dossier
 * - PATCH /api/dossiers/:id - Mise à jour
 * - POST /api/dossiers/:id/validate - Marquer complet
 */

import { apiClient } from './api';
import type { Dossier, DossierDetail, StatutDossier } from '../types';

/**
 * Liste tous les dossiers du courtier authentifié.
 */
export const listDossiers = async (statut?: StatutDossier): Promise<Dossier[]> => {
  const params = statut ? { statut } : {};
  const response = await apiClient.get<Dossier[]>('/dossiers', { params });
  return response.data;
};

/**
 * Récupère le détail complet d'un dossier.
 */
export const getDossierDetail = async (dossierId: string): Promise<DossierDetail> => {
  const response = await apiClient.get<DossierDetail>(`/dossiers/${dossierId}`);
  return response.data;
};

/**
 * Met à jour un dossier (statut, informations client, etc.).
 */
export const updateDossier = async (
  dossierId: string,
  updates: {
    statut?: StatutDossier;
    client_nom?: string;
    client_prenom?: string;
    client_email?: string;
    client_telephone?: string;
    type_pret?: string;
    montant_pret?: number;
    duree_pret?: number;
  }
): Promise<DossierDetail> => {
  const response = await apiClient.patch<DossierDetail>(`/dossiers/${dossierId}`, updates);
  return response.data;
};

/**
 * Marque un dossier comme complet (toutes pièces obligatoires reçues).
 */
export const marquerDossierComplet = async (dossierId: string): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(`/dossiers/${dossierId}/validate`);
  return response.data;
};

/**
 * Télécharge le rapport Word du dossier.
 */
export const telechargerRapport = async (dossierId: string): Promise<Blob> => {
  const response = await apiClient.get(`/dossiers/${dossierId}/rapport`, {
    responseType: 'blob',
  });
  return response.data;
};
