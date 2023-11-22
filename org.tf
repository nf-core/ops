resource "github_organization_settings" "nf-core" {
    advanced_security_enabled_for_new_repositories               = false
    billing_email                                                = var.billing_email
    blog                                                         = "http://nf-co.re"
    default_repository_permission                                = "read"
    dependabot_alerts_enabled_for_new_repositories               = false
    dependabot_security_updates_enabled_for_new_repositories     = false
    dependency_graph_enabled_for_new_repositories                = false
    description                                                  = "A community effort to collect a curated set of analysis pipelines built using Nextflow."
    email                                                        = "core@nf-co.re"
    has_organization_projects                                    = true
    has_repository_projects                                      = true
    members_can_create_internal_repositories                     = false
    members_can_create_pages                                     = false
    members_can_create_private_pages                             = false
    members_can_create_private_repositories                      = false
    members_can_create_public_pages                              = false
    members_can_create_public_repositories                       = false
    members_can_create_repositories                              = false
    members_can_fork_private_repositories                        = false
    name                                                         = "nf-core"
    secret_scanning_enabled_for_new_repositories                 = false
    secret_scanning_push_protection_enabled_for_new_repositories = false
    twitter_username                                             = "nf_core"
    web_commit_signoff_required                                  = false
}
