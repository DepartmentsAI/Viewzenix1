# Viewzenix1 Trading Platform

This repository contains the source code for the Viewzenix1 trading platform, a system that integrates with various brokers to provide automated trading capabilities.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Pip package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DepartmentsAI/Viewzenix1.git
   cd Viewzenix1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root with the following variables:
     ```
     # Flask Configuration
     FLASK_APP=src/backend/app.py
     FLASK_ENV=development
     FLASK_DEBUG=True
     PORT=5000
     
     # Alpaca API Credentials
     APCA_API_KEY_ID=PKG1F8EEMI2HWAFFWSD7
     APCA_API_SECRET_KEY=PKG1F8EEMI2HWAFFWSD7
     APCA_API_BASE_URL=https://paper-api.alpaca.markets/v2
     ```

## Running the Application

### Starting the Backend API Server

#### Windows
Run the provided batch script:
```cmd
.\scripts\start_backend.bat
```

#### macOS/Linux
Run the provided shell script:
```bash
chmod +x ./scripts/start_backend.sh
./scripts/start_backend.sh
```

#### Manual Start
If you prefer to start the server manually:
```bash
python src/backend/run.py
```

The backend API server will be available at `http://localhost:5000`.

### Starting the Frontend Development Server

To start the frontend development server:
```bash
cd src/frontend
npm install
npm start
```

The frontend development server will be available at `http://localhost:3000`.

## API Documentation

API documentation is available at the following endpoints:

- Health Check API: [API Documentation](/docs/api/health_monitoring.md)
- Webhook API: [API Documentation](/docs/api/webhook.md)
- Risk Management API: [API Documentation](/docs/api/risk_management.md)

## Architecture

For more information about the system architecture, see [Architecture Documentation](/docs/architecture/).

## Contributing

1. Create a feature branch from `develop`: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Push to your branch: `git push origin feature/your-feature-name`
4. Submit a pull request

## Troubleshooting

If you encounter issues with the backend API:

1. Check that the server is running (`http://localhost:5000/api/health`)
2. Verify that the `.env` file exists and contains the correct credentials
3. Check the log files in the `logs/` directory

## License

This project is proprietary and confidential.

## Support

For support, please contact the development team. 