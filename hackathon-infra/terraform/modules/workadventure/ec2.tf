#------------------------------------------------------------------------------
# Get Latest Amazon Linux 2023 AMI
#------------------------------------------------------------------------------
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

#------------------------------------------------------------------------------
# EC2 Instance
#------------------------------------------------------------------------------
resource "aws_instance" "workadventure" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [var.ec2_security_group_id]
  subnet_id              = var.public_subnet_ids[0]
  iam_instance_profile   = aws_iam_instance_profile.workadventure.name

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    domain                   = var.domain
    workadventure_secret_key = var.workadventure_secret_key
    livekit_url              = var.livekit_url
    livekit_api_key          = var.livekit_api_key
    livekit_api_secret       = var.livekit_api_secret
    turn_server              = var.turn_server
    turn_secret              = var.turn_secret
    jitsi_url                = var.jitsi_url
    admin_email              = var.admin_email
    # GitHub OAuth (Milestone 8)
    github_oauth_client_id     = var.github_oauth_client_id
    github_oauth_client_secret = var.github_oauth_client_secret
    oauth2_proxy_cookie_secret = var.oauth2_proxy_cookie_secret
    github_org                 = var.github_org
  }))

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-workadventure"
  })

  lifecycle {
    # IMPORTANT: user_data changes would normally force instance replacement.
    # We ignore user_data changes to prevent cascading destroys when:
    # - Secrets are rotated
    # - LiveKit/Coturn/Jitsi URLs change
    # - Any integration variable changes
    # For runtime config changes, use SSM Parameter Store or SSH into the instance.
    # See CLAUDE.md for the full rationale (January 2026 incident).
    ignore_changes = [ami, user_data]
  }
}

resource "aws_lb_target_group_attachment" "workadventure" {
  target_group_arn = aws_lb_target_group.workadventure.arn
  target_id        = aws_instance.workadventure.id
  port             = 80
}
