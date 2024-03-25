#!/usr/bin/env python

import yaml

import pulumi
import pulumi_github as github

class Organization:
    def setup_team(self, team):
        team_resource = github.Team(team["slug"],
            name=team["name"],
            description=team.get("description", ""),
            privacy="closed",
            # opts=pulumi.ResourceOptions(protect=True)
        )

        for user in team["members"]:
            # Add a user to the newly created team
            team_membership = github.TeamMembership(f"{team['name']}-{user['name']}",
                team_id=team["name"],
                username=user["name"],
                role=user.get("role", "member"),
                opts=pulumi.ResourceOptions(depends_on=[team_resource])
            )

        for repo in team.get("repositories", []):
            # Associate a repository with the team
            team_repository = github.TeamRepository(f"{team['name']}-{repo['name']}",
                team_id=team["name"],
                repository=repo["name"],
                permission=repo.get("permission", "pull"),
                opts=pulumi.ResourceOptions(depends_on=[self._repos[repo["name"]]])
            )

        for subteam in team.get("teams", []):
            self.setup_team(subteam)

    def __init__(self, org_file):
        self._repos = {}
        with open(org_file) as org_fd:
            self._org = yaml.safe_load(org_fd)

        for repo in self._org["repositories"]:
            self._repos[repo["name"]] = github.Repository(
                repo["name"],
                name=repo["name"],
                description=repo.get("description", ""),
                visibility=repo.get("visibility", "private")
            )

        for team in self._org["teams"]:
            self.setup_team(team)

Organization('org.yaml')
