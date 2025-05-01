import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  TablePagination,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid
} from '@mui/material';

// Mock data for logs
const mockLogs = Array(50).fill(null).map((_, index) => ({
  id: `log-${index + 1}`,
  timestamp: new Date(Date.now() - (index * 1000 * 60 * 5)).toISOString(),
  type: ['webhook', 'order', 'error', 'system'][Math.floor(Math.random() * 4)],
  message: [
    'Received alert from TradingView',
    'Order executed successfully',
    'Failed to place order',
    'System status updated',
    'Cleanup service ran',
    'Global SL/TP check executed'
  ][Math.floor(Math.random() * 6)],
  details: JSON.stringify({
    symbol: ['BTCUSD', 'ETHUSD', 'AAPL', 'MSFT'][Math.floor(Math.random() * 4)],
    action: ['buy', 'sell'][Math.floor(Math.random() * 2)],
    status: ['success', 'pending', 'failed'][Math.floor(Math.random() * 3)]
  })
}));

function Logs() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Filter logs based on type and search query
  const filteredLogs = mockLogs.filter(log => {
    const matchesType = filterType === 'all' || log.type === filterType;
    const matchesSearch = searchQuery === '' || 
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.details.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesType && matchesSearch;
  });

  // Get logs for current page
  const currentLogs = filteredLogs.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Get color for log type
  const getTypeColor = (type) => {
    switch (type) {
      case 'webhook': return 'primary';
      case 'order': return 'success';
      case 'error': return 'error';
      case 'system': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Logs
      </Typography>
      
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search logs"
              variant="outlined"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              size="small"
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Filter by type</InputLabel>
              <Select
                value={filterType}
                label="Filter by type"
                onChange={(e) => setFilterType(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="webhook">Webhook</MenuItem>
                <MenuItem value="order">Order</MenuItem>
                <MenuItem value="error">Error</MenuItem>
                <MenuItem value="system">System</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>
      
      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentLogs.map((log) => (
              <TableRow key={log.id} hover>
                <TableCell component="th" scope="row">
                  {new Date(log.timestamp).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Chip 
                    label={log.type} 
                    color={getTypeColor(log.type)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{log.message}</TableCell>
                <TableCell>
                  <Box 
                    sx={{ 
                      maxWidth: '300px', 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {log.details}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[10, 25, 50]}
        component="div"
        count={filteredLogs.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Box>
  );
}

export default Logs; 