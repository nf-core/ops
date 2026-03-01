# Outputs for nf-core Hackathon Infrastructure

output "route53_zone_id" {
  description = "Route53 hosted zone ID for hackathon.nf-co.re"
  value       = data.aws_route53_zone.hackathon.zone_id
}

output "route53_zone_name" {
  description = "Route53 hosted zone name"
  value       = data.aws_route53_zone.hackathon.name
}

output "route53_nameservers" {
  description = "Route53 nameservers (add these to parent zone)"
  value       = data.aws_route53_zone.hackathon.name_servers
}

#------------------------------------------------------------------------------
# VPC Outputs (Milestone 1)
#------------------------------------------------------------------------------
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = module.vpc.alb_security_group_id
}

output "workadventure_security_group_id" {
  description = "WorkAdventure security group ID"
  value       = module.vpc.workadventure_security_group_id
}

output "livekit_security_group_id" {
  description = "LiveKit security group ID"
  value       = module.vpc.livekit_security_group_id
}

output "coturn_security_group_id" {
  description = "Coturn security group ID"
  value       = module.vpc.coturn_security_group_id
}

output "livekit_eip_public_ip" {
  description = "LiveKit Elastic IP"
  value       = module.vpc.livekit_eip_public_ip
}

output "coturn_eip_public_ip" {
  description = "Coturn Elastic IP"
  value       = module.vpc.coturn_eip_public_ip
}

#------------------------------------------------------------------------------
# WorkAdventure Outputs (Milestone 2)
#------------------------------------------------------------------------------
output "workadventure_url" {
  description = "WorkAdventure application URL"
  value       = module.workadventure.app_url
}

output "workadventure_alb_dns" {
  description = "WorkAdventure ALB DNS name"
  value       = module.workadventure.alb_dns_name
}

output "workadventure_instance_id" {
  description = "WorkAdventure EC2 instance ID"
  value       = module.workadventure.instance_id
}



#------------------------------------------------------------------------------
# LiveKit Outputs (Milestone 3)
#------------------------------------------------------------------------------
output "livekit_url" {
  description = "LiveKit server URL"
  value       = module.livekit.livekit_url
}

output "livekit_ws_url" {
  description = "LiveKit WebSocket URL"
  value       = module.livekit.livekit_ws_url
}

output "livekit_instance_id" {
  description = "LiveKit EC2 instance ID"
  value       = module.livekit.instance_id
}

#------------------------------------------------------------------------------
# Coturn Outputs (Milestone 4)
#------------------------------------------------------------------------------
output "coturn_turn_url" {
  description = "Coturn TURN server URL"
  value       = module.coturn.turn_url
}

output "coturn_turns_url" {
  description = "Coturn TURNS (TLS) server URL"
  value       = module.coturn.turns_url
}

output "coturn_instance_id" {
  description = "Coturn EC2 instance ID"
  value       = module.coturn.instance_id
}

output "coturn_public_ip" {
  description = "Coturn public IP (Elastic IP)"
  value       = module.coturn.public_ip
}

#------------------------------------------------------------------------------
# Jitsi Outputs (Milestone 7)
#------------------------------------------------------------------------------
output "jitsi_url" {
  description = "Jitsi Meet URL"
  value       = module.jitsi.jitsi_url
}

output "jitsi_instance_id" {
  description = "Jitsi EC2 instance ID"
  value       = module.jitsi.instance_id
}

output "jitsi_public_ip" {
  description = "Jitsi public IP (Elastic IP)"
  value       = module.jitsi.public_ip
}

output "jitsi_eip_public_ip" {
  description = "Jitsi Elastic IP"
  value       = module.vpc.jitsi_eip_public_ip
}

output "jitsi_security_group_id" {
  description = "Jitsi security group ID"
  value       = module.vpc.jitsi_security_group_id
}
