process GITHUB_DAILY_TRAFFIC {
    conda "jq=1.7.1"

    secret 'GH_TOKEN'

    input:
    // val owner
    val repo

    output:
    path "*_daily_traffic.json"

    script:
    """
    curl -L \\
        -H "Accept: application/vnd.github+json" \\
        -H "Authorization: Bearer \$GH_TOKEN" \\
        -H "X-GitHub-Api-Version: 2022-11-28" \\
        https://api.github.com/repos/nf-core/${repo}/traffic/views \\
        > ${repo}_daily_traffic.json
    """
}
// TODO https://docs.github.com/en/rest/metrics/traffic?apiVersion=2022-11-28#get-top-referral-sources--code-samples
// TODO https://docs.github.com/en/rest/metrics/traffic?apiVersion=2022-11-28#get-page-views--status-codes

workflow {
    GITHUB_DAILY_TRAFFIC (
        // "nf-core",
        "methylseq",
    )
}
