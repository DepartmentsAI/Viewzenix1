import React from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Grid, 
  Typography, 
  Chip, 
  IconButton,
  Tooltip,
  LinearProgress
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import { getOrderStatusInfo } from '../../services/orderService';

function OrderStatusList({ orders, onOrderClick }) {
  // If no orders, show a message
  if (!orders || orders.length === 0) {
    return (
      <Box sx={{ py: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No active orders at the moment.
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={2}>
      {orders.map((order) => {
        const { text: statusText, color: statusColor } = getOrderStatusInfo(order.status);
        
        // Calculate fill percentage for partially filled orders
        const fillPercentage = order.status === 'partially_filled' && order.filled_quantity && order.quantity
          ? Math.round((order.filled_quantity / order.quantity) * 100)
          : 0;
        
        return (
          <Grid item xs={12} md={6} lg={4} key={order.id}>
            <Card 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                position: 'relative',
                '&:hover': {
                  boxShadow: 6,
                }
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6" component="div">
                    {order.symbol}
                  </Typography>
                  <Chip 
                    label={statusText} 
                    color={statusColor} 
                    size="small"
                  />
                </Box>
                
                <Box sx={{ mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Type: {order.type?.toUpperCase() || 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Side: <span style={{ color: order.side === 'buy' ? '#4caf50' : '#f44336' }}>
                      {order.side?.toUpperCase() || 'N/A'}
                    </span>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Quantity: {order.quantity || 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Price: {order.price ? `$${order.price}` : 'Market'}
                  </Typography>
                </Box>
                
                {order.status === 'partially_filled' && (
                  <Box sx={{ width: '100%', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Fill Progress: {fillPercentage}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={fillPercentage} 
                      color="primary" 
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                )}
                
                <Box sx={{ mt: 'auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(order.created_at).toLocaleString()}
                  </Typography>
                  <Tooltip title="View Details">
                    <IconButton 
                      size="small" 
                      color="primary" 
                      onClick={() => onOrderClick(order)}
                    >
                      <InfoIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        );
      })}
    </Grid>
  );
}

export default OrderStatusList; 