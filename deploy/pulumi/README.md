# Pulumi AWS Deployment for llm-slm-prompt-guard

Infrastructure as Code (IaC) for deploying llm-slm-prompt-guard on AWS using Pulumi and Python.

## Overview

This Pulumi project deploys the complete infrastructure for prompt-guard on AWS, including:

- **VPC**: Isolated network with public and private subnets across 3 availability zones
- **ECS Fargate**: Serverless container orchestration for the HTTP proxy
- **Application Load Balancer**: HTTP/HTTPS endpoint with health checks
- **RDS PostgreSQL**: Multi-AZ database for audit logging
- **ElastiCache Redis**: In-memory cache for performance
- **Auto Scaling**: Automatic scaling based on CPU utilization
- **CloudWatch**: Centralized logging and monitoring

## Prerequisites

1. **Pulumi CLI** (version 3.96.0+)
   ```bash
   # macOS
   brew install pulumi

   # Linux
   curl -fsSL https://get.pulumi.com | sh

   # Windows
   choco install pulumi
   ```

2. **Python** (3.9+)
   ```bash
   python --version
   ```

3. **AWS CLI** configured with credentials
   ```bash
   aws configure
   ```

4. **Docker image** built and pushed to a registry (ECR, Docker Hub, GHCR)
   ```bash
   docker build -t ghcr.io/your-username/prompt-guard-proxy:latest .
   docker push ghcr.io/your-username/prompt-guard-proxy:latest
   ```

## Quick Start

### 1. Install Dependencies

```bash
cd deploy/pulumi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Pulumi

```bash
# Login to Pulumi (free account or self-hosted)
pulumi login

# Create a new stack (e.g., dev, staging, production)
pulumi stack init production

# Configure AWS region
pulumi config set aws:region us-east-1

# Set database password (stored encrypted)
pulumi config set --secret db-password YourSecurePassword123!
```

### 3. Review Configuration

```bash
# View current configuration
pulumi config

# Optional: Customize configuration
pulumi config set prompt-guard:environment production
pulumi config set prompt-guard:ecs-desired-count 5
pulumi config set prompt-guard:pii-policy hipaa_phi
```

### 4. Preview Deployment

```bash
# See what will be created
pulumi preview
```

### 5. Deploy

```bash
# Deploy the infrastructure
pulumi up
```

This will create approximately 40+ AWS resources. The deployment takes about 15-20 minutes.

### 6. Get Outputs

```bash
# View stack outputs
pulumi stack output

# Get specific output
pulumi stack output alb_endpoint
```

## Configuration Options

| Configuration Key | Description | Default | Required |
|-------------------|-------------|---------|----------|
| `aws:region` | AWS region | `us-east-1` | Yes |
| `prompt-guard:environment` | Environment name | `production` | No |
| `prompt-guard:vpc-cidr` | VPC CIDR block | `10.0.0.0/16` | No |
| `prompt-guard:rds-instance-class` | RDS instance class | `db.t3.medium` | No |
| `prompt-guard:redis-node-type` | Redis node type | `cache.t3.medium` | No |
| `prompt-guard:ecs-cpu` | ECS task CPU units | `512` | No |
| `prompt-guard:ecs-memory` | ECS task memory (MB) | `1024` | No |
| `prompt-guard:ecs-desired-count` | Number of ECS tasks | `3` | No |
| `prompt-guard:pii-policy` | PII detection policy | `default_pii` | No |
| `db-password` | Database password | (none) | Yes (secret) |

### Setting Configuration

```bash
# Set environment
pulumi config set prompt-guard:environment staging

# Set ECS configuration
pulumi config set prompt-guard:ecs-cpu 1024
pulumi config set prompt-guard:ecs-memory 2048
pulumi config set prompt-guard:ecs-desired-count 5

# Set database instance class
pulumi config set prompt-guard:rds-instance-class db.t3.large

# Set PII policy
pulumi config set prompt-guard:pii-policy hipaa_phi

# Set secret database password
pulumi config set --secret db-password YourSecurePassword123!
```

## Stack Management

### Multiple Environments

```bash
# Create development stack
pulumi stack init dev
pulumi config set prompt-guard:environment dev
pulumi config set prompt-guard:ecs-desired-count 1
pulumi up

# Switch to production stack
pulumi stack select production
pulumi config set prompt-guard:environment production
pulumi config set prompt-guard:ecs-desired-count 5
pulumi up
```

### Update Infrastructure

```bash
# Make changes to __main__.py or configuration
# Preview changes
pulumi preview

# Apply changes
pulumi up
```

### Destroy Infrastructure

```bash
# Destroy all resources
pulumi destroy

# Delete the stack
pulumi stack rm production
```

## Outputs

After deployment, the following outputs are available:

| Output | Description |
|--------|-------------|
| `vpc_id` | VPC ID |
| `alb_dns_name` | ALB DNS name |
| `alb_endpoint` | HTTP endpoint URL |
| `redis_endpoint` | Redis endpoint address |
| `rds_endpoint` | PostgreSQL endpoint |
| `ecs_cluster_name` | ECS cluster name |
| `log_group_name` | CloudWatch log group name |

### Accessing Outputs

```bash
# Get all outputs
pulumi stack output

# Get specific output as JSON
pulumi stack output alb_endpoint --json

# Use in scripts
ENDPOINT=$(pulumi stack output alb_endpoint)
curl $ENDPOINT/health
```

## Cost Estimation

Approximate monthly costs for production deployment (us-east-1):

| Resource | Configuration | Monthly Cost |
|----------|---------------|--------------|
| ECS Fargate | 3 tasks (0.5 vCPU, 1GB) | ~$45 |
| ALB | 1 load balancer | ~$25 |
| RDS PostgreSQL | db.t3.medium (Multi-AZ) | ~$140 |
| ElastiCache Redis | cache.t3.medium | ~$40 |
| NAT Gateways | 3 NAT gateways | ~$100 |
| Data Transfer | ~100 GB | ~$9 |
| CloudWatch Logs | ~10 GB | ~$5 |
| **Total** | | **~$364/month** |

For development/staging (single AZ, smaller instances):

| Resource | Configuration | Monthly Cost |
|----------|---------------|--------------|
| ECS Fargate | 1 task (0.5 vCPU, 1GB) | ~$15 |
| ALB | 1 load balancer | ~$25 |
| RDS PostgreSQL | db.t3.small (single AZ) | ~$35 |
| ElastiCache Redis | cache.t3.micro | ~$15 |
| NAT Gateway | 1 NAT gateway | ~$33 |
| Data Transfer | ~20 GB | ~$2 |
| CloudWatch Logs | ~5 GB | ~$3 |
| **Total** | | **~$128/month** |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
                    ┌────────┐
                    │  ALB   │ (Public Subnets)
                    └────┬───┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      ┌──────┐      ┌──────┐      ┌──────┐
      │ ECS  │      │ ECS  │      │ ECS  │ (Private Subnets)
      │ Task │      │ Task │      │ Task │
      └──┬───┘      └──┬───┘      └──┬───┘
         │             │             │
         └─────────────┼─────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
      ┌──────┐    ┌────────┐    ┌─────┐
      │Redis │    │  RDS   │    │ NAT │
      └──────┘    │Postgres│    │ GW  │
                  └────────┘    └─────┘
                                   │
                                   ▼
                               Internet
```

## Monitoring

### CloudWatch Logs

```bash
# View logs
aws logs tail /ecs/prompt-guard-production --follow

# Filter logs
aws logs filter-log-events \
  --log-group-name /ecs/prompt-guard-production \
  --filter-pattern "ERROR"
```

### Metrics

Access CloudWatch metrics:
- ECS: CPU, Memory, Task count
- ALB: Request count, Latency, HTTP errors
- RDS: CPU, Connections, Storage
- Redis: Cache hits, Evictions, Memory

### Alarms

Create CloudWatch alarms:

```python
# Add to __main__.py

# High CPU alarm
cpu_alarm = aws.cloudwatch.MetricAlarm(
    "prompt-guard-high-cpu",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="CPUUtilization",
    namespace="AWS/ECS",
    period=300,
    statistic="Average",
    threshold=80.0,
    alarm_description="CPU > 80% for 10 minutes",
    dimensions={
        "ClusterName": ecs_cluster.name,
        "ServiceName": service.name,
    },
)
```

## Troubleshooting

### ECS Tasks Not Starting

```bash
# Check service events
aws ecs describe-services \
  --cluster prompt-guard-production \
  --services prompt-guard-service

# Check task status
aws ecs list-tasks \
  --cluster prompt-guard-production \
  --service-name prompt-guard-service

# View task logs
aws logs tail /ecs/prompt-guard-production --follow
```

### ALB Health Checks Failing

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(pulumi stack output target_group_arn)

# Check security groups
aws ec2 describe-security-groups \
  --group-ids $(pulumi stack output ecs_security_group_id)
```

### Database Connection Issues

```bash
# Test connection from ECS task
aws ecs execute-command \
  --cluster prompt-guard-production \
  --task <task-id> \
  --container proxy \
  --interactive \
  --command "/bin/sh"

# Inside container
nc -zv $(pulumi stack output rds_endpoint | cut -d: -f1) 5432
```

## Comparison: Pulumi vs Terraform

| Feature | Pulumi | Terraform |
|---------|--------|-----------|
| Language | Python, TypeScript, Go, C#, Java | HCL |
| State Management | Pulumi Service or S3 | S3, Terraform Cloud |
| Type Safety | Yes (native language) | Limited (HCL) |
| Testing | Native testing frameworks | Terratest |
| IDE Support | Full (IntelliSense, etc.) | Limited |
| Learning Curve | Use existing language skills | Learn HCL |
| Cost | Free (self-hosted) or paid | Free (OSS) or paid (Cloud) |

## Best Practices

1. **Use Secrets Management**
   ```bash
   pulumi config set --secret db-password YourPassword
   ```

2. **Enable Stack Policies**
   ```yaml
   # Pulumi.yaml
   policies:
     - type: aws:rds/instance:Instance
       properties:
         multiAz: true  # Require Multi-AZ for production
   ```

3. **Tag All Resources**
   ```python
   tags = {
       "Project": "prompt-guard",
       "Environment": environment,
       "ManagedBy": "Pulumi",
   }
   ```

4. **Use Stack References**
   ```python
   # Reference another stack
   vpc_id = pulumi.StackReference(f"org/network/{environment}").get_output("vpc_id")
   ```

5. **Version Control State**
   ```bash
   # Use S3 backend
   pulumi login s3://my-pulumi-state-bucket
   ```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy with Pulumi

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pulumi/actions@v4
        with:
          command: up
          stack-name: production
          work-dir: deploy/pulumi
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## Support

- **Pulumi Documentation**: https://www.pulumi.com/docs/
- **GitHub Issues**: https://github.com/nik-kale/llm-slm-prompt-guard/issues
- **Pulumi Community**: https://slack.pulumi.com/

## License

MIT License - see LICENSE for details.
