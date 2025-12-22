/**
 * Layout principal de l'application.
 *
 * Structure:
 * - Header fixe en haut
 * - Sidebar à gauche
 * - Contenu principal (children) à droite
 */

import React, { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-surface-bg">
      {/* Header fixe */}
      <Header />

      {/* Container principal avec sidebar et contenu */}
      <div className="flex">
        {/* Sidebar */}
        <Sidebar />

        {/* Contenu principal */}
        <main className="flex-1 p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
