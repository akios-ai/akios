# EC2 Performance Testing Guide – Complete Setup & Validation

**Document Version:** 1.0  
**Date:** 2026-01-30  
**Scope:** AKIOS v1.0.4 native Linux performance & security validation on AWS EC2

---

## ⚠️ Legal Disclaimers & User Responsibility

### AKIOS is Provided "As-Is" – AWS Infrastructure Responsibility

**Important:** AKIOS performance metrics are validated ONLY on specific AWS EC2 configurations. Your actual performance may differ based on instance type, region, load, and configuration choices.

#### What AKIOS Guarantees
✅ **Security of the AKIOS sandbox** (if you follow security best practices)  
✅ **PII redaction works as documented**  
✅ **Audit trails are cryptographically sound**  
✅ **Performance on t3.medium instances** (our baseline test platform)

#### What AKIOS Does NOT Guarantee
❌ **AWS infrastructure performance** beyond our tested configuration  
❌ **AWS account security** (your responsibility to manage credentials)  
❌ **AWS cost management** (you manage your AWS billing)  
❌ **Performance on untested instance types or regions**  
❌ **Results from misconfigured workflows or environments**

### User Responsibilities When Testing on AWS EC2

#### 1. AWS Account Security
- **Keep access keys safe** — never commit to version control or share
- **Use IAM roles** with least-privilege permissions (don't use root credentials)
- **Enable CloudTrail** for audit logging of AWS API calls
- **Rotate credentials** regularly
- **Use security groups** to restrict EC2 access (SSH on port 22 only)

**AKIOS is NOT responsible for:**
- EC2 instance compromise or account takeover
- AWS IAM misconfigurations
- Leaked API keys or credentials
- Unauthorized access to your instances

#### 2. Cost Management
- **Monitor your AWS bill** actively during testing
- **Set up AWS billing alerts** to prevent surprise charges
- **Understand EC2 pricing** for your chosen region and instance type
- **Terminate instances** when testing is complete
- **Use on-demand or spot instances** appropriately

**AKIOS is NOT responsible for:**
- AWS infrastructure charges you incur
- Data transfer costs or storage fees
- Runaway instances left running after testing
- Regional price variations

**Note:** AKIOS includes budget kill-switches for LLM API costs ($1 default), but this does NOT cover AWS EC2 or data transfer costs.

#### 3. Data Security
- **Encrypt sensitive files** before running them through AKIOS
- **Don't put secrets in workflows** (API keys, passwords, etc.)
- **Use environment variables** for credentials (never hardcode)
- **Secure your EC2 instances** with proper security groups
- **Don't run untested workflows** from untrusted sources

**AKIOS is NOT responsible for:**
- EC2 instance compromise due to misconfiguration
- Secrets leaked through your workflows
- Data breaches from misconfigured security groups
- Malicious workflows you chose to run

#### 4. Infrastructure Validation
- **Test on YOUR chosen instance type** (not just t3.medium)
- **Validate performance** meets YOUR requirements
- **Understand the difference** between baseline and your setup
- **Document your findings** for your team

**AKIOS is NOT responsible for:**
- Performance degradation on untested instance types
- Results that don't match your use case
- Infrastructure issues outside AKIOS control
- Third-party software conflicts

---

## 🚀 EC2 Instance Recommendations

### Choose Based on Your Use Case

| Use Case | Recommended | vCPU | Memory | Baseline Performance | Cost/Month | Notes |
|----------|------------|------|--------|----------------------|-----------|-------|
| **Testing & Learning** | t3.medium | 2 | 4GB | 25ms startup, 44.44 wf/s | ~$15 | ⭐ AKIOS validated baseline |
| **Light Production** | t3.large | 2 | 8GB | ~20ms startup, ~80 wf/s | ~$30 | 2x resources, burstable |
| **Standard Production** | t3.xlarge | 4 | 16GB | ~15ms startup, ~120 wf/s | ~$60 | 4x resources, high burst |
| **High Performance** | c6i.large | 2 | 4GB | ~18ms startup, ~90 wf/s | ~$70 | Compute optimized |
| **Very High Volume** | c6i.2xlarge | 8 | 16GB | ~10ms startup, ~250+ wf/s | ~$280 | Extreme performance |
| **Memory Intensive** | r6i.large | 2 | 16GB | ~22ms startup, ~50 wf/s | ~$150 | Memory optimized |
| **Budget Testing** | t3.small | 1 | 2GB | ~50ms startup, ~20 wf/s | ~$8 | Minimal resources |

**Legend:**
- ⭐ **AKIOS Validated:** We officially test & validate on this instance
- 📊 **Estimated:** Performance projections (test YOUR instance before production)
- 💰 **Cost:** Approximate monthly cost on-demand (check AWS pricing for current rates)

### Instance Family Recommendations

#### **t3 Family** (Burstable Performance)
**Best for:** Variable workloads, testing, light production
- Earn CPU credits when not running at capacity
- Burst to higher performance when needed
- Cost-effective for non-continuous workloads
- Good for development & testing
- **Example:** `t3.medium` for AKIOS testing (our validated baseline)

#### **c6i Family** (Compute Optimized)
**Best for:** Sustained high-performance workloads
- All performance, no burstability
- Consistent, predictable performance
- No CPU credit system
- Best for continuous production load
- **Example:** `c6i.large` for sustained AI workflows

#### **r6i Family** (Memory Optimized)
**Best for:** Large in-memory datasets
- Ideal for workflows processing large data volumes
- More memory per vCPU than t3/c6i
- Sustained performance like c6i
- **Example:** `r6i.large` for batch processing large files

#### **m6i Family** (General Purpose)
**Best for:** Balanced workloads using CPU, memory equally
- Good balance of compute, memory, networking
- Sustained performance
- Middle ground between c6i and r6i
- **Example:** `m6i.xlarge` for mixed workloads

### By AWS Region

Performance may vary by region due to:
- Network latency to your location
- Instance availability
- Regional pricing differences
- Data center hardware variations

**AKIOS validated in:** `us-east-1` (N. Virginia)

**For other regions:**
- Performance characteristics may differ
- Test in YOUR target region before production
- Regional pricing varies significantly
- Some instance types may not be available

---

## 📊 Expected Performance by Instance Type

### Performance Scaling Model

**Based on AKIOS v1.0.4 validation:**

```
Startup Latency:  ~25ms (base on t3.medium)
                  = baseline_latency + per_workflow_setup

Throughput:       ~44.44 wf/s (on t3.medium)
                  = CPU_count * base_throughput * scaling_factor

Memory Usage:     ~21MB (base + workflow data)
                  = constant_overhead + variable_per_workflow
```

### Performance Projections

| Instance | vCPU | Expected Startup | Expected Throughput | Scaling |
|----------|------|-----------------|-------------------|---------|
| t3.medium | 2 | **25ms** ⭐ | **44.44 wf/s** ⭐ | Baseline |
| t3.large | 2 | ~22ms | ~60 wf/s | +35% (more burst) |
| t3.xlarge | 4 | ~20ms | ~100 wf/s | +125% (2x capacity) |
| c6i.large | 2 | ~20ms | ~80 wf/s | +80% (always fast) |
| c6i.2xlarge | 8 | ~15ms | ~280 wf/s | +520% (extreme) |
| r6i.large | 2 | ~22ms | ~50 wf/s | +12% (memory overhead) |
| t3.small | 1 | ~40ms | ~22 wf/s | -50% (half resources) |

**⚠️ Important:**
- These are **projections** based on EC2 architecture
- Actual results depend on workload, instance load, AWS region
- **Test on YOUR instance before assuming performance**
- Burstable instances (t3) vary based on CPU credit balance

---

## 🔧 Complete EC2 Setup Guide

### Prerequisites

1. **AWS Account** with active credentials
2. **EC2 Key Pair** (for SSH access)
3. **Ubuntu 22.04 LTS or 24.04 LTS** AMI selection
4. **Security Group** allowing SSH (port 22) from your IP
5. **Valid LLM API key** (OpenAI, Anthropic, Grok, Mistral, or Gemini)

### Step 1: Create EC2 Instance

**Option A: AWS Console (GUI)**
```
1. Go to AWS EC2 Dashboard
2. Click "Launch Instances"
3. Select "Ubuntu 22.04 LTS" or "Ubuntu 24.04 LTS" AMI
4. Choose instance type (recommend t3.medium for testing)
5. Create/select key pair (save .pem file securely)
6. Create security group (allow SSH from your IP: 0.0.0.0/0 for quick testing, restrict to your IP for production)
7. Review and Launch
8. Wait 2-3 minutes for instance to reach "running" state
```

**Option B: AWS CLI**
```bash
aws ec2 run-instances \
  --image-ids ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups allow-ssh \
  --count 1 \
  --region us-east-1
```

### Step 2: Connect via SSH

```bash
# Set permissions on your key file (required)
chmod 400 your-key-pair.pem

# Connect to instance
ssh -i your-key-pair.pem ubuntu@your-instance-ip

# If you get "Host key verification failed" on first connect:
ssh -o StrictHostKeyChecking=no -i your-key-pair.pem ubuntu@your-instance-ip
```

### Step 3: Install AKIOS

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3-pip python3-venv

# Install AKIOS
pip install akios

# Verify installation
akios --version  # Should show "AKIOS 1.0.4"
```

### Step 4: Configure AKIOS

```bash
# Create project directory
mkdir -p ~/akios-test && cd ~/akios-test

# Initialize AKIOS
akios init test-workflow
cd test-workflow

# Run guided setup (interactive)
akios setup
# Follow wizard:
# 1. Select LLM provider (OpenAI, Anthropic, Grok, etc.)
# 2. Enter API key
# 3. Accept default budget ($1)
# 4. Accept default settings

# Verify setup
akios status
```

### Step 5: Run Performance Tests

```bash
# In your project directory
cd ~/akios-test/test-workflow

# Test 1: Basic startup time
time akios status

# Test 2: Single workflow execution
time akios run templates/hello-workflow.yml

# Test 3: Check results
cat data/output/run_*/hello-ai.txt
```

---

## 📈 Validation Checklist

After running AKIOS on EC2, validate:

### Performance Validation
- [ ] **Startup latency measured** (use `time akios status`)
- [ ] **Throughput tested** (note how many workflows complete per minute)
- [ ] **Memory usage checked** (use `free -h` or `ps aux`)
- [ ] **Results match expectations** for your instance type
- [ ] **Performance baseline documented** for your team

### Security Validation
- [ ] **Security status shows** "Full (kernel-hard)" (run `akios status`)
- [ ] **PII redaction works** (test with sensitive data)
- [ ] **Audit logs generated** (`akios audit`)
- [ ] **Budget controls active** (check cost in logs)

### Operational Validation
- [ ] **Workflows execute successfully** (no errors)
- [ ] **Output files created** in `data/output/`
- [ ] **LLM API calls work** (if using real API)
- [ ] **Logs are readable** (check `/var/log` or AKIOS logs)
- [ ] **No credential leaks** in logs or output

### Cost Validation
- [ ] **AWS billing monitored** during testing
- [ ] **Instance terminated** when testing complete
- [ ] **Unexpected charges identified** (if any)
- [ ] **Cost baselines understood** for future planning

---

## ⚡ Performance Optimization Tips

### 1. CPU Performance
```bash
# Check CPU cores available
nproc  # Should show 2 for t3.medium, 4 for t3.xlarge, etc.

# Monitor CPU usage during workflows
watch -n 1 'top -bn1 | head -20'

# Enable kernel performance features (if available)
sudo sysctl -w kernel.sched_migration_cost_ns=5000000
```

### 2. Memory Optimization
```bash
# Check available memory
free -h

# Monitor memory during workflow execution
watch -n 1 'free -h && ps aux | head -20'

# Clear caches if needed (caution!)
sudo sync && sudo sysctl -w vm.drop_caches=3
```

### 3. Network Optimization
```bash
# Check network connectivity
ping -c 4 8.8.8.8

# Test latency to LLM APIs
curl -w "@curl-format.txt" -o /dev/null -s https://api.openai.com/

# Optimize TCP settings if needed
sudo sysctl -w net.ipv4.tcp_tw_reuse=1
```

### 4. I/O Optimization
```bash
# Check disk performance
sudo iotop -o  # Show disk I/O

# Monitor disk space
df -h

# Use SSD for better performance (default on EC2 instances)
lsblk  # Verify SSD/NVMe disks
```

---

## 🛑 Common Issues & Solutions

### Issue: Slow Performance
**Could be caused by:**
- Wrong instance type (too small)
- Running other workloads on same instance
- Network latency to LLM APIs
- AWS region with high latency

**Solutions:**
1. Check CPU/memory: `top`, `free -h`
2. Test on larger instance type if needed
3. Check network latency: `ping api.openai.com`
4. Test in different AWS region
5. Verify no background processes: `systemctl status`

### Issue: High Memory Usage
**Could be caused by:**
- Large workflow data
- Memory leaks in AKIOS (unlikely)
- Other processes consuming memory

**Solutions:**
1. Check memory: `free -h`
2. Kill unnecessary processes: `killall python3` (caution!)
3. Reduce workflow input size
4. Use larger instance type (r6i.xlarge)

### Issue: API Latency High
**Could be caused by:**
- Network latency to LLM provider
- LLM provider under load
- AWS region far from API endpoint
- Connection pooling issues

**Solutions:**
1. Test latency: `curl -w "%{time_total}\n" https://api.openai.com/`
2. Use region closer to API endpoint
3. Check if LLM provider has regional endpoints
4. Try different LLM provider (Grok, Anthropic, etc.)

### Issue: Permissions Error When Running Workflows
**Could be caused by:**
- Wrong file permissions
- Volume not properly mounted
- AKIOS not installed correctly

**Solutions:**
```bash
# Check file permissions
ls -la data/input/
chmod 755 data/
chmod 644 data/input/*

# Verify AKIOS installation
which akios
akios --version

# Reinstall if needed
pip install --upgrade akios
```

### Issue: Connection to AWS EC2 Times Out
**Could be caused by:**
- Security group not allowing SSH
- Wrong key pair file
- Wrong username for AMI
- AWS rate limiting

**Solutions:**
1. Verify security group allows SSH port 22
2. Check key pair permissions: `chmod 400 key.pem`
3. Use correct username: `ubuntu` for Ubuntu AMIs
4. Verify instance IP hasn't changed
5. Try: `ssh -v -i your-key.pem ubuntu@your-ip` for debugging

---

## 💰 Cost Estimation

### EC2 Pricing (Approximate, check AWS for current rates)

```
t3.medium:   $0.0416/hour  ~= $30/month
t3.large:    $0.0832/hour  ~= $60/month
t3.xlarge:   $0.1664/hour  ~= $120/month
c6i.large:   $0.085/hour   ~= $62/month
c6i.2xlarge: $0.34/hour    ~= $248/month
```

### Example: Month-Long Testing
```
Instance Type    Hours    Hourly Rate    Total Cost
─────────────────────────────────────────────────
t3.medium        720      $0.0416        ~$30
t3.large         720      $0.0832        ~$60
c6i.large        720      $0.085         ~$62
c6i.2xlarge      720      $0.34          ~$248

Add ~20% for:
- Data transfer (EBS operations, network)
- Storage (EBS volumes, snapshots)
- CloudTrail logging (if enabled)
```

### Cost Control Tips
1. **Stop instances** when not in use (doesn't delete, just saves cost)
2. **Terminate instances** when testing complete (full cleanup)
3. **Use t3 burstable** for testing (more cost-effective)
4. **Use c6i reserved** for long-term production (20-40% discount)
5. **Monitor billing** with AWS Budgets
6. **Set cost alerts** in AWS Billing

---

## 🔐 Security Best Practices for EC2

### 1. SSH Key Management
```bash
# Generate secure key pair (if not already done)
aws ec2 create-key-pair --key-name akios-test --query 'KeyMaterial' \
  --output text > akios-test.pem
chmod 400 akios-test.pem

# Never share or commit key file
git config core.excludesfile .gitignore
echo "*.pem" >> .gitignore
```

### 2. Security Groups
```bash
# Restrict SSH to your IP only (for production)
# Development: Allow 0.0.0.0/0 (open to internet)
# Production: Allow only your IP (X.X.X.X/32 in CIDR notation)

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 22 \
  --cidr YOUR_IP/32
```

### 3. IAM Credentials
```bash
# Never use AWS root credentials for EC2
# Create IAM user with limited permissions

# On EC2 instance:
# Use IAM instance role instead of hardcoded credentials
# Attach role: AmazonEC2FullAccess (for development)
# Restrict for production (principle of least privilege)
```

### 4. Monitoring & Logging
```bash
# Enable CloudTrail for API audit
# Enable VPC Flow Logs for network traffic
# Enable CloudWatch for system metrics
# Review logs regularly

aws cloudtrail create-trail --name akios-audit --s3-bucket-name my-audit-logs
```

### 5. Shutdown & Cleanup
```bash
# When testing complete:

# Stop instance (keeps data, charges paused)
aws ec2 stop-instances --instance-ids i-xxxxxxxxx

# Terminate instance (deletes everything, no charges)
aws ec2 terminate-instances --instance-ids i-xxxxxxxxx

# Delete key pair if no longer needed
aws ec2 delete-key-pair --key-name akios-test

# Verify deletion
aws ec2 describe-instances --instance-ids i-xxxxxxxxx
```

---

## 📋 Performance Testing Checklist

Before concluding your EC2 testing, verify:

```
SETUP
☐ EC2 instance created (t3.medium or your chosen type)
☐ SSH access working
☐ AKIOS installed and verified
☐ LLM API key configured
☐ Test workflow created

PERFORMANCE TESTING
☐ Startup latency measured
☐ Throughput tested (10+ workflows)
☐ Memory usage recorded
☐ Scaling efficiency tested (if multi-core instance)
☐ API latency measured (if using real API)

SECURITY TESTING
☐ Security status shows "Full (kernel-hard)"
☐ PII redaction verified with test data
☐ Audit logs generated
☐ Budget controls functional

DOCUMENTATION
☐ Performance results recorded
☐ Baseline established for your instance
☐ Issues documented
☐ Next steps identified

CLEANUP
☐ Instance terminated or stopped
☐ Costs monitored and documented
☐ Key pair secured or deleted
☐ S3/CloudTrail data archived if needed
```

---

## 📞 Support & Questions

### When Something Goes Wrong

1. **Check AKIOS logs:**
   ```bash
   akios logs --limit 50
   cat data/audit/*.jsonl | tail -20
   ```

2. **Check system resources:**
   ```bash
   top -b -n 1 | head -20
   free -h
   df -h
   ```

3. **Check AWS health:**
   ```bash
   aws ec2 describe-instance-status --instance-ids i-xxxxxxxxx
   ```

4. **Report issues with:**
   - Instance type used
   - Workflow definition
   - Error messages from logs
   - System resource snapshot
   - AWS region and AZ

### References

- **[AKIOS Main Documentation](../README.md)** - Overview and features
- **[Native vs Docker Performance](./performance-comparison.md)** - Detailed comparison
- **[Deployment Guide](./deployment.md)** - Deployment best practices
- **[AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)** - AWS reference

---

## ⚖️ Final Legal Statement

> AKIOS is provided "as-is" for testing and development purposes. Users are solely responsible for:
> - AWS account security and cost management
> - Proper configuration of instances and security groups
> - Validation of performance on their chosen infrastructure
> - Compliance with AWS terms of service
> - Data security and privacy in their workflows
> 
> AKIOS provides performance validation scripts and baseline metrics to help users validate their setup, but does NOT guarantee specific performance on any instance other than t3.medium in us-east-1.
> 
> By using AKIOS on AWS EC2, you accept full responsibility for your infrastructure, costs, and data security.

---

**Built with security-first principles. Run AI agents safely on your infrastructure.**
