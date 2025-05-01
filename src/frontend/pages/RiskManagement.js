import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  CardHeader,
  TextField, 
  FormControlLabel, 
  FormGroup, 
  Switch, 
  Button,
  Slider,
  Divider,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import SecurityIcon from '@mui/icons-material/Security';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

// Mock data for active orders with SL/TP
const mockActiveOrders = [
  { 
    id: 'ord-1', 
    symbol: 'BTCUSD', 
    type: 'LONG', 
    entryPrice: 65000, 
    quantity: 0.1,
    slPrice: 63500,
    tpPrice: 68000,
    slPercent: -2.3,
    tpPercent: 4.6,
    status: 'active'
  },
  { 
    id: 'ord-2', 
    symbol: 'ETHUSD', 
    type: 'SHORT', 
    entryPrice: 3200, 
    quantity: 1.5,
    slPrice: 3360,
    tpPrice: 2900,
    slPercent: -5.0,
    tpPercent: 9.4,
    status: 'active'
  },
  { 
    id: 'ord-3', 
    symbol: 'AAPL', 
    type: 'LONG', 
    entryPrice: 186.5, 
    quantity: 10,
    slPrice: 180.0,
    tpPrice: 195.0,
    slPercent: -3.5,
    tpPercent: 4.6,
    status: 'sl_triggered'
  }
];

// Risk thresholds
const RISK_THRESHOLDS = {
  LOW: 30,
  MEDIUM: 60,
  HIGH: 90
};

function RiskManagement() {
  const [tab, setTab] = useState(0);
  const [baseEquity, setBaseEquity] = useState(100000);
  const [currentEquity, setCurrentEquity] = useState(105200);
  const [riskExposure, setRiskExposure] = useState(35); // percent
  
  // Default per-order SL/TP settings
  const [attachSlTp, setAttachSlTp] = useState(true);
  const [useAvgFillForSlTp, setUseAvgFillForSlTp] = useState(true);
  const [slPercent, setSlPercent] = useState(1.0);
  const [tpPercent, setTpPercent] = useState(2.0);
  
  // Global SL/TP settings
  const [enableGlobalSlTp, setEnableGlobalSlTp] = useState(true);
  const [globalSlPercent, setGlobalSlPercent] = useState(20);
  const [globalTpPercent, setGlobalTpPercent] = useState(50);
  
  // Position size limits
  const [maxPositionSize, setMaxPositionSize] = useState(5); // percent of equity
  
  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };
  
  // Get severity based on risk level
  const getRiskSeverity = (value) => {
    if (value <= RISK_THRESHOLDS.LOW) return 'success';
    if (value <= RISK_THRESHOLDS.MEDIUM) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SecurityIcon fontSize="large" sx={{ mr: 2 }} />
        <Typography variant="h4">
          Risk Management
        </Typography>
      </Box>
      
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tab} onChange={handleTabChange} variant="fullWidth">
          <Tab label="Risk Overview" />
          <Tab label="Per-Order Settings" />
          <Tab label="Global Risk Parameters" />
        </Tabs>
      </Paper>
      
      {/* Risk Overview Tab */}
      {tab === 0 && (
        <Box>
          <Grid container spacing={3}>
            {/* Summary Cards */}
            <Grid item xs={12} md={4}>
              <Card>
                <CardHeader title="Portfolio Value" />
                <CardContent>
                  <Typography variant="h4" sx={{ textAlign: 'center' }}>
                    ${currentEquity.toLocaleString()}
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
                    <TrendingUpIcon color="success" />
                    <Typography variant="body2" color="success.main">
                      +{((currentEquity - baseEquity) / baseEquity * 100).toFixed(2)}% from base
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card>
                <CardHeader title="Risk Exposure" />
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1 }}>
                    <Typography variant="h4">
                      {riskExposure}%
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={riskExposure} 
                    color={getRiskSeverity(riskExposure)}
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                  {riskExposure > RISK_THRESHOLDS.MEDIUM && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        Risk exposure is approaching your defined limits
                      </Typography>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card>
                <CardHeader title="Global SL/TP Status" />
                <CardContent sx={{ textAlign: 'center' }}>
                  {enableGlobalSlTp ? (
                    <>
                      <Chip 
                        label="Enabled" 
                        color="success" 
                        sx={{ mb: 1 }}
                      />
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            SL Threshold
                          </Typography>
                          <Typography variant="body1">
                            ${(baseEquity * (1 - globalSlPercent / 100)).toLocaleString()}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            TP Threshold
                          </Typography>
                          <Typography variant="body1">
                            ${(baseEquity * (1 + globalTpPercent / 100)).toLocaleString()}
                          </Typography>
                        </Box>
                      </Box>
                    </>
                  ) : (
                    <Chip 
                      label="Disabled" 
                      color="error" 
                      sx={{ mb: 1 }}
                    />
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            {/* Active Orders with SL/TP */}
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Active Orders with SL/TP
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Symbol</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Entry Price</TableCell>
                        <TableCell>Quantity</TableCell>
                        <TableCell>SL Price</TableCell>
                        <TableCell>TP Price</TableCell>
                        <TableCell>SL %</TableCell>
                        <TableCell>TP %</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {mockActiveOrders.map((order) => (
                        <TableRow key={order.id} hover>
                          <TableCell><strong>{order.symbol}</strong></TableCell>
                          <TableCell>
                            <Chip 
                              label={order.type} 
                              color={order.type === 'LONG' ? 'success' : 'error'} 
                              size="small"
                            />
                          </TableCell>
                          <TableCell>${order.entryPrice}</TableCell>
                          <TableCell>{order.quantity}</TableCell>
                          <TableCell>${order.slPrice}</TableCell>
                          <TableCell>${order.tpPrice}</TableCell>
                          <TableCell sx={{ color: 'error.main' }}>{order.slPercent}%</TableCell>
                          <TableCell sx={{ color: 'success.main' }}>+{order.tpPercent}%</TableCell>
                          <TableCell>
                            <Chip 
                              label={order.status === 'active' ? 'Active' : 'SL Triggered'} 
                              color={order.status === 'active' ? 'primary' : 'error'} 
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}
      
      {/* Per-Order SL/TP Settings Tab */}
      {tab === 1 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Default Per-Order Stop Loss / Take Profit Settings
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormGroup>
                  <FormControlLabel 
                    control={
                      <Switch 
                        checked={attachSlTp} 
                        onChange={(e) => setAttachSlTp(e.target.checked)}
                        color="primary"
                      />
                    } 
                    label="Automatically attach SL/TP to all orders" 
                  />
                  <FormControlLabel 
                    control={
                      <Switch 
                        checked={useAvgFillForSlTp}
                        onChange={(e) => setUseAvgFillForSlTp(e.target.checked)}
                        color="primary"
                        disabled={!attachSlTp}
                      />
                    } 
                    label="Use average fill price for SL/TP (instead of alert price)" 
                  />
                </FormGroup>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ p: 2, border: 1, borderColor: 'error.main', borderRadius: 1 }}>
                  <Typography variant="subtitle1" gutterBottom color="error">
                    <TrendingDownIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                    Stop Loss Settings
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography gutterBottom>
                      SL Percentage: {slPercent}%
                    </Typography>
                    <Slider
                      value={slPercent}
                      onChange={(e, newValue) => setSlPercent(newValue)}
                      step={0.1}
                      min={0.5}
                      max={10}
                      valueLabelDisplay="auto"
                      disabled={!attachSlTp}
                      color="error"
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      This will place a stop loss order {slPercent}% away from the entry price.
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ p: 2, border: 1, borderColor: 'success.main', borderRadius: 1 }}>
                  <Typography variant="subtitle1" gutterBottom color="success">
                    <TrendingUpIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                    Take Profit Settings
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography gutterBottom>
                      TP Percentage: {tpPercent}%
                    </Typography>
                    <Slider
                      value={tpPercent}
                      onChange={(e, newValue) => setTpPercent(newValue)}
                      step={0.1}
                      min={0.5}
                      max={20}
                      valueLabelDisplay="auto"
                      disabled={!attachSlTp}
                      color="success"
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      This will place a take profit order {tpPercent}% away from the entry price.
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="contained" color="primary">
                Save Default Settings
              </Button>
            </Box>
          </Paper>
          
          {/* Visual example of SL/TP */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Visual Example
            </Typography>
            <Box sx={{ height: '200px', position: 'relative', border: '1px solid #333', borderRadius: 1 }}>
              {/* Entry price line */}
              <Box sx={{ 
                position: 'absolute', 
                left: 0, 
                right: 0, 
                top: '50%', 
                height: '2px', 
                bgcolor: 'primary.main',
                zIndex: 1
              }} />
              
              {/* Entry price label */}
              <Box sx={{ 
                position: 'absolute', 
                left: '10px', 
                top: 'calc(50% - 15px)', 
                bgcolor: 'primary.main',
                color: 'white',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.8rem'
              }}>
                Entry: $65,000
              </Box>
              
              {/* Stop Loss line */}
              <Box sx={{ 
                position: 'absolute', 
                left: 0, 
                right: 0, 
                top: `${50 + (slPercent * 5)}%`, 
                height: '2px', 
                bgcolor: 'error.main',
                zIndex: 1
              }} />
              
              {/* Stop Loss label */}
              <Box sx={{ 
                position: 'absolute', 
                right: '10px', 
                top: `calc(${50 + (slPercent * 5)}% - 15px)`, 
                bgcolor: 'error.main',
                color: 'white',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.8rem'
              }}>
                SL: ${Math.round(65000 * (1 - slPercent/100))}
              </Box>
              
              {/* Take Profit line */}
              <Box sx={{ 
                position: 'absolute', 
                left: 0, 
                right: 0, 
                top: `${50 - (tpPercent * 2.5)}%`, 
                height: '2px', 
                bgcolor: 'success.main',
                zIndex: 1
              }} />
              
              {/* Take Profit label */}
              <Box sx={{ 
                position: 'absolute', 
                right: '10px', 
                top: `calc(${50 - (tpPercent * 2.5)}% - 15px)`, 
                bgcolor: 'success.main',
                color: 'white',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.8rem'
              }}>
                TP: ${Math.round(65000 * (1 + tpPercent/100))}
              </Box>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
              This is a visual representation of SL/TP placement for a LONG position on BTCUSD at $65,000.
            </Typography>
          </Paper>
        </Box>
      )}
      
      {/* Global Risk Parameters Tab */}
      {tab === 2 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Global Stop Loss / Take Profit
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                Global SL/TP monitors your total portfolio equity and can automatically close all positions when thresholds are reached.
              </Typography>
            </Alert>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormGroup>
                  <FormControlLabel 
                    control={
                      <Switch 
                        checked={enableGlobalSlTp} 
                        onChange={(e) => setEnableGlobalSlTp(e.target.checked)}
                        color="primary"
                      />
                    } 
                    label="Enable global SL/TP circuit breaker" 
                  />
                </FormGroup>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Base Equity"
                  variant="outlined"
                  type="number"
                  value={baseEquity}
                  onChange={(e) => setBaseEquity(Number(e.target.value))}
                  InputProps={{
                    startAdornment: '$',
                    inputProps: { min: 1000 }
                  }}
                  disabled={!enableGlobalSlTp}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  This is your starting equity value used for SL/TP calculations.
                </Typography>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Typography gutterBottom>
                  Global SL Percentage: {globalSlPercent}%
                </Typography>
                <Slider
                  value={globalSlPercent}
                  onChange={(e, newValue) => setGlobalSlPercent(newValue)}
                  step={1}
                  min={5}
                  max={50}
                  valueLabelDisplay="auto"
                  disabled={!enableGlobalSlTp}
                  color="error"
                />
                <Typography variant="body2" color="text.secondary">
                  Close all positions if equity drops below ${(baseEquity * (1 - globalSlPercent / 100)).toLocaleString()}
                </Typography>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Typography gutterBottom>
                  Global TP Percentage: {globalTpPercent}%
                </Typography>
                <Slider
                  value={globalTpPercent}
                  onChange={(e, newValue) => setGlobalTpPercent(newValue)}
                  step={5}
                  min={10}
                  max={100}
                  valueLabelDisplay="auto"
                  disabled={!enableGlobalSlTp}
                  color="success"
                />
                <Typography variant="body2" color="text.secondary">
                  Optionally close all positions if equity rises above ${(baseEquity * (1 + globalTpPercent / 100)).toLocaleString()}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
          
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Position Size Limits
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography gutterBottom>
                  Maximum Position Size: {maxPositionSize}% of equity
                </Typography>
                <Slider
                  value={maxPositionSize}
                  onChange={(e, newValue) => setMaxPositionSize(newValue)}
                  step={0.5}
                  min={0.5}
                  max={20}
                  valueLabelDisplay="auto"
                  color="primary"
                />
                <Typography variant="body2" color="text.secondary">
                  Limit maximum size of any single position to {maxPositionSize}% of your equity.
                </Typography>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ border: 1, borderColor: 'info.main', borderRadius: 1, p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Example Position Sizes
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">At current equity (${currentEquity.toLocaleString()}):</Typography>
                    <Typography variant="body2">${Math.round(currentEquity * maxPositionSize / 100).toLocaleString()}</Typography>
                  </Box>
                  <Divider sx={{ my: 1 }} />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">At base equity (${baseEquity.toLocaleString()}):</Typography>
                    <Typography variant="body2">${Math.round(baseEquity * maxPositionSize / 100).toLocaleString()}</Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Paper>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="contained" color="primary">
              Save Global Risk Parameters
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
}

export default RiskManagement; 