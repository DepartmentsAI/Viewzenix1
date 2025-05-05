import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme';
import Dashboard from './pages/Dashboard';
import OrdersPage from './pages/OrdersPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';
import { initCompatibilityCheck } from './utils/browser-compatibility-check';
import BrowserCompatibilityChecker from './components/BrowserCompatibilityChecker';

function App() {
  useEffect(() => {
    // Initialize browser compatibility check
    initCompatibilityCheck({
      showWarning: true,
      blockIncompatible: false, // Set to true to redirect incompatible browsers
      onCheck: (results) => {
        // Log compatibility results for debugging
        if (!results.fullCompatibility) {
          console.warn('Browser compatibility issues detected:', results);
        }
      }
    }).catch(err => {
      console.error('Error checking browser compatibility:', err);
    });
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* Browser compatibility checker component */}
      <BrowserCompatibilityChecker 
        showOnlyWhenIncompatible={true}
        allowDismiss={true}
        severity="warning"
      />
      
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App; 