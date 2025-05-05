# Environment Restoration Checklist

This document provides a step-by-step checklist for restoring a working development environment for the Viewzenix1 platform. Follow these steps in order to set up a fully functional environment.

## Prerequisites

- Git installed and configured
- Python 3.9+ installed
- Node.js 16+ installed
- npm 8+ or yarn 1.22+ installed
- Access to GitHub repository

## 1. Repository Setup

- [ ] Clone the repository (if not already done)
  ```bash
  git clone https://github.com/DepartmentsAI/Viewzenix1.git
  cd Viewzenix1
  ```

- [ ] Ensure you're on the develop branch with latest changes
  ```bash
  git checkout develop
  git pull origin develop --rebase
  ```

## 2. Backend Setup

- [ ] Create Python virtual environment (recommended)
  ```bash
  # Windows
  python -m venv venv
  .\venv\Scripts\activate

  # macOS/Linux
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Create backend environment file
  ```bash
  # Copy the example .env file
  cp .env.example .env
  
  # Or create a new one with these contents:
  echo "FLASK_APP=src/backend/app.py
  FLASK_ENV=development
  FLASK_DEBUG=1
  ALPACA_API_KEY=PKZPGW4YH1KH3LR1UQP9
  ALPACA_API_SECRET=pfAhZbjm3aTMpSVL4Dw3B0Iy9qxMrXQByP1SAytM
  ALPACA_API_BASE_URL=https://paper-api.alpaca.markets
  ALPACA_WS_URL=wss://paper-api.alpaca.markets/stream
  DATABASE_URL=sqlite:///db.sqlite" > .env
  ```

- [ ] Start the backend server
  ```bash
  # Windows
  .\scripts\start_backend.bat
  
  # macOS/Linux
  chmod +x ./scripts/start_backend.sh
  ./scripts/start_backend.sh
  ```

- [ ] Verify the backend is working
  - Open browser to [http://localhost:5000/api/health](http://localhost:5000/api/health)
  - Should return `{"status": "healthy"}`

## 3. Frontend Setup

- [ ] Install frontend dependencies
  ```bash
  # Navigate to frontend directory
  cd src/frontend
  
  # Install dependencies
  npm install
  # or 
  yarn install
  ```

- [ ] Create frontend environment file
  ```bash
  # Copy the example .env file
  cp .env.example .env
  
  # Or create a new one with these contents:
  echo "REACT_APP_API_URL=http://localhost:5000/api
  REACT_APP_ENVIRONMENT=development
  REACT_APP_DEBUG=true" > .env
  ```

- [ ] Start the frontend application
  ```bash
  # Windows
  ..\..\scripts\start_frontend.bat
  
  # macOS/Linux
  chmod +x ../../scripts/start_frontend.sh
  ../../scripts/start_frontend.sh
  ```

- [ ] Verify the frontend is working
  - Open browser to [http://localhost:3000](http://localhost:3000)
  - Dashboard should load without errors

## 4. Broker API Verification

- [ ] Run the broker connection verification script
  ```bash
  # Activate virtual environment if not already active
  
  # Windows
  python src/integration/utils/verify_broker_connection.py
  
  # macOS/Linux
  python3 src/integration/utils/verify_broker_connection.py
  ```

- [ ] Verify connection success
  - Script should output: `Successfully connected to Alpaca API`
  - Account information should be displayed

## 5. Test Environment Setup

- [ ] Ensure test fixtures are available
  ```bash
  # Verify fixture directory exists
  ls tests/e2e/fixtures/data
  ```

- [ ] If fixtures are missing, run the restore script (added in PR #113)
  ```bash
  # Windows
  python scripts/restore_test_fixtures.py
  
  # macOS/Linux
  python3 scripts/restore_test_fixtures.py
  ```

## 6. Full System Verification

- [ ] Run the basic verification tests
  ```bash
  # Activate virtual environment if not already active
  
  # Windows
  pytest tests/e2e/test_environment_verification.py -v
  
  # macOS/Linux
  python3 -m pytest tests/e2e/test_environment_verification.py -v
  ```

- [ ] All tests should pass with output similar to:
  ```
  ============================= test session starts ==============================
  ...
  tests/e2e/test_environment_verification.py::test_backend_health PASSED
  tests/e2e/test_environment_verification.py::test_frontend_availability PASSED
  tests/e2e/test_environment_verification.py::test_broker_connection PASSED
  tests/e2e/test_environment_verification.py::test_fixtures_available PASSED
  ============================== 4 passed in 8.52s ===============================
  ```

## Troubleshooting

### Backend Issues

- If backend fails to start, check:
  - Python version: `python --version` (should be 3.9+)
  - Flask installation: `pip list | grep Flask`
  - Environment variables: Check `.env` file exists and has correct values
  - Port conflicts: Ensure nothing else is running on port 5000

### Frontend Issues

- If frontend fails to start, check:
  - Node version: `node --version` (should be 16+)
  - npm/yarn version: `npm --version` or `yarn --version`
  - Dependencies: Ensure `node_modules` directory exists
  - Port conflicts: Ensure nothing else is running on port 3000

### Broker API Issues

- If broker connection fails, check:
  - API credentials in `.env` file
  - Internet connectivity
  - Alpaca API status: [https://status.alpaca.markets/](https://status.alpaca.markets/)

### Test Fixture Issues

- If tests fail due to missing fixtures:
  - Run the restore script mentioned in section 5
  - Manually copy fixtures from another team member
  
## Verification Status (May 10, 2025)

✅ Backend API: OPERATIONAL (PR #118, #119)
✅ Frontend Application: OPERATIONAL (PR #122)
✅ Broker Integration: OPERATIONAL (PR #120)
✅ Test Fixtures: OPERATIONAL (PR #113)

All components are now operational for the May 10-12 testing window. 