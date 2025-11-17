# Variables for Terraform deployment

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "prompt-guard"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# RDS Configuration
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 100
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "prompt_guard"
}

variable "database_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "rds_backup_retention" {
  description = "Backup retention period in days"
  type        = number
  default     = 30
}

variable "rds_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = true
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 2
}

variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

# ECS Configuration
variable "container_image" {
  description = "Docker image for the proxy"
  type        = string
  default     = "your-registry/prompt-guard-proxy:latest"
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 3
}

variable "ecs_cpu" {
  description = "ECS task CPU units"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 1024
}

variable "ecs_autoscaling_min" {
  description = "Minimum number of tasks"
  type        = number
  default     = 2
}

variable "ecs_autoscaling_max" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "ecs_autoscaling_cpu_target" {
  description = "Target CPU utilization for autoscaling"
  type        = number
  default     = 70
}

# Application Configuration
variable "pii_policy" {
  description = "PII detection policy to use"
  type        = string
  default     = "default_pii"

  validation {
    condition = contains([
      "default_pii",
      "hipaa_phi",
      "pci_dss",
      "gdpr_strict",
      "slm_local"
    ], var.pii_policy)
    error_message = "Invalid PII policy. Must be one of: default_pii, hipaa_phi, pci_dss, gdpr_strict, slm_local"
  }
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
