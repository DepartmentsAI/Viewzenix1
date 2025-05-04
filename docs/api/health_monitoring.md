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
  "timestamp": "2025-05-08T12:34:56.789Z",
  "uptime_seconds": 3600,
  "database": {
    "connected": true,
    "status": "connected",
    "latency_ms": 15
  },
  "system_info": {
    "python_version": "3.9.10",
    "platform": "Linux-5.10.0-x86_64",
    "environment": "production"
  },
  "version": "1.0.0"
}
```

#### Status Codes

- `200 OK`: Application is running (even if in degraded state)
- `500 Internal Server Error`: Application has critical issues

### Detailed Health Check

**Endpoint:** `GET /api/health/detailed`

Returns detailed information about the status of various application components. This endpoint is designed for in-depth monitoring and diagnostics.

#### Response Format

```json
{
  "status": "healthy", // or "degraded"
  "timestamp": "2025-05-08T12:34:56.789Z",
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
      "last_webhook_received": "2025-05-08T12:30:00.000Z"
    },
    "risk_management": {
      "operational": true,
      "status": "active"
    },
    "disk_space": {
      "sufficient": true,
      "available_gb": 75,
      "total_gb": 100,
      "percent_used": 25.0
    }
  }
}
```

#### Status Codes

- `200 OK`: Application is running (even if in degraded state)
- `500 Internal Server Error`: Application has critical issues

## Integration with Monitoring Systems

### Prometheus Integration

The health check endpoints can be scraped by Prometheus using the following configuration:

```yaml
scrape_configs:
  - job_name: 'viewzenix1'
    metrics_path: '/api/health'
    scrape_interval: 15s
    static_configs:
      - targets: ['viewzenix1:5000']
```

For more detailed metrics, you can use the Prometheus client library which is already integrated with the application.

### Alert Configuration Examples

#### Grafana Alerting

1. **Service Health Alert**:
   - Query: `rate(http_request_duration_seconds_count{path="/api/health",status!="200"}[5m]) > 0`
   - Condition: When request errors occur for the health endpoint
   - Severity: critical

2. **Database Connection Alert**:
   - Custom query using JSON parsing to check database status
   - Condition: When database status is not "connected"
   - Severity: critical

#### Prometheus AlertManager

```yaml
groups:
- name: viewzenix1-alerts
  rules:
  - alert: InstanceDown
    expr: up{job="viewzenix1"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Instance {{ $labels.instance }} down"
      description: "{{ $labels.instance }} has been down for more than 1 minute."
  
  - alert: HighErrorRate
    expr: rate(http_request_duration_seconds_count{status=~"5.."}[5m]) / rate(http_request_duration_seconds_count[5m]) > 0.01
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "More than 1% of requests are failing with 5xx errors."
```

## Best Practices for Monitoring

1. **Regular Polling**: Poll the `/api/health` endpoint every 15-30 seconds for basic monitoring.
2. **Detailed Checks**: Poll the `/api/health/detailed` endpoint every 1-5 minutes for in-depth monitoring.
3. **Alert Thresholds**:
   - Set immediate alerts for complete service outages
   - Set delayed alerts (2-5 minutes) for degraded performance or component failures
4. **Dashboard Visualization**: Create dashboards that display component health status, response times, and error rates.
5. **Historical Trending**: Store health metrics to analyze performance trends over time.

## Runbook for Common Issues

### Database Connection Failures

If the database connection is reported as down:

1. Check database server status
2. Verify network connectivity between application and database
3. Check database credentials and connection string
4. Inspect database logs for errors
5. Restart database service if necessary

### Broker Service Disconnections

If the broker service is reported as disconnected:

1. Verify API keys and credentials
2. Check for broker service maintenance or outages
3. Inspect network connectivity to broker API endpoints
4. Review broker-specific logs for error details

### Disk Space Warnings

If disk space is reported as insufficient:

1. Identify largest files and directories using `du -h --max-depth=1 /path/to/app`
2. Check and rotate log files
3. Clear temporary files and caches
4. Expand disk space if necessary 