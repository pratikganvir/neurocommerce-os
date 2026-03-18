terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "neurocommerce-vpc"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name            = "neurocommerce-cluster"
  role_arn        = aws_iam_role.eks_role.arn
  version         = "1.28"

  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }

  depends_on = [aws_iam_role_policy_attachment.eks_policy]

  tags = {
    Name = "neurocommerce-cluster"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier           = "neurocommerce-postgres"
  engine               = "postgres"
  engine_version       = "15.3"
  instance_class       = "db.t3.medium"
  allocated_storage    = 100
  storage_type         = "gp3"
  
  db_name  = "neurocommerce"
  username = "neurocommerce"
  password = random_password.db_password.result
  
  multi_az               = true
  publicly_accessible    = false
  skip_final_snapshot    = false
  final_snapshot_identifier = "neurocommerce-postgres-final-snapshot"

  tags = {
    Name = "neurocommerce-postgres"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "neurocommerce-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  tags = {
    Name = "neurocommerce-redis"
  }
}

# MSK Kafka Cluster
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "neurocommerce-kafka"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    ebs_volume_size = 100
    client_subnets = aws_subnet.private[*].id
  }

  tags = {
    Name = "neurocommerce-kafka"
  }
}

# Random password for DB
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

# Outputs
output "eks_cluster_name" {
  value = aws_eks_cluster.main.name
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
