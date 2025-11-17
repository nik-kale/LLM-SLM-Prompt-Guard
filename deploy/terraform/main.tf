# Terraform configuration for deploying llm-slm-prompt-guard on AWS
#
# This deploys:
# - ECS Fargate cluster for the HTTP proxy
# - RDS PostgreSQL for audit logging
# - ElastiCache Redis for caching and storage
# - Application Load Balancer
# - VPC and networking
# - CloudWatch monitoring

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Configure backend for state storage
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "prompt-guard/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "llm-slm-prompt-guard"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  azs          = var.availability_zones
}

# RDS Module (PostgreSQL for audit logging)
module "rds" {
  source = "./modules/rds"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  instance_class      = var.rds_instance_class
  allocated_storage   = var.rds_allocated_storage
  database_name       = var.database_name
  master_username     = var.database_username
  backup_retention    = var.rds_backup_retention
  multi_az            = var.rds_multi_az
}

# ElastiCache Module (Redis for caching)
module "elasticache" {
  source = "./modules/elasticache"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  node_type          = var.redis_node_type
  num_cache_nodes    = var.redis_num_nodes
  engine_version     = var.redis_engine_version
}

# ECS Module (Fargate for HTTP proxy)
module "ecs" {
  source = "./modules/ecs"

  project_name           = var.project_name
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  public_subnet_ids      = module.vpc.public_subnet_ids
  container_image        = var.container_image
  container_port         = var.container_port
  desired_count          = var.ecs_desired_count
  cpu                    = var.ecs_cpu
  memory                 = var.ecs_memory
  autoscaling_min        = var.ecs_autoscaling_min
  autoscaling_max        = var.ecs_autoscaling_max
  autoscaling_cpu_target = var.ecs_autoscaling_cpu_target

  # Environment variables
  redis_url    = module.elasticache.redis_endpoint
  postgres_url = module.rds.connection_string
  policy       = var.pii_policy
}

# Outputs
output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = module.ecs.load_balancer_dns
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.redis_endpoint
  sensitive   = true
}

output "postgres_endpoint" {
  description = "PostgreSQL endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = module.ecs.log_group_name
}
