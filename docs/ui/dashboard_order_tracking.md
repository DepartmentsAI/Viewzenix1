# Dashboard Order Status Tracking

## Overview

The Dashboard Order Status Tracking feature provides users with real-time visibility into their open and historical orders. This documentation covers the usage, components, and functionality of this feature.

## Components

### 1. Order Status Dashboard

The Order Status Dashboard is accessible from the main navigation menu under "Orders" and displays:

- **Real-time Order Updates**: Shows live status changes using WebSocket connection
- **Visual Status Indicators**: Color-coded indicators for different order states:
  - Green: Filled/Completed
  - Blue: Pending
  - Yellow: Partially Filled
  - Red: Rejected/Canceled
  - Gray: Expired
- **Order Information**: Displays key information for each order:
  - Symbol
  - Type (Market, Limit, Stop)
  - Side (Buy/Sell)
  - Quantity
  - Price
  - Current Status
  - Submission Time

#### Usage

- **Filtering**: Use the filter controls at the top of the dashboard to filter orders by:
  - Status
  - Symbol
  - Order Type
  - Side
- **Sorting**: Click on column headers to sort orders by that column
- **Refreshing**: Click the refresh button to manually refresh data (automatic updates occur via WebSocket)

### 2. Order History View

The Order History view allows users to explore their past orders with:

- **Date Range Selection**: Filter orders by specific date ranges using the date picker
- **Advanced Filtering**: Combined filters for status, symbol, type, etc.
- **Pagination**: Navigate through large sets of historical orders
- **Export Functionality**: Export data in CSV or Excel format using the "Export" button

#### Usage

- **Date Range**: Use the calendar picker to select start and end dates
- **Advanced Search**: Use the search field for text-based filtering
- **Exporting**: Click the export button and select your preferred format

### 3. Order Detail Modal

Clicking on any order in either the dashboard or history view opens the Order Detail Modal, which shows:

- **Comprehensive Order Information**: All order parameters and execution details
- **Associated Risk Parameters**: Stop-loss/take-profit levels (if applicable)
- **Execution Details**: For filled orders, shows time, price, and execution venue
- **Position P&L**: Current profit/loss for the position (if applicable)

#### Usage

- **Accessing**: Click on any order row to view details
- **Closing**: Click the "X" or press ESC to close the modal

## Responsive Design

The Order Status Tracking UI is fully responsive and adapts to all device sizes:

- **Desktop View**: Full tabular view with all columns visible
- **Tablet View**: Condensed table with essential columns, expandable rows
- **Mobile View**: Card-based layout with swipeable order cards

## Data Refresh & Loading States

- **Initial Loading**: Spinner animation when dashboard first loads
- **WebSocket Updates**: Real-time updates without full page refresh
- **Connection Status**: Indicator shows WebSocket connection status
- **Error States**: Visual indication when data loading fails with retry option

## API Endpoints

The UI interacts with the following backend endpoints:

- `GET /api/v1/orders` - Retrieve order list with optional filters
- `GET /api/v1/orders/{order_id}` - Get detailed order information
- WebSocket: `ws://api/v1/orders/stream` - Subscribe to real-time order updates

## Known Limitations

- Historical data older than 30 days may have slower loading times
- Maximum of 1000 orders can be exported at once
- Real-time updates may be delayed by 1-2 seconds during high volume periods 