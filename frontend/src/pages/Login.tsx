/**
 * Page de connexion.
 *
 * Affiche le formulaire de login dans un layout centré avec gradient.
 */

import React from 'react';
import { LoginForm } from '../components/auth/LoginForm';

export const Login: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-cif-primary/10 via-cif-secondary/5 to-surface-bg flex items-center justify-center p-4">
      <LoginForm />
    </div>
  );
};
