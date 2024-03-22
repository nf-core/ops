#!/usr/bin/env python

import yaml

import pulumi
import pulumi_github as github

with open('org.yaml') as org_fd:
    org = yaml.safe_load(org_fd)

for repo in org["repositories"]:
    repo = github.Repository(repo["name"],
        name=repo["name"],
        description=repo.get("description", ""),
        visibility=repo.get("visibility", "private"))

for team in org["teams"]:
    ops = github.Team(team["slug"],
        name=team["name"],
        description=team["description"],
        privacy="closed",
        opts=pulumi.ResourceOptions(protect=True))

    for user in team["members"]:
        # Add a user to the newly created team
        team_membership = github.TeamMembership(f"{team['name']}-{user['name']}",
            team_id=team["name"],
            username=user["name"],
            role=user["role"],
        )

    for permission in team["permissions"]:
        # Associate a repository with the team
        team_repository = github.TeamRepository(f"{team['name']}-{permission['repository']}",
            team_id=team["name"],
            repository=permission["repository"],
            permission=permission["role"],
        )
