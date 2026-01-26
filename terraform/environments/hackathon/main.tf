# Main Terraform Configuration for nf-core Hackathon
# WorkAdventure Infrastructure
#
# CONFIGURATION: This file reads all configuration from environment variables.
# Use 1Password Environments to mount the .env file in the project root.
# See .env.example for setup instructions.

#------------------------------------------------------------------------------
# Configuration Variables (from environment via .env file)
#------------------------------------------------------------------------------
variable "AWS_REGION" {
  description = "AWS region for deployment"
  type        = string
}

variable "DOMAIN" {
  description = "Base domain for all services (e.g., hackathon.example.com)"
  type        = string
}

variable "ROUTE53_ZONE_ID" {
  description = "Route53 hosted zone ID for the domain"
  type        = string
}

variable "PROJECT_NAME" {
  description = "Project name prefix for all resources"
  type        = string
}

variable "SSH_KEY_NAME" {
  description = "Name of SSH key in 1Password (for EC2 instances)"
  type        = string
}

variable "ADMIN_EMAIL" {
  description = "Admin email for Let's Encrypt certificates"
  type        = string
}

#------------------------------------------------------------------------------
# Secrets (from environment via .env file)
#------------------------------------------------------------------------------
variable "WORKADVENTURE_SECRET_KEY" {
  description = "Secret key for WorkAdventure"
  type        = string
  sensitive   = true
}

variable "LIVEKIT_API_KEY" {
  description = "LiveKit API key"
  type        = string
  sensitive   = true
}

variable "LIVEKIT_API_SECRET" {
  description = "LiveKit API secret"
  type        = string
  sensitive   = true
}

variable "COTURN_SECRET" {
  description = "Coturn TURN server secret"
  type        = string
  sensitive   = true
}

variable "JITSI_SECRET" {
  description = "Jitsi authentication secret"
  type        = string
  sensitive   = true
}

#------------------------------------------------------------------------------
# GitHub OAuth Authentication (Milestone 8)
#------------------------------------------------------------------------------
variable "GITHUB_OAUTH_CLIENT_ID" {
  description = "GitHub OAuth App Client ID for authentication"
  type        = string
  sensitive   = true
}

variable "GITHUB_OAUTH_CLIENT_SECRET" {
  description = "GitHub OAuth App Client Secret"
  type        = string
  sensitive   = true
}

variable "OAUTH2_PROXY_COOKIE_SECRET" {
  description = "Cookie secret for oauth2-proxy (generate: openssl rand -base64 32)"
  type        = string
  sensitive   = true
}

#------------------------------------------------------------------------------
# Instance Type Configuration (override via TF_VAR_* in .env)
#------------------------------------------------------------------------------
variable "workadventure_instance_type" {
  description = "EC2 instance type for WorkAdventure"
  type        = string
  default     = "t3.xlarge"
}

variable "livekit_instance_type" {
  description = "EC2 instance type for LiveKit"
  type        = string
  default     = "c5.xlarge"
}

variable "coturn_instance_type" {
  description = "EC2 instance type for Coturn"
  type        = string
  default     = "t3.medium"
}

variable "jitsi_instance_type" {
  description = "EC2 instance type for Jitsi"
  type        = string
  default     = "t3.medium"
}

#------------------------------------------------------------------------------
# Local Values
#------------------------------------------------------------------------------
locals {
  # Common tags applied to all resources
  common_tags = {
    Project     = var.PROJECT_NAME
    Environment = "hackathon"
    ManagedBy   = "terraform"
  }
}

# Data source for the Route53 hosted zone
data "aws_route53_zone" "hackathon" {
  zone_id = var.ROUTE53_ZONE_ID
}

#------------------------------------------------------------------------------
# VPC Module (Milestone 1)
#------------------------------------------------------------------------------
module "vpc" {
  source = "../../modules/vpc"

  name_prefix = var.PROJECT_NAME
  vpc_cidr    = "10.0.0.0/16"

  availability_zones  = ["${var.AWS_REGION}a", "${var.AWS_REGION}b"]
  public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]

  tags = local.common_tags
}

#------------------------------------------------------------------------------
# WorkAdventure Module (Milestone 2)
#------------------------------------------------------------------------------
module "workadventure" {
  source = "../../modules/workadventure"

  name_prefix           = var.PROJECT_NAME
  domain                = var.DOMAIN
  hosted_zone_id        = var.ROUTE53_ZONE_ID
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  ec2_security_group_id = module.vpc.workadventure_security_group_id

  # Instance configuration
  instance_type = var.workadventure_instance_type
  key_name      = var.SSH_KEY_NAME
  admin_email   = var.ADMIN_EMAIL

  # Secrets from environment variables (via .env file)
  workadventure_secret_key = var.WORKADVENTURE_SECRET_KEY

  # LiveKit integration (Milestone 3)
  livekit_url        = module.livekit.livekit_ws_url
  livekit_api_key    = var.LIVEKIT_API_KEY
  livekit_api_secret = var.LIVEKIT_API_SECRET

  # TURN integration (Milestone 4)
  turn_server = module.coturn.turn_url
  turn_secret = var.COTURN_SECRET

  # Jitsi integration (Milestone 7 - for meeting room zones)
  # Note: Using try() with fallback to prevent cascading failures if Jitsi is destroyed
  jitsi_url = try(module.jitsi.jitsi_domain, "")

  # GitHub OAuth authentication (Milestone 8)
  github_oauth_client_id     = var.GITHUB_OAUTH_CLIENT_ID
  github_oauth_client_secret = var.GITHUB_OAUTH_CLIENT_SECRET
  oauth2_proxy_cookie_secret = var.OAUTH2_PROXY_COOKIE_SECRET
  github_org                 = "nf-core"

  tags = local.common_tags

  # REMOVED: depends_on = [module.livekit, module.coturn, module.jitsi]
  # The explicit depends_on was REMOVED because:
  # 1. Implicit dependencies through variable passing are sufficient
  # 2. Explicit depends_on causes cascading destroys when any dependency is destroyed
  # 3. It makes targeted operations dangerous (destroy jitsi -> destroy workadventure)
  # See CLAUDE.md "Root Cause Analysis" for full details on the January 2026 incident
}

#------------------------------------------------------------------------------
# LiveKit Module (Milestone 3)
#------------------------------------------------------------------------------
module "livekit" {
  source = "../../modules/livekit"

  name_prefix       = var.PROJECT_NAME
  domain            = var.DOMAIN
  hosted_zone_id    = var.ROUTE53_ZONE_ID
  vpc_id            = module.vpc.vpc_id
  subnet_id         = module.vpc.public_subnet_ids[0]
  security_group_id = module.vpc.livekit_security_group_id
  eip_id            = module.vpc.livekit_eip_id
  eip_public_ip     = module.vpc.livekit_eip_public_ip

  # Instance configuration
  instance_type = var.livekit_instance_type
  key_name      = var.SSH_KEY_NAME

  # Secrets from environment variables (via .env file)
  livekit_api_key    = var.LIVEKIT_API_KEY
  livekit_api_secret = var.LIVEKIT_API_SECRET

  admin_email = var.ADMIN_EMAIL

  tags = local.common_tags
}

#------------------------------------------------------------------------------
# Coturn Module (Milestone 4)
#------------------------------------------------------------------------------
module "coturn" {
  source = "../../modules/coturn"

  name_prefix       = var.PROJECT_NAME
  domain            = var.DOMAIN
  hosted_zone_id    = var.ROUTE53_ZONE_ID
  vpc_id            = module.vpc.vpc_id
  subnet_id         = module.vpc.public_subnet_ids[0]
  security_group_id = module.vpc.coturn_security_group_id
  eip_id            = module.vpc.coturn_eip_id
  eip_public_ip     = module.vpc.coturn_eip_public_ip

  # Instance configuration
  instance_type = var.coturn_instance_type
  key_name      = var.SSH_KEY_NAME

  # Secret from environment variable (via .env file)
  turn_secret = var.COTURN_SECRET

  admin_email = var.ADMIN_EMAIL

  tags = local.common_tags
}

#------------------------------------------------------------------------------
# Jitsi Module (Milestone 7)
#------------------------------------------------------------------------------
module "jitsi" {
  source = "../../modules/jitsi"

  name_prefix       = var.PROJECT_NAME
  domain            = var.DOMAIN
  hosted_zone_id    = var.ROUTE53_ZONE_ID
  vpc_id            = module.vpc.vpc_id
  subnet_id         = module.vpc.public_subnet_ids[0]
  security_group_id = module.vpc.jitsi_security_group_id
  eip_id            = module.vpc.jitsi_eip_id
  eip_public_ip     = module.vpc.jitsi_eip_public_ip

  # Instance configuration
  instance_type = var.jitsi_instance_type
  key_name      = var.SSH_KEY_NAME

  # Secret from environment variable (via .env file)
  jitsi_secret = var.JITSI_SECRET

  admin_email = var.ADMIN_EMAIL

  tags = local.common_tags
}
