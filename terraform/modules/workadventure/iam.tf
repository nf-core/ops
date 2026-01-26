#------------------------------------------------------------------------------
# IAM Role for WorkAdventure EC2
#------------------------------------------------------------------------------
resource "aws_iam_role" "workadventure" {
  name = "${var.name_prefix}-workadventure-role"

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

resource "aws_iam_role_policy" "workadventure" {
  name = "${var.name_prefix}-workadventure-policy"
  role = aws_iam_role.workadventure.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.maps.arn,
          "${aws_s3_bucket.maps.arn}/*"
        ]
      },
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

resource "aws_iam_instance_profile" "workadventure" {
  name = "${var.name_prefix}-workadventure-profile"
  role = aws_iam_role.workadventure.name
}
