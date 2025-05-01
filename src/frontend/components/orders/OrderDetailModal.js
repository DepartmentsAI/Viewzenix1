import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  Box,
  Typography,
  Divider,
  Grid,
  Chip,
  IconButton,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { getOrderStatusInfo, fetchOrderById } from '../../services/orderService';

function OrderDetailModal({ open, order, onClose }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detailedOrder, setDetailedOrder] = useState(null);
  
  // Fetch detailed order information when the modal opens with a selected order
  useEffect(() => {
    if (open && order) {
      const fetchDetailedOrder = async () => {
        setLoading(true);
        try {
          const data = await fetchOrderById(order.id);
          setDetailedOrder(data);
          setError(null);
        } catch (err) {
          console.error('Error fetching order details:', err);
          setError('Failed to load order details. Please try again later.');
          setDetailedOrder(order); // Fallback to the basic order information
        } finally {
          setLoading(false);
        }
      };
      
      fetchDetailedOrder();
    }
  }, [open, order]);
  
  // If no order is selected, don't render the dialog content
  if (!order) return null;
  
  // Use the detailed order if available, otherwise use the provided order
  const displayOrder = detailedOrder || order;
  const { text: statusText, color: statusColor } = getOrderStatusInfo(displayOrder.status);
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            Order Details
          </Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <Box>
            {/* Order Header */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h5">
                {displayOrder.symbol}
              </Typography>
              <Chip 
                label={statusText} 
                color={statusColor} 
                sx={{ fontWeight: 'bold' }}
              />
            </Box>
            
            {/* Basic Order Information */}
            <Typography variant="subtitle1" gutterBottom>
              Order Information
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Order ID
                  </Typography>
                  <Typography variant="body1">
                    {displayOrder.id}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Type
                  </Typography>
                  <Typography variant="body1">
                    {displayOrder.type?.toUpperCase() || 'N/A'}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Side
                  </Typography>
                  <Typography variant="body1" sx={{ color: displayOrder.side === 'buy' ? '#4caf50' : '#f44336' }}>
                    {displayOrder.side?.toUpperCase() || 'N/A'}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Quantity
                  </Typography>
                  <Typography variant="body1">
                    {displayOrder.quantity || 'N/A'}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Price
                  </Typography>
                  <Typography variant="body1">
                    {displayOrder.price ? `$${displayOrder.price}` : 'Market'}
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Created At
                  </Typography>
                  <Typography variant="body1">
                    {new Date(displayOrder.created_at).toLocaleString()}
                  </Typography>
                </Box>
              </Grid>
              
              {displayOrder.updated_at && (
                <Grid item xs={12} sm={6} md={4}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Last Updated
                    </Typography>
                    <Typography variant="body1">
                      {new Date(displayOrder.updated_at).toLocaleString()}
                    </Typography>
                  </Box>
                </Grid>
              )}
              
              {displayOrder.filled_at && (
                <Grid item xs={12} sm={6} md={4}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Filled At
                    </Typography>
                    <Typography variant="body1">
                      {new Date(displayOrder.filled_at).toLocaleString()}
                    </Typography>
                  </Box>
                </Grid>
              )}
              
              {displayOrder.filled_quantity && (
                <Grid item xs={12} sm={6} md={4}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Filled Quantity
                    </Typography>
                    <Typography variant="body1">
                      {displayOrder.filled_quantity}
                    </Typography>
                  </Box>
                </Grid>
              )}
              
              {displayOrder.filled_price && (
                <Grid item xs={12} sm={6} md={4}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Filled Price
                    </Typography>
                    <Typography variant="body1">
                      ${displayOrder.filled_price}
                    </Typography>
                  </Box>
                </Grid>
              )}
            </Grid>
            
            {/* Risk Management Information */}
            {(displayOrder.stop_loss || displayOrder.take_profit) && (
              <>
                <Divider sx={{ my: 3 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Risk Management
                </Typography>
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  {displayOrder.stop_loss && (
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Stop Loss
                        </Typography>
                        <Typography variant="body1" color="error">
                          ${displayOrder.stop_loss}
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  
                  {displayOrder.take_profit && (
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Take Profit
                        </Typography>
                        <Typography variant="body1" color="success.main">
                          ${displayOrder.take_profit}
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                </Grid>
              </>
            )}
            
            {/* Execution Details */}
            {displayOrder.executions && displayOrder.executions.length > 0 && (
              <>
                <Divider sx={{ my: 3 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Execution Details
                </Typography>
                
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Price</TableCell>
                      <TableCell>Quantity</TableCell>
                      <TableCell>Exchange</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {displayOrder.executions.map((execution, index) => (
                      <TableRow key={index}>
                        <TableCell>{new Date(execution.timestamp).toLocaleString()}</TableCell>
                        <TableCell>${execution.price}</TableCell>
                        <TableCell>{execution.quantity}</TableCell>
                        <TableCell>{execution.exchange}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </>
            )}
            
            {/* Position Information */}
            {displayOrder.position && (
              <>
                <Divider sx={{ my: 3 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Position Information
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Position ID
                      </Typography>
                      <Typography variant="body1">
                        {displayOrder.position.id}
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Size
                      </Typography>
                      <Typography variant="body1">
                        {displayOrder.position.size}
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Average Entry Price
                      </Typography>
                      <Typography variant="body1">
                        ${displayOrder.position.avg_entry_price}
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Current Price
                      </Typography>
                      <Typography variant="body1">
                        ${displayOrder.position.current_price}
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        P&L
                      </Typography>
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          color: displayOrder.position.profit_loss >= 0 ? 'success.main' : 'error.main',
                          fontWeight: 'bold'
                        }}
                      >
                        ${displayOrder.position.profit_loss} ({displayOrder.position.profit_loss_percent}%)
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </>
            )}
          </Box>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default OrderDetailModal; 