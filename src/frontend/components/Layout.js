import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Toolbar, Container, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';

// Import our custom Navigation component
import Nav from './Nav';

/**
 * Main layout component that wraps the entire application
 * Provides navigation and consistent layout structure
 */
function Layout({ toggleTheme, darkMode }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Navigation */}
      <Nav toggleTheme={toggleTheme} darkMode={darkMode} />
      
      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          backgroundColor: theme.palette.background.default,
        }}
      >
        {isMobile ? null : <Toolbar />} {/* Spacer for fixed navbar on desktop */}
        <Container maxWidth="xl" sx={{ py: 3 }}>
          <Outlet />
        </Container>
      </Box>
      
      {/* Footer */}
      <Box
        component="footer"
        sx={{
          py: 2,
          px: 2,
          mt: 'auto',
          backgroundColor: theme.palette.background.paper,
          borderTop: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Container maxWidth="xl">
          <Box sx={{ textAlign: 'center', color: theme.palette.text.secondary, fontSize: '0.875rem' }}>
            © {new Date().getFullYear()} Viewzenix1 Trading Platform
          </Box>
        </Container>
      </Box>
    </Box>
  );
}

export default Layout; 