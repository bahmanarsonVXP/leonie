/**
 * Header de l'application.
 *
 * Affiche:
 * - Logo et nom de l'application
 * - Email utilisateur
 * - Bouton déconnexion
 */

import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LogOut, User } from 'lucide-react';

export const Header: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <header className="bg-white border-b border-edge-default shadow-sm sticky top-0 z-50">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo et titre */}
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-cif-primary">Léonie</h1>
            <span className="text-sm text-content-secondary hidden sm:inline">
              Agent IA - Dossiers de prêt
            </span>
          </div>

          {/* Utilisateur et actions */}
          <div className="flex items-center gap-4">
            {/* Info utilisateur */}
            <div className="flex items-center gap-2 text-sm text-content-primary">
              <User size={16} />
              <span className="hidden sm:inline">{user?.email}</span>
              {isAdmin && (
                <span className="ml-2 px-2 py-1 bg-cif-primary/10 text-cif-primary text-xs font-medium rounded">
                  Admin
                </span>
              )}
            </div>

            {/* Bouton déconnexion */}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 text-sm text-content-secondary hover:text-content-primary hover:bg-surface-hover rounded-md transition-colors"
              title="Déconnexion"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Déconnexion</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
