import {
  to = seqera_workspace.dev
  id = "{\"id\": 85085054091044, \"org_id\": 252464779077610}"
}

resource "seqera_workspace" "dev" {
  name        = "AWSmegatests-dev"
  full_name   = "AWS Megatests (dev)"
  description = "Development workspace for AWS megatests — launches from dev branch"
  org_id      = var.seqera_org_id
  visibility  = "SHARED"
}
