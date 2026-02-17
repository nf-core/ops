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
resource "aws_route53_record" "coturn" {
  zone_id = var.hosted_zone_id
  name    = "turn.${var.domain}"
  type    = "A"
  ttl     = 300
  records = [var.eip_public_ip]
}

#------------------------------------------------------------------------------
# IAM Role for EC2
#------------------------------------------------------------------------------
resource "aws_iam_role" "coturn" {
  name = "${var.name_prefix}-coturn-role"

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

resource "aws_iam_role_policy" "coturn" {
  name = "${var.name_prefix}-coturn-policy"
  role = aws_iam_role.coturn.id

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

resource "aws_iam_instance_profile" "coturn" {
  name = "${var.name_prefix}-coturn-profile"
  role = aws_iam_role.coturn.name
}

#------------------------------------------------------------------------------
# EC2 Instance
#------------------------------------------------------------------------------
resource "aws_instance" "coturn" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [var.security_group_id]
  subnet_id              = var.subnet_id
  iam_instance_profile   = aws_iam_instance_profile.coturn.name

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    domain      = var.domain
    turn_secret = var.turn_secret
    admin_email = var.admin_email
    public_ip   = var.eip_public_ip
  }))

  root_block_device {
    volume_size = 30 # Amazon Linux 2023 requires minimum 30GB
    volume_type = "gp3"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-coturn"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

#------------------------------------------------------------------------------
# Associate Elastic IP
#------------------------------------------------------------------------------
resource "aws_eip_association" "coturn" {
  instance_id   = aws_instance.coturn.id
  allocation_id = var.eip_id
}
