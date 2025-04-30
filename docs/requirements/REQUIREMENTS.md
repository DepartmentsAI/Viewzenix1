# Trading Webhook Platform - Requirements Document

## Overview

The Trading Webhook Platform is a broker-agnostic trade execution system that receives alerts from TradingView and executes trades through various brokers. The system features a React dashboard for configuration and monitoring.

## Core Requirements

### 1. Webhook Receiver (Flask API)

- **Purpose**: Receive and process TradingView alerts
- **Requirements**:
  - Accept POST requests at `/webhook` endpoint
  - Validate incoming JSON against schema
  - Support for HMAC authentication (future)
  - Enqueue trade execution jobs

### 2. Trade Classifier

- **Purpose**: Classify assets and determine trade actions
- **Requirements**:
  - Identify asset class from symbol (crypto, equity, forex)
  - Support various symbol formats (with slashes, dots, dashes)
  - Map TradingView strategy_order_id and strategy_order_action to trade types
  - Comprehensive unit tests for all supported formats

### 3. Order Engine

- **Purpose**: Execute trades through broker adapters
- **Requirements**:
  - Support for Alpaca broker initially
  - Handle different order types (market, limit, stop, bracket, etc.)
  - Support for multiple sizing methods
  - Extensible design for future broker additions

### 4. Risk Management

- **Purpose**: Implement safeguards and protect capital
- **Requirements**:
  - Attach per-order stop-loss and take-profit
  - Implementation of global stop-loss and take-profit (portfolio circuit breaker)
  - Cleanup service for orphaned orders
  - Respect broker-specific restrictions

### 5. Logging System

- **Purpose**: Track all system activity for debugging and analysis
- **Requirements**:
  - Machine-readable logs (logs.jsonl)
  - Human-readable logs (activity.log)
  - Log all webhook requests and broker responses
  - Log portfolio status and equity changes

### 6. Testing Framework

- **Purpose**: Ensure reliability through automated testing
- **Requirements**:
  - Pytest-based test suite
  - Postman collection for API testing
  - Mocked broker calls for offline testing
  - Test scenarios for all critical functions

### 7. React Frontend

- **Purpose**: Provide user interface for configuration and monitoring
- **Requirements**:
  - Dashboard with tabs for different functionality areas
  - Advanced settings for trade execution configuration
  - Bot status monitoring and control
  - Log viewer and analytics

## Non-Functional Requirements

### Performance

- Maximum webhook processing time: < 500ms
- Support multiple concurrent webhook requests
- Background processing for non-critical operations

### Security

- Secure API key storage
- IP whitelisting for webhook endpoint
- Future: JWT + RBAC for multi-tenant support

### Scalability

- Support for multiple trading bots
- Future: Multi-tenant workspaces and per-user API keys

### Maintainability

- Modular architecture for easy extension
- Comprehensive documentation
- Clean, testable code

## Future Enhancements

1. Multi-tenant workspaces
2. AI analytics for trade performance
3. Live WebSocket broker feed
4. Additional broker adapters (IBKR, Binance)
5. Auto-generated TradingView alert builders

## Acceptance Criteria

1. Successfully process TradingView alerts according to specification
2. Execute trades through Alpaca with proper risk management
3. Provide reactive and intuitive UI for configuration
4. Pass all automated tests
5. Demonstrate manual test scenario for crypto trading
6. Deploy securely to Fly.io 