resource "seqera_credential" "towerforge_aws" {
  name          = "TowerForge-AWSMegatests-Dynamic"
  description   = "Dynamically created TowerForge credentials for AWS Megatests compute environments"
  provider_type = "aws"
  workspace_id  = local.workspace_id

  keys = {
    aws = {
      access_key = aws_iam_access_key.towerforge.id
      secret_key = aws_iam_access_key.towerforge.secret
    }
  }

}
