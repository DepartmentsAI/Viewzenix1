import axios from 'axios';

const API_BASE_URL = '/api/v1';

/**
 * Fetch all orders with optional filters
 * @param {Object} filters - Optional filters like date range, status, etc.
 * @returns {Promise<Array>} List of orders
 */
export const fetchOrders = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    
    // Add filters to query params if they exist
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    
    const response = await axios.get(`${API_BASE_URL}/orders?${queryParams.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching orders:', error);
    throw error;
  }
};

/**
 * Fetch a specific order by ID
 * @param {string} orderId - The ID of the order to fetch
 * @returns {Promise<Object>} The order details
 */
export const fetchOrderById = async (orderId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/orders/${orderId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching order ${orderId}:`, error);
    throw error;
  }
};

/**
 * Export orders to CSV
 * @param {Object} filters - Optional filters like date range, status, etc.
 * @returns {Promise<Blob>} CSV file as blob
 */
export const exportOrdersToCSV = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    
    // Add filters to query params if they exist
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    
    // Set the response type to blob to handle the file download
    const response = await axios.get(`${API_BASE_URL}/orders/export/csv?${queryParams.toString()}`, {
      responseType: 'blob'
    });
    
    return response.data;
  } catch (error) {
    console.error('Error exporting orders to CSV:', error);
    throw error;
  }
};

/**
 * Export orders to Excel
 * @param {Object} filters - Optional filters like date range, status, etc.
 * @returns {Promise<Blob>} Excel file as blob
 */
export const exportOrdersToExcel = async (filters = {}) => {
  try {
    const queryParams = new URLSearchParams();
    
    // Add filters to query params if they exist
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    
    // Set the response type to blob to handle the file download
    const response = await axios.get(`${API_BASE_URL}/orders/export/excel?${queryParams.toString()}`, {
      responseType: 'blob'
    });
    
    return response.data;
  } catch (error) {
    console.error('Error exporting orders to Excel:', error);
    throw error;
  }
};

/**
 * Get order status text and color
 * @param {string} status - The order status
 * @returns {Object} Object containing text and color for the status
 */
export const getOrderStatusInfo = (status) => {
  switch (status) {
    case 'pending':
      return { text: 'Pending', color: 'info' };
    case 'open':
      return { text: 'Open', color: 'warning' };
    case 'partially_filled':
      return { text: 'Partially Filled', color: 'warning' };
    case 'filled':
      return { text: 'Filled', color: 'success' };
    case 'rejected':
      return { text: 'Rejected', color: 'error' };
    case 'canceled':
      return { text: 'Canceled', color: 'error' };
    case 'expired':
      return { text: 'Expired', color: 'error' };
    default:
      return { text: status, color: 'default' };
  }
};

/**
 * Helper function to download a Blob as a file
 * @param {Blob} blob - The blob data
 * @param {string} filename - The name of the file
 */
export const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}; 