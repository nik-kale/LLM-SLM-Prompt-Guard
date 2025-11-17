# Terraform Deployment for llm-slm-prompt-guard

This directory contains Terraform configurations for deploying llm-slm-prompt-guard on AWS.

## Architecture

The deployment creates:

- **VPC**: Isolated network with public and private subnets across multiple AZs
- **ECS Fargate**: Serverless container orchestration for the HTTP proxy
- **Application Load Balancer**: HTTPS endpoint with automatic SSL/TLS
- **RDS PostgreSQL**: ACID-compliant audit logging database
- **ElastiCache Redis**: High-performance caching and session storage
- **CloudWatch**: Centralized logging and monitoring
- **Auto Scaling**: Automatic scaling based on CPU utilization (2-10 tasks)
- **Security Groups**: Least-privilege network access controls

## Prerequisites

1. **AWS Account**: With appropriate permissions
2. **Terraform**: Version >= 1.0
   ```bash
   brew install terraform  # macOS
   ```
3. **AWS CLI**: Configured with credentials
   ```bash
   aws configure
   ```
4. **Docker Image**: Built and pushed to a registry (ECR, Docker Hub)
   ```bash
   docker build -t your-registry/prompt-guard-proxy:latest .
   docker push your-registry/prompt-guard-proxy:latest
   ```

## Quick Start

### 1. Initialize Terraform

```bash
cd deploy/terraform
terraform init
```

### 2. Review Variables

Edit `terraform.tfvars`:

```hcl
aws_region     = "us-east-1"
environment    = "production"
container_image = "your-registry/prompt-guard-proxy:latest"
pii_policy     = "default_pii"  # or hipaa_phi, pci_dss, gdpr_strict

# Optional: Customize instance sizes
rds_instance_class = "db.t3.medium"
redis_node_type    = "cache.t3.medium"
ecs_cpu            = 512
ecs_memory         = 1024
```

### 3. Plan Deployment

```bash
terraform plan
```

### 4. Deploy

```bash
terraform apply
```

This will create all resources. The process takes approximately 10-15 minutes.

### 5. Get Endpoint

```bash
terraform output load_balancer_dns
# Output: prompt-guard-prod-alb-1234567890.us-east-1.elb.amazonaws.com
```

### 6. Test Deployment

```bash
# Health check
curl https://your-load-balancer-dns/health

# Test anonymization
curl -X POST https://your-load-balancer-dns/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "My email is john@example.com"}]
  }'
```

## Configuration

### Environment Variables

The ECS tasks are configured with:

- `REDIS_URL`: ElastiCache Redis endpoint
- `POSTGRES_URL`: RDS PostgreSQL connection string
- `POLICY`: PII detection policy (from `pii_policy` variable)
- `LOG_LEVEL`: INFO (configurable)

### Scaling

Auto-scaling is configured based on CPU utilization:

- **Min tasks**: 2 (configurable via `ecs_autoscaling_min`)
- **Max tasks**: 10 (configurable via `ecs_autoscaling_max`)
- **Target CPU**: 70% (configurable via `ecs_autoscaling_cpu_target`)

### High Availability

- **Multi-AZ**: Deployed across 3 availability zones
- **RDS Multi-AZ**: Automatic failover
- **Redis Cluster**: Multi-node for redundancy
- **Load Balancer**: Health checks with automatic replacement

## Cost Estimation

Approximate monthly costs for production deployment (us-east-1):

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| ECS Fargate | 3 tasks (0.5 vCPU, 1GB) | ~$45 |
| ALB | 1 load balancer | ~$25 |
| RDS PostgreSQL | db.t3.medium | ~$70 |
| ElastiCache Redis | cache.t3.medium (2 nodes) | ~$80 |
| Data Transfer | ~100 GB | ~$9 |
| CloudWatch Logs | ~10 GB | ~$5 |
| **Total** | | **~$234/month** |

For development/staging, use smaller instance sizes to reduce costs to ~$100/month.

## Modules

### VPC Module (`modules/vpc`)

Creates:
- VPC with public and private subnets
- Internet Gateway and NAT Gateways
- Route tables
- Security groups

### RDS Module (`modules/rds`)

Creates:
- PostgreSQL RDS instance
- Subnet group
- Security group
- Automated backups (30 days retention)

### ElastiCache Module (`modules/elasticache`)

Creates:
- Redis cluster
- Subnet group
- Security group
- Parameter group

### ECS Module (`modules/ecs`)

Creates:
- ECS cluster (Fargate)
- Task definition
- Service with auto-scaling
- Application Load Balancer
- CloudWatch log group

## Security Best Practices

### Implemented

✅ **Network Isolation**: Private subnets for RDS and Redis
✅ **Security Groups**: Least-privilege access rules
✅ **Encryption at Rest**: RDS and Redis encryption enabled
✅ **Encryption in Transit**: HTTPS/TLS for all endpoints
✅ **Secrets Management**: Database password stored in AWS Secrets Manager
✅ **Logging**: CloudWatch logs for audit trail
✅ **Backups**: Automated daily backups with 30-day retention

### Recommended

- **WAF**: Add AWS WAF for DDoS protection and rate limiting
- **KMS**: Use customer-managed keys for encryption
- **VPC Flow Logs**: Enable for network traffic analysis
- **GuardDuty**: Enable for threat detection
- **AWS Shield**: Consider Advanced tier for production

## Monitoring

### CloudWatch Dashboards

Access metrics via CloudWatch:

- **ECS Metrics**: CPU, memory, task count
- **ALB Metrics**: Request count, latency, errors
- **RDS Metrics**: Connections, CPU, storage
- **Redis Metrics**: Cache hit rate, memory, evictions

### Alarms

Recommended CloudWatch alarms:

```bash
# High CPU on ECS
aws cloudwatch put-metric-alarm \
  --alarm-name prompt-guard-high-cpu \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# High error rate on ALB
aws cloudwatch put-metric-alarm \
  --alarm-name prompt-guard-high-errors \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold
```

## Maintenance

### Upgrading

1. Update container image:
   ```bash
   terraform apply -var="container_image=your-registry/prompt-guard-proxy:v1.1.0"
   ```

2. ECS will perform rolling update with zero downtime

### Backup and Restore

RDS backups are automatic. To restore:

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier prompt-guard-restored \
  --db-snapshot-identifier prompt-guard-snapshot-2025-11-17
```

### Destroying Infrastructure

```bash
terraform destroy
```

**Warning**: This deletes all data. Ensure backups are taken!

## Troubleshooting

### ECS Tasks Not Starting

Check logs:
```bash
aws logs tail /ecs/prompt-guard-proxy --follow
```

Common issues:
- Image pull failure (check ECR permissions)
- Health check failing (check `/health` endpoint)
- Redis/PostgreSQL connection issues (check security groups)

### High Latency

1. Check ECS CPU/memory metrics
2. Verify Redis cache hit rate
3. Review RDS slow query logs
4. Consider increasing task count

### Connection Timeouts

1. Verify security group rules
2. Check NAT Gateway availability
3. Review VPC route tables

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/nik-kale/llm-slm-prompt-guard/issues
- **Documentation**: https://docs.prompt-guard.com
- **Email**: support@example.com

## License

MIT License - see LICENSE file for details.
