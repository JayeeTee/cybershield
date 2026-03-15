import React from 'react';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import CloudScanner from './pages/Scanners/CloudScanner';
import SecretsScanner from './pages/Scanners/SecretsScanner';
import ThreatIntel from './pages/Scanners/ThreatIntel';
import ContainerScanner from './pages/Scanners/ContainerScanner';
import NetworkAnalyzer from './pages/Scanners/NetworkAnalyzer';
import ScanHistory from './pages/ScanHistory';
import SettingsPage from './pages/Settings';
import EnhancedDashboard from './pages/EnhancedDashboard';
import RemediationGuide from './pages/RemediationGuide';
import UserManagement from './pages/UserManagement';
import AuditLogPage from './pages/AuditLogPage';
import ReportGenerator from './pages/ReportGenerator';
import EmailNotifications from './pages/EmailNotifications';
import TwoFactorSetup from './pages/TwoFactorSetup';
import ScheduledScans from './pages/ScheduledScans';
import SlackIntegration from './pages/SlackIntegration';
import ApiKeysManagement from './pages/ApiKeysManagement';
import ThemeCustomization from './pages/ThemeCustomization';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import authService from './services/auth';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return authService.isAuthenticated() ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <WebSocketProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/cloud"
          element={
            <PrivateRoute>
              <Layout>
                <CloudScanner />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/secrets"
          element={
            <PrivateRoute>
              <Layout>
                <SecretsScanner />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/threats"
          element={
            <PrivateRoute>
              <Layout>
                <ThreatIntel />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/container"
          element={
            <PrivateRoute>
              <Layout>
                <ContainerScanner />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/network"
          element={
            <PrivateRoute>
              <Layout>
                <NetworkAnalyzer />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/history"
          element={
            <PrivateRoute>
              <Layout>
                <ScanHistory />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <PrivateRoute>
              <Layout>
                <SettingsPage />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <PrivateRoute>
              <Layout>
                <EnhancedDashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/remediation"
          element={
            <PrivateRoute>
              <Layout>
                <RemediationGuide />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/users"
          element={
            <PrivateRoute>
              <Layout>
                <UserManagement />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <PrivateRoute>
              <Layout>
                <AuditLogPage />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <PrivateRoute>
              <Layout>
                <ReportGenerator />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/email"
          element={
            <PrivateRoute>
              <Layout>
                <EmailNotifications />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/2fa"
          element={
            <PrivateRoute>
              <Layout>
                <TwoFactorSetup />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/schedule"
          element={
            <PrivateRoute>
              <Layout>
                <ScheduledScans />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/slack"
          element={
            <PrivateRoute>
              <Layout>
                <SlackIntegration />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/api-keys"
          element={
            <PrivateRoute>
              <Layout>
                <ApiKeysManagement />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/theme"
          element={
            <PrivateRoute>
              <Layout>
                <ThemeCustomization />
              </Layout>
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
    </WebSocketProvider>
  );
}

export default App;
