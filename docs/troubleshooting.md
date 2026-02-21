# Troubleshooting Guide
**Document Version:** 1.0  
**Date:** 2026-01-25  

**Resolve common AKIOS issues and configuration problems**

This guide covers frequently encountered issues, their causes, and step-by-step solutions for AKIOS V1.0.

## Quick Diagnosis

Run the diagnostic command to check system health:

```bash
# Check overall system status
./akios status

# Enable debug logging for detailed troubleshooting
./akios --debug status

# View recent audit events
./akios logs --limit 10

# Check configuration validity (implicit in status)
./akios status
```

### Debug Logging

For advanced troubleshooting, enable debug logging to see detailed internal operations:

```bash
# Enable debug logging for any command
./akios --debug status
./akios --debug run workflow.yml
./akios --debug audit export

# Or set environment variable for all commands
export AKIOS_DEBUG=1
./akios status
./akios run workflow.yml
```

Debug logs provide detailed information about:
- Configuration loading and validation
- Workflow execution steps
- Agent operations and API calls
- Security checks and audit logging
- Error conditions and recovery actions

## Installation Issues

### Hybrid Distribution Troubleshooting

**AKIOS v1.0 supports three installation methods - use this guide to troubleshoot each:**

#### **Pip Package Issues**

**Symptoms:**
- Import errors after pip install
- Security features not working on non-Linux platforms

**Solutions:**

1. **Verify pip installation:**
   ```bash
   pip show akios
   pip list | grep akios
   ```

2. **Check Python version compatibility:**
   ```bash
   python3 --version  # Must be 3.8+
   which python3
   ```

3. **Reinstall with proper permissions:**
   ```bash
   pip uninstall akios
   pip install --user akios  # Or use virtualenv
   ```

#### **Docker Issues**

**Symptoms:**
- `docker: command not found`
- Container exits immediately
- Volume mounting permissions issues

**Solutions:**

1. **Verify Docker installation:**
   ```bash
   docker --version
   docker run hello-world
   ```

2. **Check Docker permissions:**
   ```bash
   # Linux
   groups | grep docker
   sudo usermod -aG docker $USER

   # macOS/Windows: Ensure Docker Desktop is running
   ```

3. **Fix volume permissions:**
   ```bash
   # Ensure project directory has proper permissions
   ls -la /path/to/project
   ```

#### **Docker Image Appears Outdated**

**Symptoms:**
- Commands run but recent image updates do not show up

**Solution:**
```bash
# Force a pull before running commands
AKIOS_FORCE_PULL=1 ./akios status
```

### "Command not found" after installation

**Symptoms:**
- `akios: command not found`
- `python -m akios` works but `./akios` doesn't

**Causes:**
- Docker wrapper script not executable
- PATH issues
- Missing Python dependencies

**Solutions:**

1. **Make script executable:**
   ```bash
   chmod +x akios
   ```

2. **Check Python installation:**
   ```bash
   python3 --version  # Should be 3.8+
   pip list | grep akios
   ```

3. **Reinstall if needed:**
   ```bash
   # Ubuntu 24.04+ users: Use pipx
   pipx uninstall akios
   pipx install akios

   # Ubuntu 20.04/22.04 and other systems:
   pip uninstall akios
   pip install akios
   ```

### Import Errors

**Symptoms:**
- `ModuleNotFoundError: No module named 'akios'`
- Import errors in Python scripts

**Causes:**
- Incomplete installation
- Virtual environment issues
- Python path problems

**Solutions:**

1. **Check installation:**
   ```bash
   pip show akios
   # Should show location and version
   ```

2. **Reinstall in virtual environment:**
   ```bash
   # Ubuntu 24.04+ users: Use pipx (recommended)
   pipx install akios

   # Alternative: Virtual environment (works on all systems)
   python3 -m venv akios_env
   source akios_env/bin/activate
   pip install akios
   ```

3. **Check Python path:**
   ```python
   import sys
   print(sys.path)
   # Ensure akios package is in path
   ```

## Configuration Issues

### Environment Variable Problems

**Symptoms:**
- "API key not found" errors
- Mock mode not working
- Configuration not loading

**Causes:**
- `.env` file corruption
- Incorrect variable names
- File permission issues

**Solutions:**

1. **Check .env file:**
   ```bash
   cat .env
   # Should contain valid key=value pairs
   ```

2. **Validate .env format:**
   ```bash
   # Correct format:
   AKIOS_LLM_PROVIDER=grok
   AKIOS_LLM_MODEL=grok-3
   GROK_API_KEY=your-key-here

   # Incorrect (missing =):
   AKIOS_LLM_PROVIDER grok
   ```

3. **Fix common corruptions:**
   ```bash
   # If you see concatenated values like:
   # AKIOS_LLM_PROVIDER=grokopenai
   # AKIOS_LLM_MODEL=grok-3gpt-4

   # Fix by editing .env manually:
   AKIOS_LLM_PROVIDER=grok
   AKIOS_LLM_MODEL=grok-3
   GROK_API_KEY=your-actual-key
   ```

4. **Use setup wizard:**
   ```bash
   ./akios setup --force
   ```

### Configuration File Errors

**Symptoms:**
- "Invalid configuration" messages
- Missing required fields
- YAML parsing errors

**Causes:**
- Malformed YAML syntax
- Missing required fields
- Incorrect indentation

**Solutions:**

1. **Validate YAML syntax:**
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **Check required fields:**
   ```yaml
   # Minimal valid config.yaml:
   mock_llm: false
   audit_export_format: "json"
   agents:
     filesystem:
       allowed_paths: ["./data/input", "./data/output"]
     http:
       network_access_allowed: true
     llm:
       max_tokens_per_call: 1000
   ```

3. **Fix indentation:**
   ```yaml
   # Correct:
   agents:
     filesystem:
       allowed_paths:
         - "./data/input"
         - "./data/output"

   # Incorrect:
   agents:
     filesystem:
       allowed_paths: ./data/input, ./data/output
   ```

### LLM Provider/Model Validation Errors

**Symptoms:**
- "Model 'xyz' is not valid for provider 'abc'" errors
- "Unknown LLM provider" messages
- Configuration fails during startup

**Causes:**
- Incompatible provider-model combinations
- Typo in provider or model name
- Using unsupported models

**Solutions:**

1. **Check supported combinations:**
   ```bash
   # OpenAI models
   AKIOS_LLM_PROVIDER=openai AKIOS_LLM_MODEL=gpt-4
   AKIOS_LLM_PROVIDER=openai AKIOS_LLM_MODEL=gpt-4o-mini

   # Anthropic models
   AKIOS_LLM_PROVIDER=anthropic AKIOS_LLM_MODEL=claude-3.5-haiku

   # Grok models
   AKIOS_LLM_PROVIDER=grok AKIOS_LLM_MODEL=grok-3

   # Mistral models
   AKIOS_LLM_PROVIDER=mistral AKIOS_LLM_MODEL=mistral-large

   # Gemini models
   AKIOS_LLM_PROVIDER=gemini AKIOS_LLM_MODEL=gemini-1.5-pro
   ```

2. **Common mistakes:**
   ```bash
   # ❌ Wrong: OpenAI doesn't have grok-3
   AKIOS_LLM_PROVIDER=openai AKIOS_LLM_MODEL=grok-3

   # ❌ Wrong: Invalid provider
   AKIOS_LLM_PROVIDER=invalid AKIOS_LLM_MODEL=gpt-4

   # ✅ Correct: Use compatible combinations
   AKIOS_LLM_PROVIDER=grok AKIOS_LLM_MODEL=grok-3
   ```

3. **Case-insensitive matching:**
   ```bash
   # ✅ These all work (case doesn't matter)
   AKIOS_LLM_MODEL=GPT-4
   AKIOS_LLM_MODEL=gpt-4
   AKIOS_LLM_MODEL=Gpt-4
   ```

4. **Use setup wizard for safe configuration:**
   ```bash
   ./akios setup --force
   # Wizard only shows valid models for chosen provider
   ```

5. **JSON mode for automation:**
   ```bash
   # For scripts/CI that need structured error output
   AKIOS_JSON_MODE=1 ./akios status
   # Returns: {"error": true, "message": "...", "type": "configuration_error"}
   ```

## Workflow Execution Issues

### Template Not Found

**Symptoms:**
- "Template not found" errors
- Workflow fails to load

**Causes:**
- Incorrect template name
- Missing template files
- Docker image mismatch

**Solutions:**

1. **List available templates:**
   ```bash
   ./akios templates list
   ```

2. **Check template exists:**
   ```bash
   ls templates/
   ```

3. **Update Docker image:**
   ```bash
   # Pull latest image
   docker pull akiosai/akios:latest

   # Or rebuild if developing
   ./push-to-docker.sh
   ```

### Agent Execution Failures

#### Filesystem Agent Issues

**Symptoms:**
- "Path not allowed" errors
- File read/write failures

**Causes:**
- Path not in allowed_paths
- File permissions
- Invalid paths

**Solutions:**

1. **Check allowed paths:**
   ```yaml
   # In config.yaml
   agents:
     filesystem:
       allowed_paths:
         - "./data/input"
         - "./data/output"
         - "./workflows"
   ```

2. **Verify file permissions:**
   ```bash
   ls -la data/input/
   # Files should be readable
   ```

3. **Use absolute paths:**
   ```yaml
   parameters:
     path: "./data/input/document.pdf"  # Preferred
     # Avoid: /absolute/path/outside/project
   ```

#### LLM Agent Issues

**Symptoms:**
- "API key missing" errors
- "Rate limit exceeded"
- Mock mode not working

**Causes:**
- Missing API keys
- Invalid key format
- Network issues
- Model not supported

**Solutions:**

1. **Check API keys:**
   ```bash
   # Verify environment variables
   echo $GROK_API_KEY
   echo $AKIOS_LLM_PROVIDER
   ```

2. **Test API connectivity:**
   ```bash
   curl -H "Authorization: Bearer $GROK_API_KEY" \
        https://api.x.ai/v1/models
   ```

3. **Use mock mode for testing:**
   ```yaml
   # In config.yaml
   mock_llm: true
   ```

4. **Check model support:**
   ```yaml
   # Supported models:
   model: "grok-3"        # Grok
   model: "gpt-4"         # OpenAI
   model: "claude-3-sonnet-20240229"  # Anthropic
   ```

#### HTTP Agent Issues

**Symptoms:**
- Network connection errors
- SSL certificate failures
- Timeout errors

**Causes:**
- Network access disabled
- Invalid URLs
- Firewall blocking
- SSL certificate issues

**Solutions:**

1. **Enable network access:**
   ```yaml
   # In config.yaml
   agents:
     http:
       network_access_allowed: true
   ```

2. **Check URL validity:**
   ```bash
   curl -I https://api.example.com/endpoint
   ```

3. **Test SSL certificates:**
   ```bash
   openssl s_client -connect api.example.com:443
   ```

4. **Increase timeouts:**
   ```yaml
   parameters:
     timeout: 60  # Increase from default 30
   ```

### Workflow Validation Errors

**Symptoms:**
- "Workflow validation failed" messages
- Schema validation errors
- Missing required fields

**Causes:**
- Invalid YAML structure
- Missing required fields
- Incorrect agent/action names

**Solutions:**

1. **Validate workflow syntax:**
   ```bash
   python3 -c "
   import yaml
   from akios.core.runtime.workflow.parser import parse_workflow
   try:
       wf = parse_workflow('workflow.yml')
       print('Workflow is valid')
   except Exception as e:
       print(f'Validation error: {e}')
   "
   ```

2. **Check required fields:**
   ```yaml
   # Valid workflow structure:
   name: "Workflow Name"
   description: "Workflow description"
   steps:
     - step: "step_id"
       agent: "filesystem"  # filesystem, http, llm, tool_executor
       action: "read"       # agent-specific actions
       config: {}           # Required field
       parameters:
         key: "value"
   ```

3. **Use schema validation:**
   ```bash
   ./akios run workflow.yml --validate-only
   ```

## Security Issues

### Startup Security Failures

**Symptoms:**
- "SECURITY VALIDATION FAILED" messages
- Application won't start

**Causes:**
- Not running on Linux
- Missing seccomp support
- Kernel too old
- Container security issues

**Solutions:**

1. **Check platform:**
   ```bash
   uname -a
   # Must be Linux
   ```

2. **Verify seccomp:**
   ```bash
   grep -i seccomp /proc/config.gz
   # Should show CONFIG_SECCOMP=y
   ```

3. **Check kernel version:**
   ```bash
   uname -r
   # Should be 3.17+ for seccomp support, 4.5+ for cgroups v2
   ```

4. **Container considerations:**
   ```bash
   # In Docker containers, security is policy-based
   # Some validations are relaxed but still enforced
   ```

### "Trace/breakpoint trap" / SIGTRAP When Running with Sudo

**Symptoms:**
- `sudo akios run` crashes with "Trace/breakpoint trap (core dumped)"
- Exit code 133 (128 + 5 = SIGTRAP)

**Cause:** Seccomp BPF filter rejecting essential syscalls. Fixed in v1.0.5.

**Solutions:**

1. **Upgrade to v1.0.5+:**
   ```bash
   sudo pip3 install --upgrade akios
   ```

2. **Verify system packages installed:**
   ```bash
   sudo apt-get install libseccomp-dev python3-seccomp
   ```

3. **Test the fix:**
   ```bash
   sudo akios run templates/hello-workflow.yml
   # Should complete without crash
   ```

### PII Redaction Issues

**Symptoms:**
- Sensitive data in logs
- Redaction not working

**Causes:**
- PII detection disabled
- Custom patterns not configured
- Log level too verbose

**Solutions:**

1. **Enable PII redaction:**
   ```yaml
   # In config.yaml
   pii_redaction_enabled: true
   ```

2. **Check audit settings:**
   ```yaml
   audit_enabled: true
   audit_export_format: "json"
   ```

3. **Verify redaction:**
   ```bash
   ./akios audit view | grep -i "redacted"
   ```

## Performance Issues

### Slow Startup

**Symptoms:**
- Long time to start commands
- "Loading..." messages persist

**Causes:**
- Large audit logs
- Complex configurations
- Network connectivity issues

**Solutions:**

1. **Check audit log size:**
   ```bash
   ls -lh data/audit/audit_events.jsonl
   # Large files slow startup
   ```

2. **Clear old audit logs:**
   ```bash
   ./akios clean audit --older-than 30d
   ```

3. **Optimize configuration:**
   ```yaml
   # Minimize complex configurations
   mock_llm: true  # For development
   ```

### Memory Issues

**Symptoms:**
- Out of memory errors
- Slow performance with large files

**Causes:**
- Large workflow data
- Memory leaks
- Insufficient RAM

**Solutions:**

1. **Monitor memory usage:**
   ```bash
   ./akios status | grep memory
   ```

2. **Process large files in chunks:**
   ```yaml
   # Use streaming for large files
   parameters:
     stream: true  # If supported by agent
   ```

3. **Increase system memory:**
   ```bash
   free -h
   # Ensure adequate RAM available
   ```

### High CPU Usage

**Symptoms:**
- System slowdown
- High CPU consumption

**Causes:**
- Intensive LLM processing
- Large file operations
- Background processes

**Solutions:**

1. **Check CPU usage:**
   ```bash
   top -p $(pgrep -f akios)
   ```

2. **Use appropriate models:**
   ```yaml
   # Use smaller models for simple tasks
   model: "grok-3"  # Instead of larger models
   ```

3. **Limit concurrent operations:**
   ```yaml
   # Process sequentially rather than parallel
   max_concurrent: 1
   ```

## Docker-Specific Issues

### Workflow Hangs on File Operations

**Symptoms:**
- Workflows get stuck indefinitely during file read/write operations
- Resource limits message appears but workflow doesn't progress
- Occurs primarily on macOS and Windows Docker installations

**Causes:**
- POSIX resource limits (`setrlimit`) can conflict with Docker's cgroup management in virtualized environments
- File I/O operations may hang due to VM filesystem mediation layers
- Audit logging synchronization can block in containerized environments

**Solutions:**

1. **Update Docker Desktop:**
   ```bash
   # Ensure you're using the latest Docker Desktop version
   # This resolves most filesystem mediation issues
   ```

2. **Enable Performance Optimizations:**
   AKIOS v1.0 automatically detects Docker environments and applies performance optimizations:
   - Uses container-native resource limits instead of POSIX fallbacks
   - Optimizes audit logging for containerized filesystems
   - Reduces I/O operations that can hang in virtualized environments

   **Performance Validation Results:**
   - **Docker Startup**: 0.5-0.8s (baseline)
   - **Native Linux Startup**: 0.4-0.5s (10-20% faster)
   - **Memory Usage**: Docker 60-80MB, Native 40-60MB (25-33% less)
   - **All performance targets validated** against identical standards

3. **Verify Container Detection:**
   ```bash
   ./akios status
   # Look for: "🐳 Docker container detected - using Docker's built-in resource limits"
   ```

4. **For Persistent Issues:**
   If hangs continue, disable resource sandboxing for Docker environments:
   ```yaml
   # In config.yaml
   sandbox_enabled: false
   ```
   This uses Docker's built-in container isolation instead of additional POSIX limits.

**Prevention:**
- Use native Linux installation for maximum performance and security
- Keep Docker Desktop updated
- Monitor resource usage with `./akios status`

#### Audit Logging in Docker on macOS & Windows

**Full audit trail is preserved** in normal operation thanks to:

- Memory buffering (events held in RAM, flushed every 100 events)
- tmpfs mount for `/app/audit` (writes happen in ultra-fast in-memory filesystem)

**Extremely rare edge case:**
If the container is **violently killed** (e.g. via Task Manager "End task" on Windows or `docker kill --signal=SIGKILL` / force-quit Docker Desktop) exactly during a flush window, up to the last ~100 audit events could be lost.

**Real-world impact:**
This requires forceful termination at a precise moment — it is **extremely unlikely** in normal use and almost impossible without someone deliberately attacking the Docker runtime itself.

**Recommendation for maximum paranoia / compliance environments:**
Use **native Linux installation** (kernel-level cgroups + seccomp + direct filesystem writes) for absolute audit durability with zero possibility of loss.

All other security guarantees (PII redaction, sandboxing, path/command restrictions, network controls, cost/loop kill-switches) remain **fully active** in Docker on macOS and Windows.

### Image Pull Failures

**Symptoms:**
- "Image not found" errors
- Docker pull failures

**Causes:**
- Network issues
- Authentication problems
- Outdated image tags

**Solutions:**

1. **Check Docker connectivity:**
   ```bash
   docker run hello-world
   ```

2. **Pull specific version:**
   ```bash
   docker pull akiosai/akios:v1.0.9
   ```

3. **Clear Docker cache:**
   ```bash
   docker system prune -a
   ```

### Container Permission Issues

**Symptoms:**
- File access denied in containers
- Volume mount failures

**Causes:**
- Incorrect volume mounts
- File permissions
- SELinux/AppArmor policies

**Solutions:**

1. **Check volume mounts:**
   ```bash
   # Ensure correct mount syntax
   docker run -v $(pwd):/app akiosai/akios:v1.0.9
   ```

2. **Fix file permissions:**
   ```bash
   chmod -R 755 data/
   chown -R $USER:$USER data/
   ```

3. **Check SELinux:**
   ```bash
   # If on SELinux system
   chcon -Rt svirt_sandbox_file_t data/
   ```

## Audit and Logging Issues

### Audit Log Corruption

**Symptoms:**
- "Audit integrity failed" messages
- Unable to read audit logs

**Causes:**
- Disk full
- File system corruption
- Concurrent access issues

**Solutions:**

1. **Check disk space:**
   ```bash
   df -h data/audit/
   ```

2. **Verify integrity:**
   ```bash
   ./akios audit verify
   ```

3. **Repair audit logs:**
   ```bash
   ./akios audit repair
   ```

### Missing Audit Events

**Symptoms:**
- Audit logs incomplete
- Missing workflow executions

**Causes:**
- Audit disabled
- Buffer flushing issues
- Permission problems

**Solutions:**

1. **Enable audit logging:**
   ```yaml
   audit_enabled: true
   ```

2. **Flush buffers:**
   ```bash
   ./akios audit flush
   ```

3. **Check permissions:**
   ```bash
   ls -la data/audit/
   # Should be writable
   ```

## Network and Connectivity Issues

### API Connection Failures

**Symptoms:**
- Timeout errors
- Connection refused
- DNS resolution failures

**Causes:**
- Firewall blocking
- DNS issues
- Network configuration

**Solutions:**

1. **Test connectivity:**
   ```bash
   ping api.x.ai
   curl https://api.x.ai/v1/models
   ```

2. **Check DNS:**
   ```bash
   nslookup api.x.ai
   ```

3. **Verify proxy settings:**
   ```bash
   env | grep -i proxy
   ```

## Getting Help

### Diagnostic Information

Collect diagnostic information for support:

```bash
# System information
uname -a
python3 --version
docker --version

# AKIOS status
./akios status
./akios config validate

# Recent logs
./akios audit view --limit 20 --format json

# Environment check
env | grep AKIOS
```

### Support Resources

1. **Documentation:** Check `docs/` directory
2. **Examples:** Review `templates/` and sample data
3. **Community:** GitHub issues and discussions
4. **Logs:** Enable verbose logging with `--verbose` flag

### Emergency Recovery

For critical issues:

1. **Stop all workflows:**
   ```bash
   pkill -f akios
   ```

2. **Backup data:**
   ```bash
   cp -r data/ data.backup
   ```

3. **Reset configuration:**
   ```bash
   ./akios setup --force
   ```

4. **Clear caches:**
   ```bash
   ./akios clean all
   ```

5. **Reinitialize:**
   ```bash
   rm -rf data/ workflows/
   ./akios init fresh-project
   ```

Remember: AKIOS v1.0 is designed for security-first operation. Most "issues" are actually security protections working correctly. Always verify your configuration against the security requirements before troubleshooting.