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

### Metrics Endpoint

**Endpoint:** `GET /api/health/metrics`

Exposes health metrics in Prometheus-compatible format for monitoring and alerting.

```
# HELP viewzenix1_api_response_time_ms API response time in milliseconds
# TYPE viewzenix1_api_response_time_ms gauge
viewzenix1_api_response_time_ms{endpoint="/api/v1/orders"} 45.2
viewzenix1_api_response_time_ms{endpoint="/api/v1/webhooks/tradingview"} 65.8

# HELP viewzenix1_database_query_time_ms Database query time in milliseconds
# TYPE viewzenix1_database_query_time_ms gauge
viewzenix1_database_query_time_ms{query_type="read"} 12.3
viewzenix1_database_query_time_ms{query_type="write"} 28.7

# HELP viewzenix1_broker_request_time_ms Broker API request time in milliseconds
# TYPE viewzenix1_broker_request_time_ms gauge
viewzenix1_broker_request_time_ms{broker="alpaca",endpoint="orders"} 187.5

# HELP viewzenix1_active_orders Total number of active orders
# TYPE viewzenix1_active_orders gauge
viewzenix1_active_orders 12

# HELP viewzenix1_webhook_count_total Total number of received webhooks
# TYPE viewzenix1_webhook_count_total counter
viewzenix1_webhook_count_total{status="success"} 156
viewzenix1_webhook_count_total{status="error"} 8
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

#### Advanced Prometheus Configuration

For production environments, consider these additional configurations:

```yaml
scrape_configs:
  - job_name: 'viewzenix1'
    metrics_path: '/api/health/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ['viewzenix1-server:8000']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'viewzenix1-production'
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'viewzenix1_.*'
        action: keep
```

#### Example Alert Rules

Create a `viewzenix1_alerts.yml` file:

```yaml
groups:
- name: viewzenix1
  rules:
  - alert: ViewzenixApiHighLatency
    expr: avg(viewzenix1_api_response_time_ms) > 500
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API latency"
      description: "Viewzenix1 API is experiencing high latency (>500ms) for the last 5 minutes"

  - alert: ViewzenixDatabaseLatency
    expr: max(viewzenix1_database_query_time_ms) > 1000
    for: 3m
    labels:
      severity: critical
    annotations:
      summary: "Critical database latency"
      description: "Database queries are taking longer than 1 second to complete"
```

### Grafana Dashboard

A sample Grafana dashboard for visualizing the health metrics is available in the `/docs/monitoring/grafana-dashboards/` directory.

#### Dashboard Import

1. In Grafana, navigate to Dashboards > Import
2. Upload the JSON file from `/docs/monitoring/grafana-dashboards/viewzenix1-health.json`
3. Select your Prometheus data source
4. Click Import

#### Key Metrics to Monitor

The Grafana dashboard includes panels for:

1. **API Performance**:
   - Response times by endpoint
   - Request rates
   - Error rates

2. **System Resources**:
   - CPU, Memory, and Disk usage
   - Process uptime

3. **Database Performance**:
   - Query latency
   - Connection pool status
   - Transaction rates

4. **Trading Operations**:
   - Order execution times
   - Webhook processing rates
   - Risk check latency

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
```

## Troubleshooting Guide

### Common Health Check Issues

#### Database Connectivity Problems

If the health check shows database connection issues:

1. Verify database credentials in environment variables
2. Check that the database server is running and accessible
3. Inspect network configurations for any firewalls blocking connections
4. Examine database logs for errors

```python
# Manual database connection check
from viewzenix1.db import create_db_connection

def test_db_connection():
    try:
        conn = create_db_connection()
        # Execute a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            return {"status": "connected", "details": cursor.fetchone()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

#### Service Degradation

When services show degraded performance:

1. Check system resource utilization (CPU, memory, disk)
2. Review application logs for errors or warnings
3. Examine dependent service connectivity
4. Verify configuration parameters

#### External Dependency Failures

For issues with external services:

1. Verify API keys and credentials
2. Test connectivity to the external service
3. Check for service status announcements
4. Review rate limiting policies

### Health Check Runbooks

#### Restart Application Services

```bash
# Graceful restart of the API service
sudo systemctl restart viewzenix1-api

# Verify service is running
sudo systemctl status viewzenix1-api
```

#### Clear Cache and Temporary Files

```bash
# Remove temporary files
rm -rf /var/lib/viewzenix1/tmp/*

# Clear Redis cache (if applicable)
redis-cli -h localhost FLUSHDB
```

#### Recover from Database Connection Issues

```bash
# Check database service
sudo systemctl status postgresql

# Restart database if needed
sudo systemctl restart postgresql

# Verify connection pool
sudo netstat -antp | grep postgres
```

## Health Monitoring Best Practices

1. **Regular Testing**: Schedule periodic testing of the health monitoring system itself.
2. **Alerting Thresholds**: Configure appropriate thresholds to avoid alert fatigue.
3. **Correlation Analysis**: Correlate health metrics with business metrics.
4. **Escalation Procedures**: Define clear escalation paths for different types of health issues.
5. **Incident Documentation**: Maintain a record of health incidents and resolution steps.