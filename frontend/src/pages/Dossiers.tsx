/**
 * Page Liste des Dossiers.
 *
 * Affiche tous les dossiers du courtier avec filtres et recherche.
 * TODO Session 9: Implémentation complète avec tableaux et filtres.
 */

import React from 'react';

export const Dossiers: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold text-content-primary mb-6">Mes dossiers</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-content-secondary mb-4">
          Liste de tous vos dossiers clients en cours.
        </p>

        <div className="bg-cif-primary/5 border border-cif-primary/20 rounded-lg p-4">
          <p className="text-sm text-content-primary">
            <strong>📋 Session 9 :</strong> Implémentation de la liste complète avec filtres, tri et
            recherche.
          </p>
        </div>
      </div>
    </div>
  );
};
