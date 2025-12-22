/**
 * Types TypeScript pour l'application Léonie Frontend.
 *
 * Définitions des interfaces pour :
 * - Utilisateurs (Supabase Auth)
 * - Dossiers clients
 * - Pièces de dossier
 * - Courtiers (admin)
 */

export interface User {
  id: string;
  email: string;
  user_metadata?: {
    nom?: string;
    prenom?: string;
    role?: string;
  };
}

export interface Dossier {
  id: string;
  client_nom: string;
  client_prenom: string;
  client_email: string;
  type_pret: 'immobilier' | 'professionnel';
  statut: 'en_cours' | 'complet' | 'archive';
  progression: number;
  pieces_recues: number;
  pieces_manquantes: number;
  pieces_non_conformes: number;
  created_at: string;
  updated_at: string;
}

export interface DossierDetail {
  dossier: {
    id: string;
    client: {
      nom: string;
      prenom: string;
      email: string;
      emails_secondaires?: string[];
      telephone?: string;
    };
    type_pret: string;
    statut: string;
    montant_pret?: number;
    duree_pret?: number;
    created_at: string;
    updated_at: string;
    dossier_drive_url: string;
    rapport_url: string | null;
  };
  pieces: Piece[];
  progression: {
    total: number;
    recues: number;
    manquantes: number;
    non_conformes: number;
    pourcentage: number;
  };
}

export interface Piece {
  id: string;
  nom: string;
  categorie: string;
  statut: 'manquante' | 'recue' | 'non_conforme' | 'non_reconnu';
  obligatoire: boolean;
  date_reception: string | null;
  commentaire: string | null;
  fichier_url: string | null;
  fichier_drive_id: string | null;
}

export interface Courtier {
  id: string;
  email: string;
  nom: string;
  prenom: string;
  dossier_drive_id: string;
  actif: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface CreateCourtierRequest {
  email: string;
  nom: string;
  prenom: string;
  actif?: boolean;
}

export interface UpdateCourtierRequest {
  email?: string;
  nom?: string;
  prenom?: string;
  actif?: boolean;
}

export interface ApiError {
  detail: string;
  status?: number;
}

export type StatutPiece = 'manquante' | 'recue' | 'non_conforme' | 'non_reconnu';
export type StatutDossier = 'en_cours' | 'complet' | 'archive';
export type TypePret = 'immobilier' | 'professionnel';
