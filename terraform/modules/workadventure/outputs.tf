output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the ALB"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the ALB"
  value       = aws_lb.main.arn
}

output "instance_id" {
  description = "ID of the WorkAdventure EC2 instance"
  value       = aws_instance.workadventure.id
}

output "instance_public_ip" {
  description = "Public IP of the WorkAdventure EC2 instance"
  value       = aws_instance.workadventure.public_ip
}

output "instance_private_ip" {
  description = "Private IP of the WorkAdventure EC2 instance"
  value       = aws_instance.workadventure.private_ip
}

output "app_url" {
  description = "URL for WorkAdventure"
  value       = "https://app.${var.domain}"
}

output "certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.main.arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.workadventure.arn
}
