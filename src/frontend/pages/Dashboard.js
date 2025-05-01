import React from 'react';
import { 
  Grid, 
  Paper, 
  Typography, 
  Box, 
  Card, 
  CardContent, 
  CardHeader, 
  Button,
  LinearProgress,
  Alert,
  Chip
} from '@mui/material';
import SecurityIcon from '@mui/icons-material/Security';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
  const navigate = useNavigate();

  // Risk exposure mock data (35%)
  const riskExposure = 35;
  
  // Get color based on risk level
  const getRiskColor = (value) => {
    if (value <= 30) return 'success';
    if (value <= 60) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Trading Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Active Webhooks" />
            <CardContent>
              <Typography variant="h3" align="center">
                3
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Open Positions" />
            <CardContent>
              <Typography variant="h3" align="center">
                5
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Today's Alerts" />
            <CardContent>
              <Typography variant="h3" align="center">
                12
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Risk Management Summary */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SecurityIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Risk Management
                </Typography>
              </Box>
              <Button 
                variant="outlined" 
                color="primary" 
                size="small"
                onClick={() => navigate('/risk-management')}
              >
                View Details
              </Button>
            </Box>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="body2" gutterBottom>
                  Current Risk Exposure
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ flexGrow: 1, mr: 1 }}>
                    <LinearProgress 
                      variant="determinate" 
                      value={riskExposure} 
                      color={getRiskColor(riskExposure)}
                      sx={{ height: 10, borderRadius: 5 }} 
                    />
                  </Box>
                  <Typography variant="body2" color={`${getRiskColor(riskExposure)}.main`}>
                    {riskExposure}%
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Global SL/TP Status
                    </Typography>
                    <Chip 
                      label="Enabled" 
                      color="success" 
                      size="small" 
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      Default SL/TP
                    </Typography>
                    <Typography variant="body2">
                      <span style={{ color: '#f44336' }}>SL: 1.0%</span> | <span style={{ color: '#4caf50' }}>TP: 2.0%</span>
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        {/* Recent Activity */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                Activity data will be displayed here
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        {/* Performance Chart */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Performance
            </Typography>
            <Box sx={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                Performance chart will be displayed here
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard; 