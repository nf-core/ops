
process GITHUB_DAILY_TRAFFIC {
    conda "steampipe=0.23.5 jq=1.7.1"

    input:
    val repo
    path sql_file


    script:
    """
    steampipe query $sql_file \\
        --output json \\
        --var=repo_name=$repo \\
        | jq '.rows[0] + {timestamp: now|tostring}' \\
        >> hf_stats/steampipe/github.json"
    """

}

workflow github {
    GITHUB_DAILY_TRAFFIC (
        "${projectDir}/github_daily_traffic.sql"
    )
}
