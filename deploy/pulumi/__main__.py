"""
Pulumi AWS infrastructure for llm-slm-prompt-guard.

This module deploys:
- VPC with public and private subnets
- ECS Fargate cluster for HTTP proxy
- RDS PostgreSQL for audit logging
- ElastiCache Redis for caching and storage
- Application Load Balancer
- Auto-scaling and monitoring
"""

import pulumi
import pulumi_aws as aws
from pulumi import Config, Output

# Configuration
config = Config()
environment = config.get("environment") or "production"
vpc_cidr = config.get("vpc-cidr") or "10.0.0.0/16"
rds_instance_class = config.get("rds-instance-class") or "db.t3.medium"
redis_node_type = config.get("redis-node-type") or "cache.t3.medium"
ecs_cpu = config.get_int("ecs-cpu") or 512
ecs_memory = config.get_int("ecs-memory") or 1024
ecs_desired_count = config.get_int("ecs-desired-count") or 3
pii_policy = config.get("pii-policy") or "default_pii"

# Tags to apply to all resources
tags = {
    "Project": "llm-slm-prompt-guard",
    "Environment": environment,
    "ManagedBy": "Pulumi",
}

# Get availability zones
azs = aws.get_availability_zones(state="available")

# VPC
vpc = aws.ec2.Vpc(
    "prompt-guard-vpc",
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**tags, "Name": f"prompt-guard-{environment}-vpc"},
)

# Internet Gateway
igw = aws.ec2.InternetGateway(
    "prompt-guard-igw",
    vpc_id=vpc.id,
    tags={**tags, "Name": f"prompt-guard-{environment}-igw"},
)

# Public Subnets
public_subnets = []
for i, az in enumerate(azs.names[:3]):
    subnet = aws.ec2.Subnet(
        f"prompt-guard-public-subnet-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i}.0/24",
        availability_zone=az,
        map_public_ip_on_launch=True,
        tags={**tags, "Name": f"prompt-guard-{environment}-public-{az}"},
    )
    public_subnets.append(subnet)

# Private Subnets
private_subnets = []
for i, az in enumerate(azs.names[:3]):
    subnet = aws.ec2.Subnet(
        f"prompt-guard-private-subnet-{i}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{10+i}.0/24",
        availability_zone=az,
        tags={**tags, "Name": f"prompt-guard-{environment}-private-{az}"},
    )
    private_subnets.append(subnet)

# Elastic IPs for NAT Gateways
eips = []
for i in range(3):
    eip = aws.ec2.Eip(
        f"prompt-guard-eip-{i}",
        vpc=True,
        tags={**tags, "Name": f"prompt-guard-{environment}-eip-{i}"},
    )
    eips.append(eip)

# NAT Gateways
nat_gateways = []
for i, (eip, subnet) in enumerate(zip(eips, public_subnets)):
    nat = aws.ec2.NatGateway(
        f"prompt-guard-nat-{i}",
        allocation_id=eip.id,
        subnet_id=subnet.id,
        tags={**tags, "Name": f"prompt-guard-{environment}-nat-{i}"},
    )
    nat_gateways.append(nat)

# Public Route Table
public_route_table = aws.ec2.RouteTable(
    "prompt-guard-public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={**tags, "Name": f"prompt-guard-{environment}-public-rt"},
)

# Associate public subnets with public route table
for i, subnet in enumerate(public_subnets):
    aws.ec2.RouteTableAssociation(
        f"prompt-guard-public-rta-{i}",
        subnet_id=subnet.id,
        route_table_id=public_route_table.id,
    )

# Private Route Tables (one per NAT Gateway for HA)
for i, (nat, subnet) in enumerate(zip(nat_gateways, private_subnets)):
    rt = aws.ec2.RouteTable(
        f"prompt-guard-private-rt-{i}",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                nat_gateway_id=nat.id,
            )
        ],
        tags={**tags, "Name": f"prompt-guard-{environment}-private-rt-{i}"},
    )

    aws.ec2.RouteTableAssociation(
        f"prompt-guard-private-rta-{i}",
        subnet_id=subnet.id,
        route_table_id=rt.id,
    )

# Security Groups
alb_sg = aws.ec2.SecurityGroup(
    "prompt-guard-alb-sg",
    vpc_id=vpc.id,
    description="Security group for ALB",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={**tags, "Name": f"prompt-guard-{environment}-alb-sg"},
)

ecs_sg = aws.ec2.SecurityGroup(
    "prompt-guard-ecs-sg",
    vpc_id=vpc.id,
    description="Security group for ECS tasks",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            security_groups=[alb_sg.id],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={**tags, "Name": f"prompt-guard-{environment}-ecs-sg"},
)

redis_sg = aws.ec2.SecurityGroup(
    "prompt-guard-redis-sg",
    vpc_id=vpc.id,
    description="Security group for Redis",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=6379,
            to_port=6379,
            security_groups=[ecs_sg.id],
        )
    ],
    tags={**tags, "Name": f"prompt-guard-{environment}-redis-sg"},
)

rds_sg = aws.ec2.SecurityGroup(
    "prompt-guard-rds-sg",
    vpc_id=vpc.id,
    description="Security group for RDS",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            security_groups=[ecs_sg.id],
        )
    ],
    tags={**tags, "Name": f"prompt-guard-{environment}-rds-sg"},
)

# ElastiCache Redis Subnet Group
redis_subnet_group = aws.elasticache.SubnetGroup(
    "prompt-guard-redis-subnet-group",
    subnet_ids=[s.id for s in private_subnets],
    tags={**tags, "Name": f"prompt-guard-{environment}-redis-subnet-group"},
)

# ElastiCache Redis Cluster
redis_cluster = aws.elasticache.Cluster(
    "prompt-guard-redis",
    engine="redis",
    engine_version="7.0",
    node_type=redis_node_type,
    num_cache_nodes=1,
    port=6379,
    subnet_group_name=redis_subnet_group.name,
    security_group_ids=[redis_sg.id],
    tags={**tags, "Name": f"prompt-guard-{environment}-redis"},
)

# RDS Subnet Group
rds_subnet_group = aws.rds.SubnetGroup(
    "prompt-guard-rds-subnet-group",
    subnet_ids=[s.id for s in private_subnets],
    tags={**tags, "Name": f"prompt-guard-{environment}-rds-subnet-group"},
)

# RDS PostgreSQL Instance
rds_instance = aws.rds.Instance(
    "prompt-guard-rds",
    engine="postgres",
    engine_version="15.4",
    instance_class=rds_instance_class,
    allocated_storage=100,
    storage_type="gp3",
    db_name="prompt_guard",
    username="postgres",
    password=config.require_secret("db-password"),
    db_subnet_group_name=rds_subnet_group.name,
    vpc_security_group_ids=[rds_sg.id],
    multi_az=True if environment == "production" else False,
    backup_retention_period=30,
    backup_window="03:00-04:00",
    maintenance_window="mon:04:00-mon:05:00",
    skip_final_snapshot=True if environment != "production" else False,
    final_snapshot_identifier=f"prompt-guard-{environment}-final-snapshot" if environment == "production" else None,
    tags={**tags, "Name": f"prompt-guard-{environment}-rds"},
)

# Application Load Balancer
alb = aws.lb.LoadBalancer(
    "prompt-guard-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=[s.id for s in public_subnets],
    enable_deletion_protection=True if environment == "production" else False,
    tags={**tags, "Name": f"prompt-guard-{environment}-alb"},
)

# ALB Target Group
target_group = aws.lb.TargetGroup(
    "prompt-guard-tg",
    port=8000,
    protocol="HTTP",
    vpc_id=vpc.id,
    target_type="ip",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        healthy_threshold=2,
        interval=30,
        matcher="200",
        path="/health",
        port="traffic-port",
        protocol="HTTP",
        timeout=5,
        unhealthy_threshold=2,
    ),
    tags={**tags, "Name": f"prompt-guard-{environment}-tg"},
)

# ALB Listener
listener = aws.lb.Listener(
    "prompt-guard-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        )
    ],
)

# ECS Cluster
ecs_cluster = aws.ecs.Cluster(
    "prompt-guard-cluster",
    name=f"prompt-guard-{environment}",
    settings=[
        aws.ecs.ClusterSettingArgs(
            name="containerInsights",
            value="enabled",
        )
    ],
    tags=tags,
)

# IAM Role for ECS Task Execution
task_execution_role = aws.iam.Role(
    "prompt-guard-task-execution-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Effect": "Allow"
        }]
    }""",
    tags=tags,
)

aws.iam.RolePolicyAttachment(
    "prompt-guard-task-execution-policy",
    role=task_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
)

# IAM Role for ECS Task
task_role = aws.iam.Role(
    "prompt-guard-task-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Effect": "Allow"
        }]
    }""",
    tags=tags,
)

# CloudWatch Log Group
log_group = aws.cloudwatch.LogGroup(
    "prompt-guard-logs",
    name=f"/ecs/prompt-guard-{environment}",
    retention_in_days=30,
    tags=tags,
)

# ECS Task Definition
task_definition = aws.ecs.TaskDefinition(
    "prompt-guard-task",
    family=f"prompt-guard-{environment}",
    cpu=str(ecs_cpu),
    memory=str(ecs_memory),
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=task_execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=Output.all(
        redis_cluster.cache_nodes[0].address,
        rds_instance.endpoint,
    ).apply(lambda args: f"""[
        {{
            "name": "proxy",
            "image": "ghcr.io/nik-kale/llm-slm-prompt-guard/proxy:latest",
            "cpu": {ecs_cpu},
            "memory": {ecs_memory},
            "essential": true,
            "portMappings": [
                {{
                    "containerPort": 8000,
                    "protocol": "tcp"
                }}
            ],
            "environment": [
                {{
                    "name": "REDIS_URL",
                    "value": "redis://{args[0]}:6379"
                }},
                {{
                    "name": "POSTGRES_URL",
                    "value": "postgresql://postgres:${{DB_PASSWORD}}@{args[1]}/prompt_guard"
                }},
                {{
                    "name": "POLICY",
                    "value": "{pii_policy}"
                }},
                {{
                    "name": "LOG_LEVEL",
                    "value": "INFO"
                }}
            ],
            "logConfiguration": {{
                "logDriver": "awslogs",
                "options": {{
                    "awslogs-group": "{log_group.name}",
                    "awslogs-region": "{aws.config.region}",
                    "awslogs-stream-prefix": "ecs"
                }}
            }}
        }}
    ]"""),
    tags=tags,
)

# ECS Service
service = aws.ecs.Service(
    "prompt-guard-service",
    cluster=ecs_cluster.arn,
    desired_count=ecs_desired_count,
    launch_type="FARGATE",
    task_definition=task_definition.arn,
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=[s.id for s in private_subnets],
        security_groups=[ecs_sg.id],
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=target_group.arn,
            container_name="proxy",
            container_port=8000,
        )
    ],
    tags=tags,
    opts=pulumi.ResourceOptions(depends_on=[listener]),
)

# Auto Scaling Target
autoscaling_target = aws.appautoscaling.Target(
    "prompt-guard-autoscaling-target",
    max_capacity=10,
    min_capacity=ecs_desired_count,
    resource_id=Output.concat("service/", ecs_cluster.name, "/", service.name),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)

# Auto Scaling Policy (CPU-based)
autoscaling_policy = aws.appautoscaling.Policy(
    "prompt-guard-autoscaling-policy",
    policy_type="TargetTrackingScaling",
    resource_id=autoscaling_target.resource_id,
    scalable_dimension=autoscaling_target.scalable_dimension,
    service_namespace=autoscaling_target.service_namespace,
    target_tracking_scaling_policy_configuration=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
        predefined_metric_specification=aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
            predefined_metric_type="ECSServiceAverageCPUUtilization",
        ),
        target_value=70.0,
        scale_in_cooldown=300,
        scale_out_cooldown=60,
    ),
)

# Exports
pulumi.export("vpc_id", vpc.id)
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("alb_endpoint", Output.concat("http://", alb.dns_name))
pulumi.export("redis_endpoint", redis_cluster.cache_nodes[0].address)
pulumi.export("rds_endpoint", rds_instance.endpoint)
pulumi.export("ecs_cluster_name", ecs_cluster.name)
pulumi.export("log_group_name", log_group.name)
