# Trading Webhook Platform

A broker-agnostic webhook platform for automated trading execution from TradingView alerts.

## Overview

The Trading Webhook Platform is a comprehensive solution for executing trades from TradingView alerts through various brokers. The system features a Flask-based API for receiving webhooks and a React dashboard for configuration and monitoring.

## Key Features

- **Deterministic, broker-agnostic trade execution** from TradingView alerts
- **Feature-rich React dashboard** with minimal-click access and advanced settings
- **Comprehensive risk management** with per-order and global stop-loss/take-profit
- **Automated testing** with mocked broker interactions
- **Extensible design** for adding new brokers and features

## Project Structure

```
Viewzenix1/
├── src/                   # Source code
│   ├── backend/           # Flask API and backend services
│   ├── frontend/          # React dashboard
│   └── integration/       # Integration with external services
├── tests/                 # Test files
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── docs/                  # Documentation
│   ├── api/               # API documentation
│   ├── architecture/      # Architecture docs
│   ├── requirements/      # Requirements docs
│   ├── ui/                # UI/UX documentation
│   ├── testing/           # Testing docs
│   └── knowledge-base/    # Shared learnings
└── communication/         # Team communication
    ├── inbox/             # Agent-specific messages
    ├── decision_log.md    # Project decisions
    └── pr_tracker.md      # PR tracking
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Git

### Installation

1. Clone the repository
   ```
   git clone https://github.com/DepartmentsAI/Viewzenix1.git
   cd Viewzenix1
   ```

2. Set up backend
   ```
   cd src/backend
   pip install -r requirements.txt
   ```

3. Set up frontend
   ```
   cd src/frontend
   npm install
   ```

### Running for Development

1. Start the backend server
   ```
   cd src/backend
   python app.py
   ```

2. Start the frontend development server
   ```
   cd src/frontend
   npm run dev
   ```

3. Access the application at http://localhost:3000

## Contributing

1. Ensure you're working in the appropriate branch for your task
2. Follow the code standards and testing requirements
3. Submit pull requests for review

## Testing

Run backend tests:
```
cd src/backend
pytest
```

Run frontend tests:
```
cd src/frontend
npm test
```

## Deployment

The application is deployed on Fly.io with private networking.

## License

[Specify License]

## Contact

[Project Contact Information] 