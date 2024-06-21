import pulumi
import pulumi_github as github

# Create a new GitHub team within the nf-core organization
my_team = github.Team(
    "myTeam",
    name="my-team",
    description="My Team Description",
    privacy="closed",  # Can be 'secret' or 'closed'
)

# Add a user to the newly created team
team_membership = github.TeamMembership(
    "teamMembership",
    team_id=my_team.id,
    username="example-user",  # Replace with the actual GitHub username
    role="member",  # Can be 'member' or 'maintainer'
)

# Associate a repository with the team
team_repository = github.TeamRepository(
    "teamRepository",
    team_id=my_team.id,
    repository="example-repo",  # Replace with the actual repository name
    permission="push",  # Can be 'pull', 'push', or 'admin'
)

# Export the team slug to access the team on GitHub
pulumi.export("team_slug", my_team.slug)
