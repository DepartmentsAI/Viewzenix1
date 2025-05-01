import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  TablePagination,
  TableSortLabel,
  TextField,
  Typography,
  Chip,
  Button,
  InputAdornment,
  Grid,
  IconButton,
  Tooltip,
  MenuItem,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import { 
  Search as SearchIcon, 
  FileDownload as FileDownloadIcon,
  Info as InfoIcon,
  DateRange as DateRangeIcon
} from '@mui/icons-material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { getOrderStatusInfo, exportOrdersToCSV, exportOrdersToExcel, downloadBlob } from '../../services/orderService';

// Sorting function
function descendingComparator(a, b, orderBy) {
  if (b[orderBy] === null || b[orderBy] === undefined) return -1;
  if (a[orderBy] === null || a[orderBy] === undefined) return 1;
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

function getComparator(order, orderBy) {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

function stableSort(array, comparator) {
  const stabilizedThis = array.map((el, index) => [el, index]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) return order;
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

// Table head with sorting
function EnhancedTableHead(props) {
  const { order, orderBy, onRequestSort } = props;
  
  const headCells = [
    { id: 'symbol', label: 'Symbol' },
    { id: 'type', label: 'Type' },
    { id: 'side', label: 'Side' },
    { id: 'quantity', label: 'Quantity' },
    { id: 'price', label: 'Price' },
    { id: 'status', label: 'Status' },
    { id: 'created_at', label: 'Created At' },
    { id: 'actions', label: 'Actions', disableSort: true }
  ];
  
  const createSortHandler = (property) => (event) => {
    onRequestSort(event, property);
  };

  return (
    <TableHead>
      <TableRow>
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            align={headCell.id === 'actions' ? 'center' : 'left'}
            sortDirection={orderBy === headCell.id ? order : false}
            sx={{ fontWeight: 'bold' }}
          >
            {headCell.disableSort ? (
              headCell.label
            ) : (
              <TableSortLabel
                active={orderBy === headCell.id}
                direction={orderBy === headCell.id ? order : 'asc'}
                onClick={createSortHandler(headCell.id)}
              >
                {headCell.label}
              </TableSortLabel>
            )}
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

function OrderHistory({ orders, onOrderClick }) {
  // State for sorting
  const [order, setOrder] = useState('desc');
  const [orderBy, setOrderBy] = useState('created_at');
  
  // State for pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // State for filtering
  const [filters, setFilters] = useState({
    symbol: '',
    status: '',
    startDate: null,
    endDate: null
  });
  
  // Filtered orders
  const [filteredOrders, setFilteredOrders] = useState(orders || []);
  
  // Effect to filter orders when filters or orders change
  useEffect(() => {
    let result = [...(orders || [])];
    
    // Filter by symbol
    if (filters.symbol) {
      result = result.filter(order => 
        order.symbol && order.symbol.toLowerCase().includes(filters.symbol.toLowerCase())
      );
    }
    
    // Filter by status
    if (filters.status) {
      result = result.filter(order => order.status === filters.status);
    }
    
    // Filter by date range
    if (filters.startDate) {
      result = result.filter(order => 
        new Date(order.created_at) >= new Date(filters.startDate)
      );
    }
    
    if (filters.endDate) {
      // Add one day to include the end date fully
      const endDate = new Date(filters.endDate);
      endDate.setDate(endDate.getDate() + 1);
      
      result = result.filter(order => 
        new Date(order.created_at) < endDate
      );
    }
    
    setFilteredOrders(result);
    setPage(0); // Reset to first page when filters change
    
  }, [orders, filters]);
  
  // Handler for sort request
  const handleRequestSort = (event, property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };
  
  // Handlers for pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Handler for filter changes
  const handleFilterChange = (field) => (event) => {
    setFilters({ ...filters, [field]: event.target.value });
  };
  
  // Handle date filter changes
  const handleDateChange = (field) => (date) => {
    setFilters({ ...filters, [field]: date });
  };
  
  // Export handlers
  const handleExportCSV = async () => {
    try {
      const blob = await exportOrdersToCSV(filters);
      downloadBlob(blob, `orders-export-${new Date().toISOString().split('T')[0]}.csv`);
    } catch (error) {
      console.error('Error exporting to CSV:', error);
    }
  };
  
  const handleExportExcel = async () => {
    try {
      const blob = await exportOrdersToExcel(filters);
      downloadBlob(blob, `orders-export-${new Date().toISOString().split('T')[0]}.xlsx`);
    } catch (error) {
      console.error('Error exporting to Excel:', error);
    }
  };
  
  // Calculate the sorted and paginated orders
  const sortedOrders = stableSort(filteredOrders, getComparator(order, orderBy));
  const paginatedOrders = sortedOrders.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  
  // If no orders, show a message
  if (!orders || orders.length === 0) {
    return (
      <Box sx={{ py: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No order history available.
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Filter Section */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Filters
        </Typography>
        
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={12} sm={6} md={3}>
            <TextField 
              label="Symbol"
              fullWidth
              value={filters.symbol}
              onChange={handleFilterChange('symbol')}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel id="status-filter-label">Status</InputLabel>
              <Select
                labelId="status-filter-label"
                value={filters.status}
                label="Status"
                onChange={handleFilterChange('status')}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="filled">Filled</MenuItem>
                <MenuItem value="rejected">Rejected</MenuItem>
                <MenuItem value="canceled">Canceled</MenuItem>
                <MenuItem value="expired">Expired</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="Start Date"
                value={filters.startDate}
                onChange={handleDateChange('startDate')}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <DatePicker
                label="End Date"
                value={filters.endDate}
                onChange={handleDateChange('endDate')}
                slotProps={{ textField: { fullWidth: true } }}
              />
            </Grid>
          </LocalizationProvider>
        </Grid>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2">
            {filteredOrders.length} orders found
          </Typography>
          
          <Box>
            <Button 
              variant="outlined" 
              startIcon={<FileDownloadIcon />}
              onClick={handleExportCSV}
              sx={{ mr: 1 }}
              size="small"
            >
              CSV
            </Button>
            <Button 
              variant="outlined" 
              startIcon={<FileDownloadIcon />}
              onClick={handleExportExcel}
              size="small"
            >
              Excel
            </Button>
          </Box>
        </Box>
      </Paper>
      
      {/* Table Section */}
      <Paper>
        <TableContainer>
          <Table size="medium">
            <EnhancedTableHead
              order={order}
              orderBy={orderBy}
              onRequestSort={handleRequestSort}
            />
            <TableBody>
              {paginatedOrders.map((order) => {
                const { text: statusText, color: statusColor } = getOrderStatusInfo(order.status);
                
                return (
                  <TableRow key={order.id} hover>
                    <TableCell>{order.symbol}</TableCell>
                    <TableCell>{order.type?.toUpperCase() || 'N/A'}</TableCell>
                    <TableCell>
                      <span style={{ color: order.side === 'buy' ? '#4caf50' : '#f44336' }}>
                        {order.side?.toUpperCase() || 'N/A'}
                      </span>
                    </TableCell>
                    <TableCell>{order.quantity || 'N/A'}</TableCell>
                    <TableCell>{order.price ? `$${order.price}` : 'Market'}</TableCell>
                    <TableCell>
                      <Chip 
                        label={statusText} 
                        color={statusColor} 
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{new Date(order.created_at).toLocaleString()}</TableCell>
                    <TableCell align="center">
                      <Tooltip title="View Details">
                        <IconButton 
                          size="small" 
                          color="primary" 
                          onClick={() => onOrderClick(order)}
                        >
                          <InfoIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
              
              {/* Empty rows to maintain consistent height */}
              {paginatedOrders.length === 0 && (
                <TableRow style={{ height: 53 }}>
                  <TableCell colSpan={8} align="center">
                    No orders match the current filters
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredOrders.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  );
}

export default OrderHistory; 