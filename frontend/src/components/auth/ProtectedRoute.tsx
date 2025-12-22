/**
 * Composant de route protégée.
 *
 * Vérifie que l'utilisateur est authentifié avant d'afficher le contenu.
 * Redirige vers /login si non authentifié.
 */

import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requireAdmin?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requireAdmin = false }) => {
  const { user, loading, isAdmin } = useAuth();

  // Afficher loader pendant vérification auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-bg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cif-primary mx-auto"></div>
          <p className="mt-4 text-content-secondary">Chargement...</p>
        </div>
      </div>
    );
  }

  // Rediriger vers login si non authentifié
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Vérifier les permissions admin si requises
  if (requireAdmin && !isAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-bg">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-content-primary mb-4">Accès Refusé</h1>
          <p className="text-content-secondary mb-6">
            Cette page est réservée aux administrateurs.
          </p>
          <a
            href="/dashboard"
            className="text-cif-primary hover:text-cif-primary-dark underline"
          >
            Retour au tableau de bord
          </a>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
