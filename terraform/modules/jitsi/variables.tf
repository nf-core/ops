variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "hackathon"
}

variable "domain" {
  description = "Base domain (e.g., hackathon.nf-co.re)"
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

variable "subnet_id" {
  description = "Subnet ID for the EC2 instance"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID for Jitsi"
  type        = string
}

variable "eip_id" {
  description = "Elastic IP allocation ID"
  type        = string
}

variable "eip_public_ip" {
  description = "Elastic IP public address"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
  default     = "nfcore-hackathon"
}

variable "jitsi_secret" {
  description = "JWT secret for Jitsi authentication"
  type        = string
  sensitive   = true
}

variable "admin_email" {
  description = "Email for Let's Encrypt certificate"
  type        = string
  default     = "admin@nf-co.re"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
