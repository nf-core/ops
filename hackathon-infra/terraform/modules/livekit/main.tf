#------------------------------------------------------------------------------
# Data Sources
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
# Route53 DNS Record
#------------------------------------------------------------------------------
resource "aws_route53_record" "livekit" {
  zone_id = var.hosted_zone_id
  name    = "livekit.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.eip_public_ip]
}

#------------------------------------------------------------------------------
# IAM Role for EC2
#------------------------------------------------------------------------------
resource "aws_iam_role" "livekit" {
  name = "${var.name_prefix}-livekit-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "livekit" {
  name = "${var.name_prefix}-livekit-policy"
  role = aws_iam_role.livekit.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "livekit" {
  name = "${var.name_prefix}-livekit-profile"
  role = aws_iam_role.livekit.name
}

#------------------------------------------------------------------------------
# EC2 Instance
#------------------------------------------------------------------------------
resource "aws_instance" "livekit" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [var.security_group_id]
  subnet_id              = var.subnet_id
  iam_instance_profile   = aws_iam_instance_profile.livekit.name

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    domain             = var.domain
    livekit_api_key    = var.livekit_api_key
    livekit_api_secret = var.livekit_api_secret
    admin_email        = var.admin_email
  }))

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-livekit"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

#------------------------------------------------------------------------------
# Associate Elastic IP
#------------------------------------------------------------------------------
resource "aws_eip_association" "livekit" {
  instance_id   = aws_instance.livekit.id
  allocation_id = var.eip_id
}
