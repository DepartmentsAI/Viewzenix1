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
    "status": "connected",
    "latency_ms": 15
  },
  "system_info": {
    "python_version": "3.9.7",
    "platform": "Linux-5.15.0-x86_64",
    "environment": "production"
  },
  "version": "1.0.0"
}
```

### Detailed Health Check

**Endpoint:** `GET /api/health/detailed`

Provides a comprehensive health check of all system components, including the database, integration services, and any external dependencies.

#### Response Format

```json
{
  "status": "healthy", // "healthy", "degraded", or "unhealthy"
  "timestamp": "2025-05-09T12:34:56.789Z",
  "components": {
    "database": {
      "connected": true,
      "status": "connected",
      "latency_ms": 15
    },
    "broker_service": {
      "connected": true,
      "status": "connected"
    },
    "webhook_system": {
      "operational": true,
      "last_webhook_received": "2025-05-09T12:30:00.000Z"
    },
    "risk_management": {
      "operational": true,
      "status": "active"
    },
    "disk_space": {
      "sufficient": true,
      "available_gb": 75,
      "total_gb": 100,
      "percent_used": 25
    }
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

The health endpoints can be integrated with Prometheus for comprehensive monitoring of the Viewzenix1 platform.

#### Metrics Endpoint

**Endpoint:** `GET /api/metrics`

This endpoint exposes Prometheus-formatted metrics from the application.

#### Sample Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'viewzenix1'
    metrics_path: '/api/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
    static_configs:
      - targets: ['viewzenix1-server:5000']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        regex: '(.*):.*'
        replacement: $1
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

#### Key Metrics

The following key metrics are exposed:

1. **Application Health**
   - `viewzenix1_health_status`: Overall health status (1=healthy, 0=unhealthy)
   - `viewzenix1_uptime_seconds`: Application uptime in seconds

2. **Database Performance**
   - `viewzenix1_db_query_duration_seconds`: Database query duration histogram
   - `viewzenix1_db_connection_errors_total`: Counter of database connection errors

3. **API Performance**
   - `viewzenix1_http_requests_total`: Counter of HTTP requests
   - `viewzenix1_http_request_duration_seconds`: HTTP request duration histogram

4. **Order Processing**
   - `viewzenix1_orders_processed_total`: Counter of processed orders
   - `viewzenix1_order_processing_duration_seconds`: Order processing duration histogram
   - `viewzenix1_order_errors_total`: Counter of order processing errors

5. **Risk Management**
   - `viewzenix1_risk_checks_total`: Counter of risk checks performed
   - `viewzenix1_risk_violations_total`: Counter of risk violations detected

6. **System Resources**
   - `viewzenix1_memory_usage_bytes`: Memory usage in bytes
   - `viewzenix1_cpu_usage_percent`: CPU usage percentage
   - `viewzenix1_disk_usage_bytes`: Disk usage in bytes

### Grafana Dashboard

A Grafana dashboard template is available for visualizing Viewzenix1 metrics.

#### Dashboard Installation

1. Import the dashboard JSON from `/workspace/Viewzenix1/docs/monitoring/grafana/viewzenix1-dashboard.json`
2. Configure the Prometheus data source
3. Adjust any variables to match your environment

#### Dashboard Panels

The dashboard includes the following panel groups:

1. **System Overview**
   - Application Status (healthy/degraded/unhealthy)
   - Uptime
   - Error Rates
   - Key Performance Indicators

2. **API Performance**
   - Request Rate
   - Request Duration
   - Error Rate by Endpoint
   - Status Code Distribution

3. **Database Performance**
   - Query Response Time
   - Connection Pool Status
   - Error Rate
   - Query Volume

4. **Trading Operations**
   - Order Volume
   - Order Processing Time
   - Success/Failure Rate
   - Webhook Processing Status

5. **Risk Management**
   - Risk Check Volume
   - Violation Rate
   - Rule Execution Time
   - Violations by Rule Type

6. **System Resources**
   - CPU Usage
   - Memory Usage
   - Disk Usage
   - Network Traffic

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

## Alerting Configuration

### Prometheus Alert Rules

Sample Prometheus alert rules for monitoring Viewzenix1:

```yaml
groups:
- name: viewzenix1_alerts
  rules:
  - alert: ViewzenixHealthCritical
    expr: viewzenix1_health_status == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Viewzenix1 health status critical"
      description: "The Viewzenix1 application has been reporting unhealthy status for 5 minutes."

  - alert: ViewzenixHighErrorRate
    expr: rate(viewzenix1_http_requests_total{status_code=~"5.."}[5m]) / rate(viewzenix1_http_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate on Viewzenix1"
      description: "More than 5% of requests are resulting in 5xx errors over the last 2 minutes."

  - alert: ViewzenixDatabaseLatency
    expr: histogram_quantile(0.95, viewzenix1_db_query_duration_seconds_bucket) > 0.5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High database latency"
      description: "95% of database queries are taking more than 500ms."
```

## Troubleshooting Runbooks

### API Health Check Failures

If the health check endpoint returns `degraded` or `unhealthy`:

1. **Check Database Connectivity**
   - Verify database credentials in configuration
   - Check database server is running
   - Ensure network connectivity to database
   - Check for database lock contention

2. **Broker Integration Issues**
   - Verify broker API credentials
   - Check broker service status page
   - Ensure network connectivity to broker API
   - Verify correct configuration in `config/broker.yaml`

3. **Webhook System Failures**
   - Check webhook logs in `/logs/webhooks.log`
   - Verify endpoint configuration
   - Check webhook authentication settings
   - Ensure proper validation schema is in place

4. **Risk Management Service Issues**
   - Check risk management service logs
   - Verify rule configuration in `config/risk_rules.yaml`
   - Check database tables for risk management
   - Restart risk management service if needed

5. **Disk Space Warnings**
   - Check available disk space with `df -h`
   - Remove old log files in `/logs/archive/`
   - Clear temporary files in `/tmp/viewzenix1/`
   - Consider increasing available storage if recurrent

### Connection Refused Errors

If clients experience "Connection refused" errors when accessing the API:

1. **Check Service Status**
   - Verify the service is running: `systemctl status viewzenix1-api`
   - Check process list: `ps aux | grep viewzenix1`
   - Restart if necessary: `systemctl restart viewzenix1-api`

2. **Check Port Binding**
   - Verify the service is binding to the correct port: `netstat -tulpn | grep 5000`
   - Check for port conflicts
   - Verify firewall rules: `ufw status` or `iptables -L`

3. **Check Environment Configuration**
   - Verify the correct host binding in `.env` or configuration
   - Check for syntax errors in application startup files
   - Verify correct environment variables are set

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