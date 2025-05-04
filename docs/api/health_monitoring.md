# Health Check API Documentation

## Overview

The Health Check API provides endpoints for monitoring the health and status of the Viewzenix1 trading application. These endpoints allow external monitoring systems to check the overall health of the application, as well as detailed status information about individual components.

## Endpoints

### Basic Health Check

**Endpoint:** `GET /api/health`

Returns a simple health check response with basic system information. This endpoint is designed for quick status checks by load balancers and monitoring systems.

#### Response Format

```json
{
  "status": "healthy", // or "degraded"
  "timestamp": "2025-05-09T12:34:56.789Z",
  "uptime_seconds": 3600,
  "database": {
    "connected": true,
    "status": "connected"
  },
  "version": "1.0.0"
}
```

### Detailed Health Check

**Endpoint:** `GET /api/health/details`

Provides a comprehensive health check of all system components, including the database, integration services, and any external dependencies.

#### Response Format

```json
{
  "status": "healthy", // "healthy", "degraded", or "unhealthy"
  "timestamp": "2025-05-09T12:34:56.789Z",
  "uptime_seconds": 3600,
  "database": {
    "connected": true,
    "status": "connected",
    "latency_ms": 15,
    "query_success_rate": 99.9
  },
  "services": {
    "order_execution": {
      "status": "healthy",
      "last_execution_time": "2025-05-09T12:30:00.000Z"
    },
    "risk_management": {
      "status": "healthy",
      "active_rules": 5
    },
    "broker_integration": {
      "status": "healthy",
      "connected_brokers": ["alpaca", "paper_trading"]
    }
  },
  "external_dependencies": {
    "market_data_provider": {
      "status": "connected",
      "latency_ms": 250
    }
  },
  "system": {
    "cpu_usage_percent": 45,
    "memory_usage_percent": 60,
    "disk_usage_percent": 35
  }
}
```

## Integration with Monitoring Systems

### Prometheus Integration

The health endpoints can be scraped by Prometheus for monitoring. Configure your `prometheus.yml` as follows:

```yaml
scrape_configs:
  - job_name: 'viewzenix1'
    metrics_path: '/api/health/metrics'
    scrape_interval: 15s
    static_configs:
      - targets: ['viewzenix1-server:8000']
```

### Grafana Dashboard

A sample Grafana dashboard for visualizing the health metrics is available in the `/docs/monitoring/grafana-dashboards/` directory.

## Health Status Codes

The API uses consistent status codes across all health endpoints:

- `200 OK`: System is healthy
- `429 Too Many Requests`: Rate limiting applied
- `503 Service Unavailable`: System is in a degraded or unhealthy state

## Implementing Custom Health Checks

You can extend the health checking system by implementing the `HealthCheck` interface:

```python
from viewzenix1.health import HealthCheck, HealthStatus

class CustomServiceHealthCheck(HealthCheck):
    def check_health(self) -> HealthStatus:
        # Implement health check logic
        return HealthStatus(
            status="healthy",
            details={"custom_metric": 100}
        )
```

Then register your custom health check in `app.py`:

```python
from viewzenix1.health import health_registry
from custom_health import CustomServiceHealthCheck

health_registry.register("custom_service", CustomServiceHealthCheck()) 