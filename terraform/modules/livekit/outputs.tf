output "instance_id" {
  description = "ID of the LiveKit EC2 instance"
  value       = aws_instance.livekit.id
}

output "public_ip" {
  description = "Public IP of the LiveKit instance (Elastic IP)"
  value       = var.eip_public_ip
}

output "livekit_url" {
  description = "URL for LiveKit server"
  value       = "https://livekit.${var.domain}"
}

output "livekit_ws_url" {
  description = "WebSocket URL for LiveKit"
  value       = "wss://livekit.${var.domain}"
}
