#!/usr/bin/env python3
# /// script
# dependencies = [
#   "boto3",
#   "requests",
# ]
# ///
"""
nf-core Test Coverage Report Generator

This script generates comprehensive reports showing:
- All nf-core pipelines and their releases
- Which releases have test results in S3
- Which releases are missing test results
- Coverage statistics and actionable insights

The script outputs reports in multiple formats:
- Markdown (for GitHub Actions summaries)
- CSV (for data analysis)
- JSON (for programmatic access)
"""

import boto3
import requests
import sys
import argparse
import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PipelineRelease:
    """Data class for pipeline release information"""

    pipeline: str
    version: str
    tag_name: str
    sha: str
    published_at: str
    is_prerelease: bool
    has_test_results: bool = False


@dataclass
class PipelineCoverage:
    """Data class for pipeline test coverage statistics"""

    pipeline: str
    total_releases: int
    tested_releases: int
    coverage_percentage: float
    missing_releases: List[str]
    latest_release: Optional[str]
    latest_release_tested: bool


@dataclass
class CoverageReport:
    """Main coverage report data structure"""

    generated_at: str
    total_pipelines: int
    total_releases: int
    total_tested_releases: int
    overall_coverage_percentage: float
    pipeline_coverage: List[PipelineCoverage]
    orphaned_results: List[str]
    summary_insights: Dict[str, Any]


def fetch_all_pipeline_releases(
    github_token: Optional[str] = None,
) -> Dict[str, List[PipelineRelease]]:
    """Fetch all releases for all nf-core pipelines from GitHub API"""
    try:
        logger.info(
            "Fetching comprehensive nf-core pipeline release data from GitHub API"
        )

        # Set up headers with optional authentication
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            logger.info("Using GitHub token for authentication")

        # Get all nf-core repositories
        repos_url = "https://api.github.com/orgs/nf-core/repos"
        all_repos = []
        page = 1

        while True:
            logger.info(f"Fetching nf-core repositories page {page}")
            response = requests.get(
                f"{repos_url}?type=public&per_page=100&page={page}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            repos = response.json()

            if not repos:
                break

            # Filter out archived repos and non-pipeline repos
            active_repos = [repo for repo in repos if not repo.get("archived", True)]
            all_repos.extend(active_repos)
            page += 1

        logger.info(f"Found {len(all_repos)} active nf-core repositories")

        # Build comprehensive release data
        all_pipeline_releases = {}

        for repo in all_repos:
            repo_name = repo["name"]

            # Skip non-pipeline repositories (tools, modules, etc.)
            ignored_repos = [
                "tools",
                "modules",
                "subworkflows",
                "website",
                "test-datasets",
            ]
            if repo_name in ignored_repos:
                logger.debug(f"Skipping non-pipeline repository: {repo_name}")
                continue

            try:
                logger.info(f"Fetching releases for {repo_name}")

                # Get all releases for this repository
                releases_url = (
                    f"https://api.github.com/repos/nf-core/{repo_name}/releases"
                )
                releases_response = requests.get(
                    releases_url, headers=headers, timeout=30
                )
                releases_response.raise_for_status()
                releases = releases_response.json()

                pipeline_releases = []

                # Process each release
                for release in releases:
                    tag_name = release.get("tag_name", "").strip()

                    # Skip dev releases and draft releases, but include prereleases
                    if (
                        tag_name == "dev"
                        or release.get("draft", False)
                        or tag_name == ""
                    ):
                        continue

                    # Get the commit SHA for this tag
                    sha = None
                    try:
                        tag_url = f"https://api.github.com/repos/nf-core/{repo_name}/git/ref/tags/{tag_name}"
                        tag_response = requests.get(
                            tag_url, headers=headers, timeout=30
                        )

                        if tag_response.status_code == 200:
                            tag_data = tag_response.json()
                            sha = tag_data.get("object", {}).get("sha")
                    except Exception as e:
                        logger.warning(
                            f"Could not get SHA for {repo_name} tag {tag_name}: {e}"
                        )
                        continue

                    if sha:
                        pipeline_release = PipelineRelease(
                            pipeline=repo_name,
                            version=tag_name,
                            tag_name=tag_name,
                            sha=sha,
                            published_at=release.get("published_at", ""),
                            is_prerelease=release.get("prerelease", False),
                        )
                        pipeline_releases.append(pipeline_release)

                if pipeline_releases:
                    # Sort by publication date (newest first)
                    pipeline_releases.sort(key=lambda x: x.published_at, reverse=True)
                    all_pipeline_releases[repo_name] = pipeline_releases
                    logger.info(
                        f"Found {len(pipeline_releases)} releases for {repo_name}"
                    )
                else:
                    logger.warning(f"No valid releases found for {repo_name}")

            except Exception as e:
                logger.error(f"Failed to fetch releases for {repo_name}: {e}")
                continue

        total_releases = sum(
            len(releases) for releases in all_pipeline_releases.values()
        )
        logger.info(
            f"Found {len(all_pipeline_releases)} pipelines with {total_releases} total releases"
        )

        return all_pipeline_releases

    except Exception as e:
        logger.error(f"Failed to fetch pipeline release data from GitHub: {e}")
        sys.exit(1)


def scan_s3_test_results(s3_bucket: str) -> Set[str]:
    """Scan S3 bucket to identify which releases have test results"""
    try:
        s3_client = boto3.client("s3")
        logger.info(f"Scanning S3 bucket {s3_bucket} for test results")

        paginator = s3_client.get_paginator("list_objects_v2")
        results_paths = set()

        # Look for all results- prefixes across all pipelines
        page_iterator = paginator.paginate(Bucket=s3_bucket, Delimiter="/")

        for page in page_iterator:
            # Get pipeline-level prefixes
            for prefix_info in page.get("CommonPrefixes", []):
                pipeline_prefix = prefix_info["Prefix"]

                # Look for results- directories within each pipeline
                pipeline_paginator = s3_client.get_paginator("list_objects_v2")
                pipeline_iterator = pipeline_paginator.paginate(
                    Bucket=s3_bucket, Prefix=pipeline_prefix, Delimiter="/"
                )

                for pipeline_page in pipeline_iterator:
                    for sub_prefix in pipeline_page.get("CommonPrefixes", []):
                        sub_dir = sub_prefix["Prefix"]
                        if "/results-" in sub_dir:
                            # Extract the results directory path (remove trailing slash)
                            results_path = sub_dir.rstrip("/")
                            results_paths.add(results_path)

        logger.info(f"Found {len(results_paths)} test result directories in S3")
        return results_paths

    except Exception as e:
        logger.error(f"Failed to scan S3 for test results: {e}")
        sys.exit(1)


def analyze_coverage(
    all_releases: Dict[str, List[PipelineRelease]], s3_results: Set[str]
) -> CoverageReport:
    """Analyze test coverage by cross-referencing releases with S3 results"""
    logger.info("Analyzing test coverage...")

    # Create lookup for S3 results by SHA
    s3_results_by_sha: Dict[str, Set[str]] = {}
    orphaned_results = []

    for result_path in s3_results:
        if "/results-" in result_path:
            parts = result_path.split("/results-")
            if len(parts) == 2:
                pipeline = parts[0]
                sha = parts[1]

                if pipeline not in s3_results_by_sha:
                    s3_results_by_sha[pipeline] = set()
                s3_results_by_sha[pipeline].add(sha)
            else:
                orphaned_results.append(result_path)

    # Analyze coverage for each pipeline
    pipeline_coverage_list = []
    total_releases = 0
    total_tested_releases = 0

    for pipeline_name, releases in all_releases.items():
        pipeline_shas = s3_results_by_sha.get(pipeline_name, set())

        tested_count = 0
        missing_releases = []

        for release in releases:
            total_releases += 1
            if release.sha in pipeline_shas:
                release.has_test_results = True
                tested_count += 1
                total_tested_releases += 1
            else:
                missing_releases.append(release.version)

        coverage_percentage = (tested_count / len(releases) * 100) if releases else 0

        # Get latest release info
        latest_release = releases[0] if releases else None
        latest_release_tested = (
            latest_release.has_test_results if latest_release else False
        )

        pipeline_coverage = PipelineCoverage(
            pipeline=pipeline_name,
            total_releases=len(releases),
            tested_releases=tested_count,
            coverage_percentage=coverage_percentage,
            missing_releases=missing_releases,
            latest_release=latest_release.version if latest_release else None,
            latest_release_tested=latest_release_tested,
        )

        pipeline_coverage_list.append(pipeline_coverage)

    # Sort by coverage percentage (lowest first for actionability)
    pipeline_coverage_list.sort(key=lambda x: x.coverage_percentage)

    # Calculate overall statistics
    overall_coverage = (
        (total_tested_releases / total_releases * 100) if total_releases > 0 else 0
    )

    # Generate insights
    pipelines_needing_attention = [
        p for p in pipeline_coverage_list if p.coverage_percentage < 50
    ]
    latest_releases_untested = [
        p for p in pipeline_coverage_list if not p.latest_release_tested
    ]

    summary_insights = {
        "pipelines_below_50_percent_coverage": len(pipelines_needing_attention),
        "pipelines_with_untested_latest_release": len(latest_releases_untested),
        "lowest_coverage_pipelines": [
            {"pipeline": p.pipeline, "coverage": p.coverage_percentage}
            for p in pipeline_coverage_list[:5]
        ],
        "pipelines_needing_latest_release_tests": [
            {"pipeline": p.pipeline, "latest_release": p.latest_release}
            for p in latest_releases_untested[:10]
        ],
    }

    # Find orphaned results (results in S3 without matching releases)
    for pipeline_name, shas in s3_results_by_sha.items():
        if pipeline_name in all_releases:
            known_shas = {release.sha for release in all_releases[pipeline_name]}
            orphaned_shas = shas - known_shas
            for sha in orphaned_shas:
                orphaned_results.append(f"{pipeline_name}/results-{sha}")

    report = CoverageReport(
        generated_at=datetime.utcnow().isoformat(),
        total_pipelines=len(all_releases),
        total_releases=total_releases,
        total_tested_releases=total_tested_releases,
        overall_coverage_percentage=overall_coverage,
        pipeline_coverage=pipeline_coverage_list,
        orphaned_results=orphaned_results,
        summary_insights=summary_insights,
    )

    logger.info(f"Coverage analysis complete: {overall_coverage:.1f}% overall coverage")
    return report


def generate_markdown_report(report: CoverageReport) -> str:
    """Generate a markdown-formatted coverage report"""
    md_lines = []

    # Header
    md_lines.append("# 🧪 nf-core Test Coverage Report")
    md_lines.append("")
    md_lines.append(f"**Generated:** {report.generated_at}")
    md_lines.append("")

    # Summary Statistics
    md_lines.append("## 📊 Summary Statistics")
    md_lines.append("")
    md_lines.append(f"- **Total Pipelines:** {report.total_pipelines}")
    md_lines.append(f"- **Total Releases:** {report.total_releases}")
    md_lines.append(f"- **Tested Releases:** {report.total_tested_releases}")
    md_lines.append(
        f"- **Overall Coverage:** {report.overall_coverage_percentage:.1f}%"
    )
    md_lines.append("")

    # Key Insights
    insights = report.summary_insights
    md_lines.append("## 🔍 Key Insights")
    md_lines.append("")
    md_lines.append(
        f"- **Pipelines below 50% coverage:** {insights['pipelines_below_50_percent_coverage']}"
    )
    md_lines.append(
        f"- **Pipelines with untested latest release:** {insights['pipelines_with_untested_latest_release']}"
    )
    md_lines.append("")

    if insights["lowest_coverage_pipelines"]:
        md_lines.append("### 🚨 Lowest Coverage Pipelines")
        md_lines.append("")
        for item in insights["lowest_coverage_pipelines"]:
            md_lines.append(f"- **{item['pipeline']}:** {item['coverage']:.1f}%")
        md_lines.append("")

    if insights["pipelines_needing_latest_release_tests"]:
        md_lines.append("### 🆕 Latest Releases Needing Tests")
        md_lines.append("")
        for item in insights["pipelines_needing_latest_release_tests"][:5]:
            md_lines.append(f"- **{item['pipeline']}:** {item['latest_release']}")
        md_lines.append("")

    # Per-Pipeline Coverage (show worst performers first)
    md_lines.append("## 📋 Per-Pipeline Coverage")
    md_lines.append("")
    md_lines.append(
        "| Pipeline | Total | Tested | Coverage | Latest Release | Latest Tested | Missing Releases |"
    )
    md_lines.append(
        "|----------|-------|--------|----------|----------------|---------------|------------------|"
    )

    for coverage in report.pipeline_coverage[:20]:  # Show top 20 worst performers
        latest_status = "✅" if coverage.latest_release_tested else "❌"
        missing_count = len(coverage.missing_releases)
        missing_preview = ", ".join(coverage.missing_releases[:3])
        if missing_count > 3:
            missing_preview += f" (+{missing_count - 3} more)"

        md_lines.append(
            f"| {coverage.pipeline} | {coverage.total_releases} | "
            f"{coverage.tested_releases} | {coverage.coverage_percentage:.1f}% | "
            f"{coverage.latest_release} | {latest_status} | {missing_preview} |"
        )

    if len(report.pipeline_coverage) > 20:
        md_lines.append(
            f"| ... | ... | ... | ... | ... | ... | *({len(report.pipeline_coverage) - 20} more pipelines)* |"
        )

    md_lines.append("")

    # Orphaned Results
    if report.orphaned_results:
        md_lines.append("## 🗑️ Orphaned Test Results")
        md_lines.append("")
        md_lines.append("Test results found in S3 that don't match any known release:")
        md_lines.append("")
        for orphan in report.orphaned_results[:10]:
            md_lines.append(f"- `{orphan}`")
        if len(report.orphaned_results) > 10:
            md_lines.append(f"- ... and {len(report.orphaned_results) - 10} more")
        md_lines.append("")

    return "\n".join(md_lines)


def generate_csv_report(report: CoverageReport) -> str:
    """Generate a CSV-formatted coverage report"""
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "pipeline",
            "total_releases",
            "tested_releases",
            "coverage_percentage",
            "latest_release",
            "latest_release_tested",
            "missing_releases",
        ]
    )

    # Data rows
    for coverage in report.pipeline_coverage:
        writer.writerow(
            [
                coverage.pipeline,
                coverage.total_releases,
                coverage.tested_releases,
                f"{coverage.coverage_percentage:.1f}",
                coverage.latest_release,
                coverage.latest_release_tested,
                "; ".join(coverage.missing_releases),
            ]
        )

    return output.getvalue()


def generate_json_report(report: CoverageReport) -> str:
    """Generate a JSON-formatted coverage report"""

    # Convert dataclasses to dictionaries for JSON serialization
    def dataclass_to_dict(obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return obj

    report_dict = {
        "generated_at": report.generated_at,
        "total_pipelines": report.total_pipelines,
        "total_releases": report.total_releases,
        "total_tested_releases": report.total_tested_releases,
        "overall_coverage_percentage": report.overall_coverage_percentage,
        "pipeline_coverage": [dataclass_to_dict(pc) for pc in report.pipeline_coverage],
        "orphaned_results": report.orphaned_results,
        "summary_insights": report.summary_insights,
    }

    return json.dumps(report_dict, indent=2)


def write_github_actions_outputs(report: CoverageReport):
    """Write report data to GitHub Actions outputs"""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"total_pipelines={report.total_pipelines}\n")
            f.write(f"total_releases={report.total_releases}\n")
            f.write(f"total_tested_releases={report.total_tested_releases}\n")
            f.write(
                f"overall_coverage_percentage={report.overall_coverage_percentage:.1f}\n"
            )
            f.write(
                f"pipelines_below_50_percent={report.summary_insights['pipelines_below_50_percent_coverage']}\n"
            )
            f.write(
                f"latest_releases_untested={report.summary_insights['pipelines_with_untested_latest_release']}\n"
            )

            # Format worst performers for GitHub output
            worst_performers = []
            for coverage in report.pipeline_coverage[:5]:
                worst_performers.append(
                    f"- **{coverage.pipeline}**: {coverage.coverage_percentage:.1f}%"
                )
            f.write(f"worst_performers={'\\n'.join(worst_performers)}\n")

            # Format latest releases needing tests
            latest_untested = []
            for item in report.summary_insights[
                "pipelines_needing_latest_release_tests"
            ][:5]:
                latest_untested.append(
                    f"- **{item['pipeline']}**: {item['latest_release']}"
                )
            f.write(f"latest_untested={'\\n'.join(latest_untested)}\n")

        logger.info("GitHub Actions outputs written to $GITHUB_OUTPUT")


def main():
    parser = argparse.ArgumentParser(
        description="Generate nf-core test coverage report"
    )
    parser.add_argument(
        "--bucket", default="nf-core-awsmegatests", help="S3 bucket name"
    )
    parser.add_argument(
        "--github-token",
        help="GitHub personal access token for higher rate limits (optional)",
    )
    parser.add_argument(
        "--output-dir", default="./reports", help="Output directory for report files"
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["markdown", "csv", "json"],
        choices=["markdown", "csv", "json"],
        help="Output formats to generate",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode with mock S3 data (for testing without AWS credentials)",
    )

    args = parser.parse_args()

    logger.info("Starting nf-core test coverage report generation")
    logger.info(f"S3 bucket: {args.bucket}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Output formats: {', '.join(args.formats)}")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: Fetch all pipeline releases
    all_releases = fetch_all_pipeline_releases(args.github_token)

    # Step 2: Scan S3 for test results (or use mock data in test mode)
    if args.test_mode:
        logger.info("Running in test mode - using mock S3 data")
        # Create some mock S3 results for testing
        s3_results = set()
        for pipeline_name, releases in list(all_releases.items())[
            :3
        ]:  # Take first 3 pipelines
            for release in releases[:2]:  # Take first 2 releases per pipeline
                s3_results.add(f"{pipeline_name}/results-{release.sha}")
        logger.info(f"Mock S3 results: {len(s3_results)} test result directories")
    else:
        s3_results = scan_s3_test_results(args.bucket)

    # Step 3: Analyze coverage
    report = analyze_coverage(all_releases, s3_results)

    # Step 4: Generate reports in requested formats
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if "markdown" in args.formats:
        markdown_report = generate_markdown_report(report)
        markdown_path = os.path.join(
            args.output_dir, f"test_coverage_report_{timestamp}.md"
        )
        with open(markdown_path, "w") as f:
            f.write(markdown_report)
        logger.info(f"Markdown report written to: {markdown_path}")

    if "csv" in args.formats:
        csv_report = generate_csv_report(report)
        csv_path = os.path.join(
            args.output_dir, f"test_coverage_report_{timestamp}.csv"
        )
        with open(csv_path, "w") as f:
            f.write(csv_report)
        logger.info(f"CSV report written to: {csv_path}")

    if "json" in args.formats:
        json_report = generate_json_report(report)
        json_path = os.path.join(
            args.output_dir, f"test_coverage_report_{timestamp}.json"
        )
        with open(json_path, "w") as f:
            f.write(json_report)
        logger.info(f"JSON report written to: {json_path}")

    # Step 5: Write GitHub Actions outputs
    write_github_actions_outputs(report)

    # Final summary
    logger.info("=" * 80)
    logger.info("TEST COVERAGE REPORT SUMMARY")
    logger.info("=" * 80)
    logger.info(
        f"📊 Overall Coverage: {report.overall_coverage_percentage:.1f}% ({report.total_tested_releases}/{report.total_releases} releases)"
    )
    logger.info(f"🔍 Pipelines analyzed: {report.total_pipelines}")
    logger.info(
        f"🚨 Pipelines below 50% coverage: {report.summary_insights['pipelines_below_50_percent_coverage']}"
    )
    logger.info(
        f"🆕 Latest releases needing tests: {report.summary_insights['pipelines_with_untested_latest_release']}"
    )
    logger.info(f"🗑️ Orphaned test results: {len(report.orphaned_results)}")
    logger.info("=" * 80)

    logger.info("Test coverage report generation completed successfully")


if __name__ == "__main__":
    main()
