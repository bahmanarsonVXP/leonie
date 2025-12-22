/**
 * Composant principal de l'application Léonie.
 *
 * Configure:
 * - AuthProvider (contexte d'authentification global)
 * - BrowserRouter (routing React Router)
 * - Routes protégées et publiques
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Layout } from './components/layout/Layout';

// Pages
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Dossiers } from './pages/Dossiers';
import { DossierDetail } from './pages/DossierDetail';
import { Admin } from './pages/Admin';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Route publique : Login */}
          <Route path="/login" element={<Login />} />

          {/* Routes protégées avec Layout */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dossiers"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dossiers />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/dossiers/:id"
            element={
              <ProtectedRoute>
                <Layout>
                  <DossierDetail />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin>
                <Layout>
                  <Admin />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Redirect root vers dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* 404 - Page non trouvée */}
          <Route
            path="*"
            element={
              <div className="min-h-screen bg-surface-bg flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-content-primary mb-4">404</h1>
                  <p className="text-content-secondary mb-6">Page non trouvée</p>
                  <a
                    href="/dashboard"
                    className="text-cif-primary hover:text-cif-primary-dark underline"
                  >
                    Retour au tableau de bord
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
