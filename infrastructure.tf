resource "github_team" "infrastructure" {
  description = "The best team according to them"
  name        = "infrastructure"
  # parent_team_id = null
  privacy = "closed"
}

resource "github_team_members" "infrastructure" {
  team_id = github_team.infrastructure.id

  members {
    username = "mashehu"
    role     = "maintainer"
  }

  members {
    username = "mirpedrol"
    role     = "maintainer"
  }
}
