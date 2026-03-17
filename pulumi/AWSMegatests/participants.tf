resource "null_resource" "team_data_setup" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "uv run python scripts/setup_team_data.py"

    environment = {
      GITHUB_TOKEN = local.github_token
      # TOWER_ACCESS_TOKEN inherited from env (.envrc)
    }
  }
}

resource "null_resource" "workspace_participants" {
  depends_on = [null_resource.team_data_setup]

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "uv run scripts/add_maintainers_to_workspace.py --yes"

    environment = {
      TOWER_WORKSPACE_ID = local.workspace_id
      # TOWER_ACCESS_TOKEN inherited from env (.envrc)
    }
  }
}
