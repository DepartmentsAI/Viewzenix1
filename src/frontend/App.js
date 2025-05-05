import React, { useState, useMemo } from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Theme
import { lightTheme, darkTheme } from './styles/theme';

// Layout
import Layout from './components/Layout';

// Pages
import Dashboard from './pages/Dashboard';
import RiskManagement from './pages/RiskManagement';
import Configurations from './pages/Configurations';
import Logs from './pages/Logs';
import NotFound from './pages/NotFound';

/**
 * Main application component
 * Provides theme provider, routing, and layout wrapper
 */
function App() {
  // Theme state
  const [darkMode, setDarkMode] = useState(true);
  
  // Memoize theme to prevent unnecessary re-renders
  const theme = useMemo(
    () => darkMode ? darkTheme : lightTheme,
    [darkMode]
  );

  // Function to toggle between light and dark themes
  const toggleTheme = () => {
    setDarkMode(!darkMode);
    // Save preference to localStorage for persistence
    localStorage.setItem('darkMode', !darkMode);
  };

  // Check localStorage for theme preference on initial load
  React.useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode !== null) {
      setDarkMode(savedDarkMode === 'true');
    }
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/" element={<Layout toggleTheme={toggleTheme} darkMode={darkMode} />}>
          <Route index element={<Dashboard />} />
          <Route path="risk" element={<RiskManagement />} />
          <Route path="config" element={<Configurations />} />
          <Route path="logs" element={<Logs />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}

export default App; 