/**
 * Page Détail Dossier.
 *
 * TODO Session 10:
 * - Informations client complètes
 * - Liste des pièces avec statuts
 * - Barre de progression
 * - Actions (télécharger rapport, marquer complet)
 * - Timeline des activités
 */

import React from 'react';
import { useParams } from 'react-router-dom';

export const DossierDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h1 className="text-3xl font-bold text-content-primary mb-6">Détail du dossier</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-content-secondary mb-4">Dossier ID: {id}</p>

        <div className="bg-cif-primary/5 border border-cif-primary/20 rounded-lg p-4">
          <p className="text-sm text-content-primary">
            <strong>📋 Session 10 :</strong> Implémentation complète de la page détail dossier avec
            gestion des pièces, upload, et actions.
          </p>
        </div>
      </div>
    </div>
  );
};
