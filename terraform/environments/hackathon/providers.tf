# Terraform and Provider Configuration for nf-core Hackathon
# WorkAdventure Infrastructure
#
# All configuration is read from environment variables (via .env file).
# Terraform automatically reads TF_VAR_* prefixed variables, but also
# reads variables with matching names directly from the environment.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# AWS Profile variable (from .env)
variable "AWS_PROFILE" {
  description = "AWS CLI profile to use"
  type        = string
}

# AWS Provider
provider "aws" {
  region  = var.AWS_REGION
  profile = var.AWS_PROFILE

  default_tags {
    tags = {
      Project     = var.PROJECT_NAME
      Environment = "hackathon"
      ManagedBy   = "terraform"
    }
  }
}

# Random Provider (for generating unique identifiers)
provider "random" {}
