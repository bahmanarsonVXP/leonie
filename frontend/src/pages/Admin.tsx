/**
 * Page Administration.
 *
 * TODO Session 11:
 * - Liste des courtiers
 * - Créer/Modifier/Désactiver courtiers
 * - Statistiques globales
 */

import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export const Admin: React.FC = () => {
  const { isAdmin } = useAuth();

  if (!isAdmin) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-red-700 mb-2">Accès refusé</h2>
        <p className="text-red-600">Cette page est réservée aux administrateurs.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-content-primary mb-6">Administration</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-content-primary mb-4">
          Gestion des courtiers
        </h2>

        <div className="bg-cif-primary/5 border border-cif-primary/20 rounded-lg p-4">
          <p className="text-sm text-content-primary">
            <strong>📋 Session 11 :</strong> Implémentation de l'interface admin complète pour la
            gestion des courtiers (CRUD).
          </p>
        </div>
      </div>
    </div>
  );
};
