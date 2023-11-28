resource "github_repository" "pipelines" {

  for_each = toset(var.pipelines)

  name = each.key
}
