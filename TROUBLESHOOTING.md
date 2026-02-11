# AKIOS v1.0.5 – Troubleshooting Guide
**Document Version:** 1.0.5  
**Date:** 2026-02-10  

**Common issues, error codes, and solutions for AKIOS v1.0.5.**

This guide covers the most frequent issues users encounter with AKIOS. If you can't find your issue here, check the [GitHub Issues](https://github.com/akios-ai/akios/issues) or start a [GitHub Discussion](https://github.com/akios-ai/akios/discussions).

## 🚀 Quick Diagnosis

### 1. Check Environment
```bash
# Verify Python version
python3 --version  # Should show 3.8+

# Check Linux kernel
uname -r  # Should show 3.17+ (seccomp-bpf support)

# Verify cgroups v2
stat -fc %T /sys/fs/cgroup/  # Should show "cgroup2fs"

# Check seccomp-bpf
grep CONFIG_SECCOMP_FILTER /boot/config-$(uname -r)  # Should show "=y"
```

### 2. Test Basic Functionality
```bash
# Check installation
akios --version

# Test basic workflow
akios run templates/hello-workflow.yml

# Check audit logs
akios logs
```

### 3. Get System Information
```bash
# Full system diagnostics
akios status
```

## ❌ Common Error Messages

### "Domain not in allowed list: example.com"

**Cause:** HTTP agent attempting to access a domain not in the `allowed_domains` whitelist.

**Solutions:**
1. **Add domain to config.yaml:**
   ```yaml
   network_access_allowed: true
   allowed_domains:
     - example.com
     - api.example.com
   ```

2. **Or use environment variable:**
   ```bash
   export AKIOS_ALLOWED_DOMAINS="example.com,api.example.com"
   akios run workflow.yml
   ```

3. **Check if using subdomain:** `api.example.com` ≠ `example.com` (no wildcard support)

4. **Note:** LLM APIs (OpenAI, Anthropic, etc.) always bypass whitelist — cannot be blocked.

### "Cage down destroyed data but directories not empty"

**Cause:** Filesystem permissions or files locked by another process.

**Solutions:**
1. **Check directory ownership:**
   ```bash
   ls -la audit/ data/output/ data/input/
   sudo chown -R $(whoami):$(whoami) audit/ data/
   ```

2. **Force cleanup manually:**
   ```bash
   rm -rf audit/* data/output/* data/input/*
   ```

3. **Check for locked files:**
   ```bash
   lsof +D audit/
   lsof +D data/
   ```

4. **Verify cage down completed:**
   ```bash
   akios cage status  # Should show RELAXED
   find audit/ data/output/ data/input/ -type f  # Should be empty
   ```

### "AKIOS requires Linux kernel 5.4+ with cgroups v2"

**Cause:** Running on incompatible system or kernel version too old.

**Solutions:**
1. **Check kernel version:**
   ```bash
   uname -r  # Must be 5.4.0 or higher
   ```

2. **Upgrade kernel (Ubuntu/Debian):**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

3. **Check cgroups v2:**
   ```bash
   stat -fc %T /sys/fs/cgroup/
   # Should show "cgroup2fs"
   ```

4. **Enable cgroups v2 at boot:**
   ```bash
   # Add to /etc/default/grub
   GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=1"
   sudo update-grub
   ```

### "Sandbox initialization failed" / "cgroups v2 not available"

**Cause:** cgroups v2 not enabled or supported.

**Solutions:**
1. **Check cgroups version:**
   ```bash
   stat -fc %T /sys/fs/cgroup/
   ```

2. **Enable cgroups v2 (Ubuntu/Debian):**
   ```bash
   sudo apt install cgroup-tools
   echo "kernel.unified_cgroup_hierarchy=1" | sudo tee /etc/sysctl.d/99-cgroup.conf
   sudo sysctl -p /etc/sysctl.d/99-cgroup.conf
   ```

3. **Reboot required:**
   ```bash
   sudo reboot
   ```

### "seccomp-bpf not supported" / "Syscall filtering unavailable"

**Cause:** seccomp-bpf not compiled into kernel.

**Solutions:**
1. **Check kernel config:**
   ```bash
   grep CONFIG_SECCOMP_FILTER /boot/config-$(uname -r)
   # Should show "=y"
   ```

2. **Recompile kernel with seccomp support (advanced):**
   ```bash
   # This requires kernel development setup
   # Consider using a newer Linux distribution instead
   ```

3. **Use newer kernel:**
   ```bash
   # Ubuntu 20.04+ or Fedora 35+ recommended
   lsb_release -a
   ```

### "Trace/breakpoint trap (core dumped)" / SIGTRAP with sudo

**Cause:** Seccomp BPF filter rejecting essential syscalls during `sudo akios run`. Fixed in v1.0.5.

**Solutions:**
1. **Upgrade to v1.0.5+:**
   ```bash
   pip install --upgrade akios
   # Or for system-wide:
   sudo pip3 install --upgrade akios
   ```

2. **Verify fix:**
   ```bash
   sudo akios run templates/hello-workflow.yml
   # Should complete without crash
   ```

3. **If still occurring:** Check that `python3-seccomp` system package is installed:
   ```bash
   sudo apt-get install libseccomp-dev python3-seccomp
   ```

### "Permission denied" / "Cannot access file"

**Cause:** File permissions or path restrictions.

**Solutions:**
1. **Check file permissions:**
   ```bash
   ls -la /path/to/file
   ```

2. **Fix permissions:**
   ```bash
   chmod 644 /path/to/file  # For files
   chmod 755 /path/to/dir   # For directories
   ```

3. **Check if path is allowed:**
   AKIOS only allows access to:
   - `./workflows/`
   - `./templates/`
   - `./data/input/`
   - `./data/output/`

4. **Move file to allowed location:**
   ```bash
   mkdir -p data/input
   mv your-file.txt data/input/
   ```

### "Network access blocked" / "HTTP request failed"

**Cause:** Network access disabled by default.

**Solutions:**
1. **Enable network access in config:**
   ```yaml
   # config.yaml
   network_access_allowed: true
   ```

2. **Check rate limits:**
   HTTP agent limited to 10 requests per minute.

3. **Verify URL format:**
   Only HTTP/HTTPS URLs allowed.

### "Budget exceeded" / "Cost limit reached"

**Cause:** Workflow cost exceeded budget limit.

**Solutions:**
1. **Check current budget:**
   ```bash
   akios status --budget  # Shows budget dashboard with cost breakdown
   ```

2. **Increase budget limit:**
   ```yaml
   # config.yaml
   budget_limit_per_run: 5.0  # $5.00 instead of $1.00
   ```

3. **Reduce token usage:**
   ```yaml
   max_tokens_per_call: 250  # Lower token limit
   ```

4. **Check LLM costs:**
   ```bash
   akios logs --limit 5  # Shows recent API calls and costs
   ```

### "PII redaction failed" / "Redaction error"

**Cause:** PII detection encountered invalid data.

**Solutions:**
1. **Check data format:**
   Ensure input data is valid text/JSON.

2. **Disable PII redaction temporarily:**
   ```yaml
   # config.yaml
   pii_redaction_enabled: false
   ```

3. **Review redacted content:**
   ```bash
   akios logs  # Shows what was redacted
   ```

### "Command not allowed" / "Tool execution blocked"

**Cause:** Attempted to run unauthorized command.

**Solutions:**
1. **Check allowed commands:**
   Tool executor only allows safe commands:
   - `echo`, `cat`, `grep`, `head`, `tail`
   - `wc`, `sort`, `uniq`, `cut`, `tr`
   - `date`, `pwd`, `ls`, `ps`, `df`, `free`

2. **Use allowed alternative:**
   ```bash
   # Instead of: tool_executor run command: "curl"
   # Use: http get url: "https://example.com"
   ```

### "Direct shell execution is not permitted inside the security cage"

**Cause:** Using `--exec` flag with `akios run`. This flag is a security trap that blocks shell-injection attempts.

**Solutions:**
1. **Remove `--exec` from your command:**
   ```bash
   # Wrong:
   akios run workflow.yml --exec "some command"

   # Correct:
   akios run workflow.yml
   ```

2. **Use proper agents instead of shell commands:**
   - Use `http` agent for HTTP requests
   - Use `filesystem` agent for file operations
   - Use `tool_executor` agent for allowed commands

### "HTTP request failed" / "URL not in whitelist" (akios http)

**Cause:** Domain not in `allowed_domains` or cage not active.

**Solutions:**
1. **Add domain to whitelist:**
   ```yaml
   # config.yaml
   network_access_allowed: true
   allowed_domains:
     - api.example.com
   ```

2. **Ensure cage is active:**
   ```bash
   akios cage up
   akios http GET https://api.example.com/data
   ```

3. **Use HTTPS (required):**
   ```bash
   # Wrong: akios http GET http://api.example.com
   # Correct: akios http GET https://api.example.com
   ```

### "Audit log corrupted" / "Integrity check failed"

**Cause:** Audit log file was modified externally.

**Solutions:**
1. **Check file permissions:**
   ```bash
   ls -la audit/
   # Should be owned by akios user
   ```

2. **Verify integrity:**
   ```bash
   akios audit export --format json
   # Will show integrity status
   ```

3. **Restore from backup:**
   If you have audit backups, restore the clean version.

### "Configuration validation failed"

**Cause:** Invalid configuration values or corrupted `.env` file.

**Solutions:**
1. **Use the setup wizard (Recommended):**
   ```bash
   # Automatically fixes most configuration issues
   akios setup --force
   ```

2. **Manual validation:**
   ```bash
   # Check YAML syntax
   python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

   # Validate .env file for corruption
   akios setup --non-interactive  # Shows validation errors
   ```

3. **Common .env corruption fixes:**
   - `grokopenai` → `grok` (concatenated provider names)
   - `tru` → `true` (invalid booleans)
   - Missing required API keys

4. **Reset to defaults:**
   ```bash
   akios init fresh-project  # Creates clean configuration
   cd fresh-project
   akios setup  # Configure with wizard
   ```

Most configuration issues can be resolved using the setup wizard.

## 🔧 Installation Issues

### "pip install akios failed"

**Solutions:**
1. **Check Python version:**
   ```bash
   python3 --version  # Must be 3.8+
   ```

2. **Upgrade pip:**
   ```bash
   pip install --upgrade pip
   ```

3. **Install in virtual environment:**
   ```bash
   python3 -m venv akios-env
   source akios-env/bin/activate
   pip install akios
   ```

### "Module not found" after installation

**Solutions:**
1. **Check virtual environment:**
   ```bash
   which python  # Should show virtual env path
   which akios   # Should show virtual env path
   ```

2. **Reinstall in virtual env:**
   ```bash
   pip uninstall akios
   pip install akios
   ```

3. **Check PATH:**
   ```bash
   echo $PATH
   source ~/.bashrc  # Or your shell config
   ```

## 🔒 Security-Related Issues

### "Sandbox violation" / "Security policy breach"

**Cause:** Workflow attempted forbidden operation.

**Solutions:**
1. **Check what was blocked:**
   ```bash
   akios logs --limit 5
   ```

2. **Modify workflow to avoid blocked operations:**
   - Use allowed filesystem paths
   - Avoid dangerous system calls
   - Stay within resource limits

3. **Adjust security settings (not recommended):**
   ```yaml
   # config.yaml - LESS SECURE
   sandbox_enabled: false  # Only for testing
   ```

### "Process killed" / "Resource limit exceeded"

**Cause:** Workflow exceeded CPU/memory limits.

**Solutions:**
1. **Check resource usage:**
   ```bash
   akios status
   ```

2. **Increase limits:**
   ```yaml
   # config.yaml
   cpu_limit: 0.9      # Allow more CPU
   memory_limit_mb: 512  # Allow more memory
   ```

3. **Optimize workflow:**
   - Reduce concurrent operations
   - Use smaller data sets
   - Add delays between operations

## 📊 Performance Issues

### "Workflow too slow" / "Timeout exceeded"

**Solutions:**
1. **Check system resources:**
   ```bash
   free -h     # Memory
   df -h       # Disk space
   top         # CPU usage
   ```

2. **Optimize configuration:**
   ```yaml
   # config.yaml
   cpu_limit: 0.9      # Allow more CPU
   memory_limit_mb: 512  # Allow more memory
   ```

3. **Check network latency (for HTTP agent):**
   ```bash
   ping -c 3 example.com
   ```

### "High memory usage" / "Out of memory"

**Solutions:**
1. **Reduce memory limits:**
   ```yaml
   memory_limit_mb: 128  # Conservative limit
   ```

2. **Check for memory leaks:**
   ```bash
   akios status  # Shows memory usage
   ```

3. **Use smaller data sets:**
   - Process files in chunks
   - Reduce concurrent operations

## 🔧 Advanced Debugging

### Enable Debug Logging
```yaml
# config.yaml
log_level: "DEBUG"
```

### Check Detailed Status
```bash
akios status  # Shows system information
```

### Examine Audit Logs
```bash
# Last 10 entries
akios logs --limit 10

# Export full audit
akios audit export --format json
```

### Test Individual Agents
```yaml
# Test filesystem agent
- name: "test_fs"
  agent: "filesystem"
  action: "list"
  parameters:
    path: "."

# Test LLM agent (if API key available)
- name: "test_llm"
  agent: "llm"
  action: "complete"
  parameters:
    prompt: "Hello"
```

## 🚨 When to Seek Help

### Community Support
- **GitHub Discussions:** General questions and usage help
- **GitHub Issues:** Bug reports with reproduction steps

## 📞 Emergency Contacts

**Security Issues:** security@akioud.ai (private disclosure only)  
**General Support:** GitHub Issues/Discussions  

---

**Most issues are configuration-related or environment compatibility problems. The troubleshooting steps above resolve 90%+ of user issues.**

*AKIOS — Where AI meets unbreakable security*  
*Use responsibly. Your safety and compliance are your responsibility.* 🛡️
