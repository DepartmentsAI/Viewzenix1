# Trading Webhook Platform - Architecture

## System Architecture Overview

The Trading Webhook Platform is designed as a modular, scalable application with clear separation of concerns. This document outlines the high-level architecture and component interactions.

## Core Components

### 1. Webhook Receiver (API Layer)

- **Purpose**: Exposes HTTP endpoints to receive TradingView alerts
- **Implementation**: Flask API with JSON schema validation
- **Key Responsibilities**:
  - Validate webhook payload format
  - Authenticate incoming requests
  - Queue trade execution jobs
  - Provide status responses

### 2. Trade Classifier

- **Purpose**: Determines the asset class and trade action from symbols
- **Implementation**: Python module with regex-based parsers
- **Key Responsibilities**:
  - Parse trading symbols to identify asset class (crypto, equity, forex)
  - Map strategy actions to trade operations
  - Identify special instructions within alerts

### 3. Order Engine

- **Purpose**: Core trade execution logic
- **Implementation**: Modular engine with strategy pattern for broker selection
- **Key Responsibilities**:
  - Calculate position sizing based on configured rules
  - Select appropriate broker adapter for execution
  - Apply risk management parameters
  - Track order status and fills

### 4. Broker Adapters

- **Purpose**: Interface with specific trading platforms
- **Implementation**: Adapter pattern with interface contracts
- **Key Responsibilities**:
  - Translate generic orders to broker-specific formats
  - Handle authentication with broker APIs
  - Process broker-specific responses
  - Implement broker-specific restrictions

### 5. Risk Management System

- **Purpose**: Protect capital through various safeguards
- **Implementation**: Both per-order and portfolio-wide monitoring
- **Key Responsibilities**:
  - Apply stop-loss and take-profit to individual orders
  - Track global portfolio risk
  - Implement "circuit breaker" protections
  - Clean up orphaned or incomplete orders

### 6. Logging System

- **Purpose**: Record all system activities for debugging and analysis
- **Implementation**: Structured logging with multiple formats
- **Key Responsibilities**:
  - Record webhook requests and responses
  - Track order lifecycle events
  - Log broker interactions
  - Monitor performance metrics

### 7. Frontend Dashboard

- **Purpose**: User interface for configuration and monitoring
- **Implementation**: React with Next.js, modular tabs design
- **Key Responsibilities**:
  - Webhook configuration interface
  - Broker settings management
  - Bot configuration with advanced settings
  - Log viewing and filtering
  - Status monitoring with visual indicators

## Data Flow

1. **TradingView Alert Reception**:
   - TradingView sends webhook alert to Flask API
   - API validates payload and enqueues job
   - Returns immediate acknowledgment

2. **Trade Classification and Execution**:
   - Trade classifier categorizes the trade
   - Order engine calculates sizing and parameters
   - Appropriate broker adapter is selected
   - Order is submitted to broker

3. **Order Tracking and Management**:
   - System monitors order status
   - Risk management rules are applied
   - Updates are logged to file system
   - WebSocket pushes updates to frontend

4. **User Configuration Flow**:
   - User configures settings in React dashboard
   - API stores configuration
   - Settings are applied to subsequent trades

## System Interfaces

### External Interfaces

1. **TradingView Webhook Interface**:
   - `POST /webhook` endpoint
   - Expects JSON payload with alert details
   - Returns HTTP 200 on success, error codes on failure

2. **Broker APIs**:
   - Alpaca REST API (initial implementation)
   - Future: IBKR, Binance, others

### Internal Interfaces

1. **Backend-to-Frontend API**:
   - RESTful API for configuration and data retrieval
   - WebSocket for real-time updates

2. **Database Interface**:
   - SQLite for development, PostgreSQL for production
   - Stores configuration, order history, logs

## Deployment Architecture

- **Docker containerization** for all components
- **Fly.io** for hosting with private networking
- **Database** hosted within Fly.io private network

## Security Architecture

- Webhook authentication with secret key verification
- API keys stored securely in environment variables
- IP whitelisting for webhook endpoints
- HTTPS for all external communication
- Non-exposure of broker credentials

## Future Architecture Extensions

1. **Multi-Tenant Architecture**:
   - Per-user databases and configurations
   - Role-based access control
   - Isolated execution environments

2. **Microservices Evolution**:
   - Split webhook receiver, order engine, and broker adapters
   - Implement message queue for scaling

3. **Advanced Monitoring**:
   - Prometheus metrics
   - Grafana dashboards
   - Alerting system for critical failures

## Architecture Decision Records

Significant architecture decisions will be documented as ADRs in the `/docs/architecture/decisions/` directory. 