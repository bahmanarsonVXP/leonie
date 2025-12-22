/**
 * Sidebar de navigation.
 *
 * Navigation principale:
 * - Tableau de bord
 * - Dossiers (liste)
 * - Administration (admin seulement)
 */

import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, FolderOpen, Settings } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

export const Sidebar: React.FC = () => {
  const { isAdmin } = useAuth();

  const navItems = [
    { to: '/dashboard', icon: Home, label: 'Tableau de bord' },
    { to: '/dossiers', icon: FolderOpen, label: 'Dossiers' },
  ];

  // Ajouter admin si autorisé
  if (isAdmin) {
    navItems.push({ to: '/admin', icon: Settings, label: 'Administration' });
  }

  return (
    <aside className="w-64 bg-surface-default border-r border-edge-default h-[calc(100vh-4rem)] sticky top-16">
      {/* Header sidebar */}
      <div className="p-4 border-b border-edge-default">
        <h2 className="text-lg font-semibold text-content-primary">Navigation</h2>
      </div>

      {/* Nav links */}
      <nav className="p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                isActive
                  ? 'bg-cif-primary text-white font-medium'
                  : 'text-content-secondary hover:bg-surface-hover hover:text-content-primary'
              }`
            }
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer sidebar */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-edge-default">
        <p className="text-xs text-content-tertiary text-center">Léonie v1.0.0</p>
      </div>
    </aside>
  );
};
