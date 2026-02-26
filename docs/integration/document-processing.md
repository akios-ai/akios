# Document Processing Integration Guide
**Document Version:** 1.2.1  
**Date:** 2026-02-23  

**Process documents with AI-powered analysis and insights**

This guide shows how to integrate AKIOS for automated document processing workflows, including text extraction, analysis, and structured data generation.

## Quick Start

```bash
# Initialize project
./akios init my-doc-project
cd my-doc-project

# Copy sample document
python src/akios/templates/samples/copy_samples.py document-analysis

# Run document analysis
./akios run templates/document_ingestion.yml
```

## Supported Document Types

AKIOS supports multiple document formats with automatic text extraction:

- **PDF files**: Native PDF parsing with fallback to OCR
- **Word documents**: DOCX format with rich text preservation
- **Text files**: Direct processing with encoding detection
- **Images**: OCR processing for scanned documents

## Basic Document Processing

### 1. Prepare Your Documents

Place documents in the `data/input` directory:

```
my-doc-project/
├── data/
│   ├── input/
│   │   ├── contract.pdf
│   │   ├── report.docx
│   │   └── notes.txt
│   └── output/
```

### 2. Configure Workflow

Create a `workflow.yml` file:

```yaml
name: "Document Analysis Pipeline"
description: "Extract and analyze documents with AI insights"

steps:
  - step: "extract_contract"
    agent: "filesystem"
    action: "read"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/contract.pdf"

  - step: "analyze_contract"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Analyze this contract and extract:
        1. Key parties involved
        2. Important dates and deadlines
        3. Financial terms
        4. Risk factors

        Contract text:
        {{extract_contract.content}}
```

### 3. Execute Workflow

```bash
# Set up API keys
export GROK_API_KEY="your-key-here"

# Run the workflow
./akios run workflow.yml --verbose

# Check results
ls -la data/output/
cat data/output/run_*/contract_analysis.txt
```

## Advanced Document Processing

### Batch Processing Multiple Documents

```yaml
name: "Batch Document Analysis"
description: "Process multiple documents in parallel"

steps:
  - step: "list_documents"
    agent: "filesystem"
    action: "list"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input"
      pattern: "*.pdf"

  - step: "process_batch"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "find"
      args: ["./data/input", "-name", "*.pdf", "-exec", "akios", "run", "templates/document_ingestion.yml", "--input-file", "{}", ";"]
```

### Document Classification and Routing

```yaml
name: "Smart Document Router"
description: "Automatically classify and route documents"

steps:
  - step: "read_document"
    agent: "filesystem"
    action: "read"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/new_document.pdf"

  - step: "classify_document"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Classify this document into one category:
        - legal_contract
        - financial_report
        - technical_spec
        - correspondence

        Document: {{read_document.content}}

        Respond with only the category name.

  - step: "route_document"
    agent: "tool_executor"
    action: "run"
    config: {}
    parameters:
      command: "mv"
      args: ["./data/input/new_document.pdf", "./data/input/{{classify_document.content}}/"]
```

## PII Detection and Redaction

AKIOS automatically detects and redacts sensitive information:

```yaml
name: "PII-Safe Document Processing"
description: "Process documents with automatic PII protection"

steps:
  - step: "analyze_with_pii_protection"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Analyze this document for business insights.
        Note: All PII has been automatically redacted for privacy.

        Document content:
        {{read_document.content}}
```

## Integration with External Systems

### Webhook Notifications

```yaml
name: "Document Processing with Notifications"
description: "Process documents and send webhook notifications"

steps:
  - step: "process_document"
    agent: "filesystem"
    action: "read"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/document.pdf"

  - step: "send_webhook"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://api.company.com/webhooks/document-processed"
      json:
        document_id: "doc_123"
        status: "processed"
        timestamp: "{{process_document.timestamp}}"
```

### Database Integration

```yaml
name: "Document Processing with Database Storage"
description: "Extract document data and store in database"

steps:
  - step: "extract_data"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        Extract structured data from this document as JSON:
        - customer_name
        - invoice_number
        - amount
        - due_date

        Document: {{read_document.content}}

        Return only valid JSON.

  - step: "store_in_database"
    agent: "http"
    action: "post"
    config: {}
    parameters:
      url: "https://api.database.com/insert"
      json: "{{extract_data.content}}"
```

## Error Handling and Retry Logic

```yaml
name: "Robust Document Processing"
description: "Handle errors gracefully with retry logic"

steps:
  - step: "safe_read"
    agent: "filesystem"
    action: "read"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/document.pdf"

  - step: "analyze_with_retry"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: "Analyze this document: {{safe_read.content}}"
      max_tokens: 1000
    retry:
      max_attempts: 3
      backoff_seconds: 5
```

## Performance Optimization

### Large Document Handling

```yaml
name: "Efficient Large Document Processing"
description: "Process large documents with memory optimization"

steps:
  - step: "check_file_size"
    agent: "filesystem"
    action: "stat"
    config:
      allowed_paths: ["./data/input"]
    parameters:
      path: "./data/input/large_document.pdf"

  - step: "conditional_processing"
    agent: "llm"
    action: "complete"
    config: {}
    parameters:
      prompt: |
        {% if check_file_size.size > 1000000 %}
        This is a large document ({{check_file_size.size}} bytes).
        Provide a high-level summary only.
        {% else %}
        Provide detailed analysis.
        {% endif %}

        Document: {{read_document.content}}
```

## Monitoring and Auditing

AKIOS provides comprehensive audit trails for document processing:

```bash
# View audit log
./akios audit view --format json

# Export audit for compliance
./akios audit export --task latest --format json --output doc_audit_2026.json
```

## Best Practices

### 1. File Organization
```
data/
├── input/
│   ├── pending/     # Documents waiting processing
│   ├── processed/   # Successfully processed
│   └── failed/      # Failed processing
├── output/
│   ├── summaries/   # AI-generated summaries
│   ├── extracts/    # Extracted data
│   └── reports/     # Analysis reports
```

### 2. Error Handling
- Always check file existence before processing
- Use try/catch blocks for API calls
- Implement retry logic for transient failures
- Log errors for debugging

### 3. Performance
- Process documents in batches when possible
- Use caching for repeated operations
- Monitor memory usage with large files
- Consider document size limits

### 4. Security
- Validate file paths and types
- Use allowed_paths restrictions
- Enable PII redaction for sensitive documents
- Audit all document access

## Troubleshooting

### Common Issues

**"File not found" errors**
- Ensure documents are in `data/input/`
- Check file permissions
- Verify allowed_paths configuration

**"API rate limit exceeded"**
- Implement retry logic with backoff
- Use multiple API keys if available
- Consider batch processing

**"Memory errors with large files"**
- Check file size before processing
- Use streaming for very large documents
- Consider splitting large files

**"PII redaction failures"**
- Ensure security validation is enabled
- Check document encoding
- Review audit logs for redaction details

## Next Steps

- Explore [API Integration Guide](api-integration.md) for external system connections
- Check [Troubleshooting Guide](../troubleshooting.md) for common issues
- Review [Best Practices](../best-practices.md) for optimization tips
