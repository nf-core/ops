variable "gh_token" {
  description = "Token for GitHub"
  type        = string
  sensitive   = true
}

variable "billing_email" {
  description = "Who to send the bill to"
  type        = string
  sensitive   = true
}

variable "pipelines" {
  description = "All of the pipelines"
  type        = list(string)
}
