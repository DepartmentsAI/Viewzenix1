import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Tabs, 
  Tab,
  CircularProgress,
  Alert
} from '@mui/material';
import OrderStatusList from './OrderStatusList';
import OrderHistory from './OrderHistory';
import OrderDetailModal from './OrderDetailModal';
import { fetchOrders } from '../../services/orderService';

// Tabs panel component
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`order-tabpanel-${index}`}
      aria-labelledby={`order-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function OrderTrackingPanel() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  // Fetch orders on component mount
  useEffect(() => {
    const getOrders = async () => {
      setLoading(true);
      try {
        const data = await fetchOrders();
        setOrders(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching orders:', err);
        setError('Failed to load orders. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    getOrders();

    // Set up WebSocket connection for real-time updates
    const ws = new WebSocket('ws://api/v1/orders/stream');
    
    ws.onopen = () => {
      console.log('WebSocket connection established');
    };
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      
      // Update orders state with the new/updated order
      setOrders(currentOrders => {
        const index = currentOrders.findIndex(order => order.id === update.id);
        if (index !== -1) {
          // Update existing order
          const updatedOrders = [...currentOrders];
          updatedOrders[index] = update;
          return updatedOrders;
        } else {
          // Add new order
          return [update, ...currentOrders];
        }
      });
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    // Clean up WebSocket connection on component unmount
    return () => {
      ws.close();
    };
  }, []);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleOrderClick = (order) => {
    setSelectedOrder(order);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  // Filter active orders (pending, open, partially filled)
  const activeOrders = orders.filter(order => 
    ['pending', 'open', 'partially_filled'].includes(order.status)
  );

  // Other orders are considered historical
  const historicalOrders = orders.filter(order => 
    !['pending', 'open', 'partially_filled'].includes(order.status)
  );

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Order Tracking
        </Typography>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Active Orders" id="order-tab-0" aria-controls="order-tabpanel-0" />
          <Tab label="Order History" id="order-tab-1" aria-controls="order-tabpanel-1" />
        </Tabs>
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <>
          <TabPanel value={tabValue} index={0}>
            <OrderStatusList orders={activeOrders} onOrderClick={handleOrderClick} />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <OrderHistory orders={historicalOrders} onOrderClick={handleOrderClick} />
          </TabPanel>
        </>
      )}
      
      <OrderDetailModal 
        open={modalOpen} 
        order={selectedOrder} 
        onClose={handleCloseModal} 
      />
    </Paper>
  );
}

export default OrderTrackingPanel; 