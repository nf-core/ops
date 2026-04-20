import {
  to = aws_s3_bucket.nf_core_awsmegatests
  id = "nf-core-awsmegatests"
}

resource "aws_s3_bucket" "nf_core_awsmegatests" {
  bucket = local.s3_bucket_name

  lifecycle {
    prevent_destroy = true
    ignore_changes  = [lifecycle_rule, versioning]
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "nf_core_awsmegatests" {
  bucket = aws_s3_bucket.nf_core_awsmegatests.id

  # Rule 1: Preserve metadata files with cost optimization
  rule {
    id     = "preserve-metadata-files"
    status = "Enabled"

    filter {
      tag {
        key   = "nextflow.io/metadata"
        value = "true"
      }
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }

  # Rule 2: Clean up temporary files after 30 days
  rule {
    id     = "cleanup-temporary-files"
    status = "Enabled"

    filter {
      tag {
        key   = "nextflow.io/temporary"
        value = "true"
      }
    }

    expiration {
      days = 30
    }
  }

  # Rule 3: Clean up work directory after 30 days
  rule {
    id     = "cleanup-work-directory"
    status = "Enabled"

    filter {
      prefix = "work/"
    }

    expiration {
      days = 30
    }
  }

  # Rule 4: Clean up scratch directory after 30 days
  rule {
    id     = "cleanup-scratch-directory"
    status = "Enabled"

    filter {
      prefix = "scratch/"
    }

    expiration {
      days = 30
    }
  }

  # Rule 5: Clean up cache directories after 30 days
  rule {
    id     = "cleanup-cache-directories"
    status = "Enabled"

    filter {
      prefix = "cache/"
    }

    expiration {
      days = 30
    }
  }

  # Rule 6: Clean up .cache directories after 30 days
  rule {
    id     = "cleanup-dot-cache-directories"
    status = "Enabled"

    filter {
      prefix = ".cache/"
    }

    expiration {
      days = 30
    }
  }

  # Rule 7: Clean up incomplete multipart uploads
  rule {
    id     = "cleanup-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "nf_core_awsmegatests" {
  bucket = aws_s3_bucket.nf_core_awsmegatests.id

  # Seqera Data Explorer access
  cors_rule {
    id              = "SeqeraDataExplorerAccess"
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD", "POST", "PUT", "DELETE"]
    allowed_origins = [
      "https://*.cloud.seqera.io",
      "https://*.tower.nf",
      "https://cloud.seqera.io",
      "https://tower.nf",
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }

  # Direct browser access
  cors_rule {
    id              = "BrowserDirectAccess"
    allowed_headers = ["Authorization", "Content-Type", "Range"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["Content-Range", "Content-Length", "ETag"]
    max_age_seconds = 3000
  }
}
