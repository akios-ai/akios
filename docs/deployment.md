# AKIOS v1.0 – Deployment Scope & Boundaries  
**Document Version:** 1.0  
**Date:** 2026-01-25  

**Status: FINAL – Locked for v1.0 Open Runtime Launch (January 2026)**

This document **completely replaces and overrides** all previous deployment philosophy, methods, Docker Compose setups, systemd services, Nginx configs, monitoring integrations, security hardening scripts, backup strategies, scaling patterns, and troubleshooting guides from the old architecture.

We are now in a **security & governance-first, minimal cage** product.  
Deployment is **not** a multi-container, multi-service, production-hardened cluster setup.  
It is **the simplest possible way** to run the single-process cage securely in staging or internal production.

### 1. Philosophy for v1.0

Deployment must be **minimal, secure, and air-gapped capable** from day 1.  
The cage is a **Python package or Docker container** — no database, no Redis, no API server, no monitoring dashboard, no reverse proxy, no Helm charts.

**Core principle**:  
Run anywhere (laptop, VM, air-gapped server) with **zero external dependencies** at runtime.  
Security is enforced by the cage itself — not by infrastructure.

### 2. In Scope – What MUST exist in v1.0 Deployment

**Deployment Options (two supported methods)**:

| Method                        | Description & How It Works                                      | Security Level | Best For |
|-------------------------------|-----------------------------------------------------------------|----------------|----------|
| **Pip Package** ⭐            | Python package installation with ecosystem integration         | Full kernel-hard (Linux) | Python developers, CI/CD |
| **Docker Container**          | Official minimal Docker image + containerized deployment       | Strong policy-based | Cross-platform teams, development |

**Required Artifacts**:
- `Dockerfile` (Alpine/scratch base + Python application)
- `README.md` deployment section with exact commands
- `examples/docker-compose.yml` (optional, minimal 1-service)

**Basic Docker Example (must be simple)**:

```dockerfile
# Dockerfile (minimal)
FROM python:3.12-slim
RUN pip install akios
CMD ["akios", "run", "/app/templates/document_ingestion.yml"]
```

```bash
# Run
docker run --rm -v $(pwd)/templates:/app/templates akios:latest
```

**No**:
- Multi-service docker-compose (no db/redis)
- Systemd service files
- Nginx reverse proxy
- Prometheus/Grafana setup
- Backup scripts
- Scaling instructions

### 3. Out of Scope – What MUST NOT exist in v1.0 Deployment

| Feature / Method                                      | Why forbidden in v1.0                              | Where it belongs (if ever)                  |
|-------------------------------------------------------|----------------------------------------------------|---------------------------------------------|
| Multi-container setups (db, redis, monitoring)        | Single-process cage – no external deps             | Future open releases                        |
| Docker Compose with volumes/networks/services         | Too complex for v1.0                               | Future open releases                        |
| Systemd/Init.d service files                          | Not needed for minimal usage                       | Future open releases                        |
| Nginx/Apache reverse proxy                            | No API/web server in v1.0                          | Future open releases                        |
| Prometheus/Grafana/Jaeger monitoring                  | No observability layer in v1.0                     | Future open releases                        |
| Backup & recovery scripts (DB snapshots, logs)        | No DB, no persistence                              | Future open releases                        |
| Scaling / horizontal load balancing                   | Single-process runtime                             | Future open releases                        |
| Security hardening (ufw, fail2ban, SELinux profiles)  | Cage enforces security internally                  | Future or PRO                               |

### 4. Security & Safety Boundaries

- **Air-gapped capable** — runs without internet after initial setup
- **Minimal footprint** — small container images, low attack surface
- **No ports open by default** — no API server, no dashboard
- **Run as non-root** — docs recommend `--user` in Docker or dedicated user
- **Audit always on** — every run produces Merkle-proof export
- **Fail-safe** — invalid config/workflow → immediate exit

### 5. Size & Complexity Target for v1.0

- **Dockerfile**: <20 lines
- **Deployment docs**: 1 page in README
- **No additional scripts/tools** (no compose, no systemd, no nginx)

### Summary – deployment in one sentence

**V1.0 deployment is a Python package or basic Docker container that runs the cage standalone with zero external dependencies — nothing more.**

**No multi-service setups. No monitoring. No scaling. No hardening scripts. Just the simplest secure run.**

This boundary is **locked** for v1.0 Open Runtime.  
Any addition of multi-container, monitoring, proxy, scaling, or hardening features requires explicit scope re-opening and justification against the minimal security-first philosophy.

All previous comprehensive deployment docs (Docker Compose clusters, systemd, Nginx, monitoring, backups, scaling) are now **obsolete** for V1.0.

## 🛠️ Troubleshooting Deployment Issues

### Environment Compatibility Issues

#### "AKIOS requires Linux kernel 5.4+"
**Solutions:**
1. **Check kernel version:**
   ```bash
   uname -r  # Must be 5.4.0 or higher
   ```

2. **Upgrade Ubuntu:**
   ```bash
   sudo apt update && sudo apt upgrade
   sudo apt install linux-generic-hwe-20.04-edge
   sudo reboot
   ```

3. **Supported distributions:**
   - Ubuntu 20.04 LTS+ (kernel 5.4+)
   - Fedora 35+ (kernel 5.15+)
   - CentOS/RHEL 8+ (kernel 4.18+ with backports)

#### "cgroups v2 not available"
**Solutions:**
1. **Check status:**
   ```bash
   stat -fc %T /sys/fs/cgroup/  # Should show "cgroup2fs"
   ```

2. **Enable cgroups v2:**
   ```bash
   # Ubuntu/Debian
   sudo nano /etc/default/grub
   # Add to GRUB_CMDLINE_LINUX: systemd.unified_cgroup_hierarchy=1
   sudo update-grub
   sudo reboot
   ```

#### "seccomp-bpf not supported"
**Solutions:**
1. **Check kernel config:**
   ```bash
   grep CONFIG_SECCOMP_FILTER /boot/config-$(uname -r)
   # Should show "=y"
   ```

2. **Use supported kernel:**
   - Ubuntu 20.04+ with HWE kernel
   - Fedora 35+ with modern kernel

### Docker Installation Issues

#### "docker: command not found"
**Solutions:**
1. **Install Docker:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install docker.io
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

2. **Verify installation:**
   ```bash
   docker --version
   docker run hello-world
   ```

#### "docker: Got permission denied"
**Solutions:**
1. **Add user to docker group:**
   ```bash
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

2. **Use sudo (less secure):**
   ```bash
   sudo docker run akios:latest --version
   ```

### PyPI Installation Issues

#### "pip install akios failed"
**Solutions:**
1. **Check Python version:**
   ```bash
   python3 --version  # Must be 3.8+
   ```

2. **Upgrade pip:**
   ```bash
   pip install --upgrade pip
   ```

3. **Use virtual environment:**
   ```bash
   python3 -m venv akios-env
   source akios-env/bin/activate
   pip install akios
   ```

#### "akios: command not found"
**Solutions:**
1. **Check PATH:**
   ```bash
   which akios  # Should show installation path
   echo $PATH   # Should include bin directory
   ```

2. **Add to PATH:**
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   # Add to ~/.bashrc or ~/.zshrc
   ```

3. **Reinstall:**
   ```bash
   pip uninstall akios
   pip install akios
   ```

### Container Runtime Issues

#### "Container exits immediately"
**Solutions:**
1. **Check logs:**
   ```bash
   docker run --rm akios:latest 2>&1
   ```

2. **Run with shell:**
   ```bash
   docker run -it --rm akios:latest /bin/bash
   ```

3. **Check environment:**
   ```bash
   docker run --rm akios:latest env
   ```

#### "Permission denied" with volumes
**Solutions:**
1. **Check file permissions:**
   ```bash
   ls -la /host/directory/
   ```

2. **Use correct user mapping:**
   ```bash
   docker run -v /host/path:/container/path -u $(id -u):$(id -g) akios:latest
   ```

#### "Network access blocked"
**Solutions:**
1. **Enable network in config:**
   ```yaml
   # config.yaml
   network_access_allowed: true
   ```

2. **Check DNS:**
   ```bash
   docker run --rm akios:latest nslookup google.com
   ```

### Resource and Performance Issues

#### "Container killed" due to limits
**Solutions:**
1. **Increase resource limits:**
   ```bash
   docker run --memory=512m --cpus=1.0 akios:latest
   ```

2. **Check system resources:**
   ```bash
   free -h    # Memory
   df -h      # Disk
   nproc      # CPU cores
   ```

#### "Workflow too slow"
**Solutions:**
1. **Optimize config:**
   ```yaml
   cpu_limit: 0.9
   memory_limit_mb: 512
   ```

2. **Check network latency:**
   ```bash
   docker run --rm akios:latest ping -c 3 google.com
   ```

### Security-Related Issues

#### "Sandbox initialization failed"
**Solutions:**
1. **Check kernel features:**
   ```bash
   uname -r                    # 5.4+
   ls /sys/fs/cgroup/          # Should exist
   grep seccomp /proc/config.gz  # Should show =y
   ```

2. **Disable sandbox for testing:**
   ```yaml
   # config.yaml (NOT RECOMMENDED)
   sandbox_enabled: false
   ```

#### "Root user warning"
**Solution:** Create dedicated user for security:
```bash
sudo useradd -m akios-user
sudo -u akios-user docker run akios:latest
```

### Multi-Environment Setup

#### Development Environment
```bash
# Relaxed settings for development
docker run \
  -v $(pwd)/workflows:/app/workflows \
  -v $(pwd)/data:/app/data \
  --memory=1g \
  --cpus=1.0 \
  akios:latest
```

#### Production Environment
```bash
# Secure settings for production
docker run \
  --read-only \
  --tmpfs /tmp \
  --memory=256m \
  --cpus=0.5 \
  --user 1001:1001 \
  akios:latest
```

#### CI/CD Integration
```yaml
# GitHub Actions example
- name: Test AKIOS workflow
  run: |
    docker run --rm \
      -v ${{ github.workspace }}:/workflows \
      akios:latest \
      run /workflows/ci-test.yml
```

## 🔍 Advanced Diagnostics

### Environment Validation Script
```bash
#!/bin/bash
echo "=== AKIOS Environment Check ==="

# Python
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python: $python_version"
[ "$(printf '%s\n' "$python_version" "3.8" | sort -V | head -n1)" = "3.8" ] && echo "✅ Python OK" || echo "❌ Python 3.8+ required"

# Kernel
kernel=$(uname -r)
echo "Kernel: $kernel"
[ "$(printf '%s\n' "$kernel" "5.4" | sort -V | head -n1)" = "5.4" ] && echo "✅ Kernel OK" || echo "❌ Kernel 5.4+ required"

# Cgroups
cgroup_type=$(stat -fc %T /sys/fs/cgroup/ 2>/dev/null)
echo "Cgroups: $cgroup_type"
[ "$cgroup_type" = "cgroup2fs" ] && echo "✅ cgroups v2 OK" || echo "❌ cgroups v2 required"

# Seccomp
grep -q "CONFIG_SECCOMP_FILTER=y" /boot/config-$(uname -r) 2>/dev/null && echo "✅ seccomp OK" || echo "❌ seccomp required"

# Docker
command -v docker >/dev/null 2>&1 && echo "✅ Docker OK" || echo "❌ Docker required"

echo "=== Environment Check Complete ==="
```

### Deployment Testing Checklist
- [ ] Environment validation passes
- [ ] Docker installation works
- [ ] PyPI installation succeeds
- [ ] Basic commands execute
- [ ] Volume mounting works
- [ ] Network access functions (when enabled)
- [ ] Resource limits respected
- [ ] Sandbox initializes properly

## 📞 Support Resources

- **Documentation:** README.md, TROUBLESHOOTING.md
- **Community:** GitHub Issues, GitHub Discussions

---

**Deployment issues are usually environment or configuration related. The troubleshooting guide above resolves 95% of deployment problems.**

