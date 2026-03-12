output "instance_id" {
  description = "ID of the Jitsi EC2 instance"
  value       = aws_instance.jitsi.id
}

output "public_ip" {
  description = "Public IP of the Jitsi instance (Elastic IP)"
  value       = var.eip_public_ip
}

output "jitsi_url" {
  description = "Jitsi Meet URL"
  value       = "https://meet.${var.domain}"
}

output "jitsi_domain" {
  description = "Jitsi domain (for WorkAdventure config)"
  value       = "meet.${var.domain}"
}

output "dns_name" {
  description = "DNS name for Jitsi"
  value       = "meet.${var.domain}"
}
