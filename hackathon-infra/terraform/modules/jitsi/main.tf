#------------------------------------------------------------------------------
# Data Sources
#------------------------------------------------------------------------------
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

#------------------------------------------------------------------------------
# Route53 DNS Record
#------------------------------------------------------------------------------
resource "aws_route53_record" "jitsi" {
  zone_id = var.hosted_zone_id
  name    = "meet.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.eip_public_ip]
}

#------------------------------------------------------------------------------
# IAM Role for EC2
#------------------------------------------------------------------------------
resource "aws_iam_role" "jitsi" {
  name = "${var.name_prefix}-jitsi-role"

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

resource "aws_iam_role_policy" "jitsi" {
  name = "${var.name_prefix}-jitsi-policy"
  role = aws_iam_role.jitsi.id

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

resource "aws_iam_instance_profile" "jitsi" {
  name = "${var.name_prefix}-jitsi-profile"
  role = aws_iam_role.jitsi.name
}

#------------------------------------------------------------------------------
# EC2 Instance
#------------------------------------------------------------------------------
resource "aws_instance" "jitsi" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [var.security_group_id]
  subnet_id              = var.subnet_id
  iam_instance_profile   = aws_iam_instance_profile.jitsi.name

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    domain       = var.domain
    jitsi_secret = var.jitsi_secret
    admin_email  = var.admin_email
    public_ip    = var.eip_public_ip
  }))

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-jitsi"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

#------------------------------------------------------------------------------
# Associate Elastic IP
#------------------------------------------------------------------------------
resource "aws_eip_association" "jitsi" {
  instance_id   = aws_instance.jitsi.id
  allocation_id = var.eip_id
}
