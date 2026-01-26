#------------------------------------------------------------------------------
# Data Sources
#------------------------------------------------------------------------------
data "aws_region" "current" {}

#------------------------------------------------------------------------------
# Random suffix for globally unique bucket name
#------------------------------------------------------------------------------
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

#------------------------------------------------------------------------------
# S3 Bucket for Map Storage
#------------------------------------------------------------------------------
resource "aws_s3_bucket" "maps" {
  bucket = "${var.name_prefix}-maps-${random_id.bucket_suffix.hex}"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-maps"
  })

  # PROTECTION: Prevent accidental deletion of maps bucket
  # This bucket contains uploaded map files that may be difficult to recreate.
  # To destroy: first set prevent_destroy = false, then run terraform apply, then destroy.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "maps" {
  bucket = aws_s3_bucket.maps.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_cors_configuration" "maps" {
  bucket = aws_s3_bucket.maps.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_public_access_block" "maps" {
  bucket = aws_s3_bucket.maps.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "maps" {
  bucket     = aws_s3_bucket.maps.id
  depends_on = [aws_s3_bucket_public_access_block.maps]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadMaps"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.maps.arn}/maps/*"
      },
      {
        Sid       = "PublicReadAssets"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.maps.arn}/assets/*"
      }
    ]
  })
}
