variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "hackathon"
}

variable "domain" {
  description = "Base domain for the hackathon (e.g., hackathon.nf-co.re)"
  type        = string
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for ALB"
  type        = string
}

variable "ec2_security_group_id" {
  description = "Security group ID for EC2"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.xlarge"
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
  default     = "nfcore-hackathon"
}

variable "admin_email" {
  description = "Admin email for Let's Encrypt certificates"
  type        = string
}

variable "workadventure_secret_key" {
  description = "Secret key for WorkAdventure"
  type        = string
  sensitive   = true
}

variable "livekit_url" {
  description = "LiveKit server URL (optional, can be added later)"
  type        = string
  default     = ""
}

variable "livekit_api_key" {
  description = "LiveKit API key (optional, can be added later)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "livekit_api_secret" {
  description = "LiveKit API secret (optional, can be added later)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "turn_server" {
  description = "TURN server URL (optional, can be added later)"
  type        = string
  default     = ""
}

variable "turn_secret" {
  description = "TURN static auth secret (optional, can be added later)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "jitsi_url" {
  description = "Jitsi Meet server URL without https:// (for meeting room zones)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}

#------------------------------------------------------------------------------
# GitHub OAuth Authentication (Milestone 8)
#------------------------------------------------------------------------------
variable "github_oauth_client_id" {
  description = "GitHub OAuth App Client ID"
  type        = string
  sensitive   = true
}

variable "github_oauth_client_secret" {
  description = "GitHub OAuth App Client Secret"
  type        = string
  sensitive   = true
}

variable "oauth2_proxy_cookie_secret" {
  description = "Cookie encryption secret for oauth2-proxy"
  type        = string
  sensitive   = true
}

variable "github_org" {
  description = "GitHub organization - only members can access"
  type        = string
  default     = "nf-core"
}
