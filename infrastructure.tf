# import {
#   to = github_team.infrastructure
#   id = "infrastructure"
# }

resource "github_team" "infrastructure" {
  description = "The best team according to them"
  # id                        = "8796434"
  name           = "infrastructure"
  parent_team_id = null
  privacy        = "closed"
}
