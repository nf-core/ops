output "instance_id" {
  description = "ID of the Coturn EC2 instance"
  value       = aws_instance.coturn.id
}

output "public_ip" {
  description = "Public IP of the Coturn instance (Elastic IP)"
  value       = var.eip_public_ip
}

output "turn_url" {
  description = "TURN server URL"
  value       = "turn:turn.${var.domain}:3478"
}

output "turns_url" {
  description = "TURNS (TLS) server URL"
  value       = "turns:turn.${var.domain}:5349"
}

output "turn_domain" {
  description = "TURN server domain"
  value       = "turn.${var.domain}"
}
