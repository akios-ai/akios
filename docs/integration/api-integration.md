# API Integration Guide
**Document Version:** 1.2.2  
**Date:** 2026-02-23  

**Connect AKIOS workflows with external APIs and services**

This guide covers integrating AKIOS with REST APIs, webhooks, databases, and third-party services for automated data processing and system integration.

## Quick Start

```bash
# Initialize project
./akios init api-integration
cd api-integration

# Copy sample data
python src/akios/templates/samples/copy_samples.py batch-processing

# Run batch processing workflow (demonstrates local data processing)
./akios run templates/batch_processing.yml
```

**V1.0 note:** `batch_processing.yml` demonstrates local multi-file AI analysis. API integration capabilities are available through custom workflows.

## HTTP Agent Capabilities

AKIOS provides a secure HTTP agent for API interactions:

- **Automatic PII redaction** in requests/responses
- **Rate limiting** (10 requests/minute)
- **SSL/TLS validation** required
- **Timeout protection** (30 seconds default)
- **Audit logging** of all API calls

## REST API Integration

### Basic API Call

```yaml
name: "API Data Fetch"
description: "Fetch data from REST API"

steps:
  - step: "fetch_user_data"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/users/123"
      headers:
        Authorization: "Bearer {{API_TOKEN}}"
        Accept: "application/json"
```

### API Data Processing

```yaml
name: "API Data Enrichment"
description: "Fetch and enrich data with AI"

steps:
  - step: "get_raw_data"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.company.com/customers"
      params:
        limit: 10
        status: "active"

  - step: "enrich_data"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Analyze these customer records and provide insights:

        {{get_raw_data.content}}

        Focus on:
        1. Customer segmentation
        2. Purchase patterns
        3. Retention recommendations

  - step: "store_insights"
    agent: "filesystem"
    action: "write"
    config:
      allowed_paths: ["./data/output"]
    parameters:
      path: "./data/output/customer_insights.txt"
      content: "{{enrich_data.content}}"
```

## Webhook Integration

### Receiving Webhooks

```yaml
name: "Webhook Processor"
description: "Process incoming webhook data"

steps:
  - step: "process_webhook"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Process this webhook payload and generate a response:

        Webhook data: {{webhook_data}}

        Actions needed:
        1. Validate the data
        2. Extract key information
        3. Generate appropriate response
```

### Sending Webhooks

```yaml
name: "Webhook Notifications"
description: "Send webhook notifications on workflow completion"

steps:
  - step: "analyze_data"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: "Analyze this data: {{input_data}}"

  - step: "send_notification"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://webhook.site/your-webhook-url"
      json:
        event: "analysis_complete"
        workflow_id: "{{workflow_id}}"
        result_summary: "{{analyze_data.content|truncate(200)}}"
        timestamp: "{{timestamp}}"
```

## Database Integration

### REST API Databases

```yaml
name: "Database API Integration"
description: "Read from and write to database via REST API"

steps:
  - step: "fetch_records"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.database.com/records"
      params:
        table: "customers"
        limit: 100

  - step: "process_records"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: "Process these records: {{fetch_records.content}}"

  - step: "update_database"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://api.database.com/records/update"
      json:
        table: "customers"
        updates: "{{process_records.content}}"
```

### GraphQL Integration

```yaml
name: "GraphQL API Integration"
description: "Query GraphQL APIs with complex data fetching"

steps:
  - step: "graphql_query"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://api.example.com/graphql"
      json:
        query: |
          {
            users(limit: 10) {
              id
              name
              email
              posts {
                title
                content
              }
            }
          }
      headers:
        Content-Type: "application/json"
```

## OAuth and Authentication

### Bearer Token Authentication

```yaml
name: "OAuth API Integration"
description: "Use OAuth tokens for API authentication"

steps:
  - step: "refresh_token"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://auth.example.com/oauth/token"
      data:
        grant_type: "refresh_token"
        refresh_token: "{{REFRESH_TOKEN}}"
        client_id: "{{CLIENT_ID}}"
        client_secret: "{{CLIENT_SECRET}}"

  - step: "api_call"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/data"
      headers:
        Authorization: "Bearer {{refresh_token.access_token}}"
```

### API Key Authentication

```yaml
name: "API Key Integration"
description: "Use API keys for service authentication"

steps:
  - step: "authenticated_request"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.service.com/data"
      headers:
        X-API-Key: "{{API_KEY}}"
        Accept: "application/json"
```

## Error Handling and Retry Logic

### Robust API Integration

```yaml
name: "Reliable API Integration"
description: "Handle API failures gracefully"

steps:
  - step: "api_call_with_retry"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.unreliable.com/data"
      timeout: 10
    retry:
      max_attempts: 3
      backoff_seconds: 2
      retry_on_status: [500, 502, 503, 504]

  - step: "fallback_processing"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        API call failed. Generate fallback response.

        Error: {{api_call_with_retry.error}}
        Attempted URL: {{api_call_with_retry.url}}
```

### Circuit Breaker Pattern

```yaml
name: "Circuit Breaker API Calls"
description: "Prevent cascading failures"

steps:
  - step: "check_service_health"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/health"
      timeout: 5

  - step: "conditional_api_call"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/data"
      skip_if: "{{check_service_health.status_code != 200}}"
```

## Rate Limiting and Throttling

### Respecting API Limits

```yaml
name: "Rate Limited API Processing"
description: "Process data while respecting API rate limits"

steps:
  - step: "batch_api_calls"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "sleep"
      args: ["1"]  # Rate limit: 1 call per second

  - step: "api_call_1"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/endpoint1"

  - step: "delay_between_calls"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "sleep"
      args: ["1"]

  - step: "api_call_2"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/endpoint2"
```

## Data Transformation and Mapping

### API Response Processing

```yaml
name: "API Response Transformation"
description: "Transform API responses into desired format"

steps:
  - step: "fetch_data"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/data"

  - step: "transform_response"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Transform this API response into a standardized format:

        Raw response: {{fetch_data.content}}

        Required output format:
        {
          "records": [...],
          "metadata": {...},
          "processed_at": "..."
        }

        Return only valid JSON.
```

## Monitoring and Alerting

### API Health Monitoring

```yaml
name: "API Health Monitoring"
description: "Monitor API endpoints and send alerts"

steps:
  - step: "health_check"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/health"
      timeout: 10

  - step: "send_alert_if_down"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://alerts.company.com/webhook"
      json:
        alert: "API Down"
        service: "api.example.com"
        status_code: "{{health_check.status_code}}"
        response_time: "{{health_check.duration}}"
      skip_if: "{{health_check.status_code == 200}}"
```

## Security Best Practices

### PII Protection

```yaml
name: "Secure API Integration"
description: "API integration with automatic PII protection"

steps:
  - step: "secure_api_call"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://api.example.com/process"
      json:
        user_data: "Contains PII: email=user@example.com, phone=555-1234"
        # PII will be automatically redacted in logs and responses
```

### Certificate Validation

```yaml
name: "Secure HTTPS Integration"
description: "Enforce SSL/TLS certificate validation"

steps:
  - step: "secure_api_call"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://secure-api.example.com/data"
      # SSL verification is always enabled
      verify_ssl: true
```

## Performance Optimization

### Concurrent API Calls

```yaml
name: "Parallel API Processing"
description: "Make multiple API calls concurrently"

steps:
  - step: "parallel_calls"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "parallel"
      args: ["--no-notice", "curl", "-s", "https://api.example.com/data/{}", "::: {1..10}"]
```

### Response Caching

```yaml
name: "Cached API Responses"
description: "Cache API responses to reduce redundant calls"

steps:
  - step: "cached_api_call"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://api.example.com/static-data"
      cache_ttl: 3600  # Cache for 1 hour
```

## Common Integration Patterns

### ETL Pipeline

```yaml
name: "API-based ETL Pipeline"
description: "Extract, Transform, Load data via APIs"

steps:
  - step: "extract"
    agent: "http"
    action: "get"
    config: {}
    parameters:
      url: "https://source-api.com/data"

  - step: "transform"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: "Transform this data: {{extract.content}}"

  - step: "load"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://destination-api.com/ingest"
      json: "{{transform.content}}"
```

### Webhook to API Bridge

```yaml
name: "Webhook to API Bridge"
description: "Receive webhooks and forward to APIs"

steps:
  - step: "receive_webhook"
    agent: "filesystem"
    action: "read"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/webhook_payload.json"

  - step: "process_and_forward"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://target-api.com/webhook"
      json: "{{receive_webhook.content}}"
```

## Troubleshooting

### Common API Integration Issues

**SSL Certificate Errors**
- Ensure certificates are valid and not expired
- Check system certificate store
- Use `verify_ssl: false` only for testing (not recommended for production)

**Rate Limiting**
- Implement exponential backoff
- Use API key rotation
- Cache responses when possible

**Timeout Errors**
- Increase timeout values for slow APIs
- Implement retry logic
- Break large requests into smaller chunks

**Authentication Failures**
- Verify API keys and tokens
- Check token expiration
- Ensure correct authentication headers

## Next Steps

- Explore [Document Processing Guide](document-processing.md) for file-based workflows
- Check [Troubleshooting Guide](../troubleshooting.md) for common issues
- Review [Best Practices](../best-practices.md) for optimization tips
- See [Developer API Reference](../api-reference.md) for programmatic integration
