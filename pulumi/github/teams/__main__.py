#!/usr/bin/env python

import yaml

import pulumi_github as github


class Organization:
    def setup_team(self, team, parent_team=None):
        team_resource = github.Team(
            team.get("slug", team["name"].lower().replace(" ", "-")),
            name=team["name"],
            description=team.get("description", ""),
            privacy=team.get("privacy", "closed"),
            parent_team_id=parent_team,
        )

        if team.get("membersYAML"):
            with open(team.get("membersYAML")) as members_fd:
                members = yaml.safe_load(members_fd)
        else:
            members = team["members"]

        for user in members:
            # Add a user to the newly created team
            # team_membership =
            github.TeamMembership(
                f"{team['name']}-{user['name']}",
                team_id=team_resource,
                username=user["name"],
                role=user.get("role", "member"),
            )
            # TODO pulumi.export("team_membership",team_memebership.name)

        for repo in team.get("repositories", []):
            if repo["name"] not in self._repos:
                print(f"Repository '{repo['name']}' not managed by Pulumi. Skipping.")
                continue

            # Associate a repository with the team
            # team_repository =
            github.TeamRepository(
                f"{team['name']}-{repo['name']}",
                team_id=team_resource,
                repository=self._repos[repo["name"]],
                permission=repo.get("permission", "pull"),
            )
            # TODO pulumi.export("team_repository",team_memebership.name)

        for subteam in team.get("teams", []):
            self.setup_team(subteam, parent_team=team_resource)

    def __init__(self, org_file):
        self._repos = {}
        with open(org_file) as org_fd:
            self._org = yaml.safe_load(org_fd)

        for repo in self._org.get("repositories", []):
            self._repos[repo["name"]] = github.Repository(
                repo["name"],
                name=repo["name"],
                description=repo.get("description", ""),
                visibility=repo.get("visibility", "private"),
                has_issues=repo.get("has_issues", True),
                has_projects=repo.get("has_projects", True),
                has_wiki=repo.get("has_wiki", False),
                has_downloads=repo.get("has_downloads", False),
                allow_merge_commit=repo.get("allow_merge_commit", True),
                allow_rebase_merge=repo.get("allow_rebase_merge", True),
                allow_squash_merge=repo.get("allow_squash_merge", True),
                merge_commit_message=repo.get("merge_commit_message"),
                merge_commit_title=repo.get("merge_commit_title"),
                squash_merge_commit_message=repo.get("squash_merge_commit_message"),
                squash_merge_commit_title=repo.get("squash_merge_commit_title"),
            )

        for team in self._org.get("teams", []):
            self.setup_team(team)


Organization("org.yaml")
