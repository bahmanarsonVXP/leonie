/**
 * Page Dashboard (Tableau de bord).
 *
 * TODO Session 9:
 * - Statistiques (nb dossiers, progression moyenne, etc.)
 * - Liste des dossiers récents
 * - Graphiques de suivi
 */

import React from 'react';

export const Dashboard: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-content-primary mb-6">Tableau de bord</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-content-primary mb-4">
          Bienvenue sur Léonie !
        </h2>
        <p className="text-content-secondary mb-4">
          Votre assistant IA pour la gestion de dossiers de prêt.
        </p>

        <div className="bg-cif-primary/5 border border-cif-primary/20 rounded-lg p-4">
          <p className="text-sm text-content-primary">
            <strong>📋 Session 9 :</strong> Implémentation complète du dashboard avec statistiques et
            liste des dossiers.
          </p>
        </div>
      </div>
    </div>
  );
};
