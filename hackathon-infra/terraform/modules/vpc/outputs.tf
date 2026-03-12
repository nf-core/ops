output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "workadventure_security_group_id" {
  description = "ID of the WorkAdventure security group"
  value       = aws_security_group.workadventure.id
}

output "livekit_security_group_id" {
  description = "ID of the LiveKit security group"
  value       = aws_security_group.livekit.id
}

output "coturn_security_group_id" {
  description = "ID of the Coturn security group"
  value       = aws_security_group.coturn.id
}

output "livekit_eip_id" {
  description = "Allocation ID of the LiveKit Elastic IP"
  value       = aws_eip.livekit.id
}

output "livekit_eip_public_ip" {
  description = "Public IP of the LiveKit Elastic IP"
  value       = aws_eip.livekit.public_ip
}

output "coturn_eip_id" {
  description = "Allocation ID of the Coturn Elastic IP"
  value       = aws_eip.coturn.id
}

output "coturn_eip_public_ip" {
  description = "Public IP of the Coturn Elastic IP"
  value       = aws_eip.coturn.public_ip
}

output "jitsi_security_group_id" {
  description = "ID of the Jitsi security group"
  value       = aws_security_group.jitsi.id
}

output "jitsi_eip_id" {
  description = "Allocation ID of the Jitsi Elastic IP"
  value       = aws_eip.jitsi.id
}

output "jitsi_eip_public_ip" {
  description = "Public IP of the Jitsi Elastic IP"
  value       = aws_eip.jitsi.public_ip
}
