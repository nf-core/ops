# nf-core Operations Infrastructure

This repository manages infrastructure and automation for nf-core operations, including AWS resources, GitHub management, and test coverage analysis.

## 🧪 Test Coverage Reporting

The repository includes a comprehensive test coverage reporting system that analyzes which nf-core pipeline releases have been tested against the AWS megatests infrastructure.

### Features

- **Complete Coverage Analysis**: Scans all nf-core pipelines and their releases
- **S3 Integration**: Cross-references releases with test results in the S3 bucket
- **Gap Identification**: Identifies which releases are missing test results
- **Multiple Output Formats**: Generates markdown, CSV, and JSON reports
- **GitHub Actions Integration**: Automated weekly reporting with summaries
- **Actionable Insights**: Prioritizes pipelines and releases needing attention

### Usage

#### Manual Report Generation

```bash
# Generate all report formats
uv run .github/generate_test_coverage_report.py

# Generate specific formats only
uv run .github/generate_test_coverage_report.py --formats markdown csv

# Custom S3 bucket and output directory
uv run .github/generate_test_coverage_report.py \
  --bucket my-test-bucket \
  --output-dir custom-reports \
  --github-token $GITHUB_TOKEN
```

#### Automated Reporting

The test coverage report runs automatically:

- **Weekly**: Every Monday at 06:00 UTC
- **On Pull Requests**: When report files are modified
- **Manual Trigger**: Via GitHub Actions workflow dispatch

### Report Contents

The generated reports include:

1. **Summary Statistics**: Overall coverage percentages and counts
2. **Pipeline Analysis**: Per-pipeline breakdown of tested vs missing releases
3. **Priority Insights**: Pipelines with lowest coverage needing attention
4. **Latest Release Status**: Which latest releases haven't been tested yet
5. **Orphaned Results**: Test results in S3 without matching releases

### Report Formats

- **Markdown (`.md`)**: Human-readable summary with insights and recommendations
- **CSV (`.csv`)**: Machine-readable data for spreadsheet analysis
- **JSON (`.json`)**: Structured data for programmatic processing

## 🏷️ S3 Results Tagging

The repository also includes an S3 results tagging system that:

- Identifies current pipeline releases in S3
- Tags orphaned directories for cleanup
- Provides statistics and reporting

## 📁 Project Structure

```
├── .github/
│   ├── generate_test_coverage_report.py  # Test coverage analysis script
│   ├── s3_results_tagger.py              # S3 cleanup and tagging script
│   └── workflows/
│       ├── test-coverage-report.yml      # Coverage reporting workflow
│       └── s3-results-tagging.yml        # S3 tagging workflow
└── pulumi/                               # Infrastructure as Code projects
    ├── AWSMegatests/                     # AWS megatests infrastructure
    ├── github/                           # GitHub management
    └── ...
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- AWS credentials (for S3 access)
- GitHub token (for API access)

### Installation

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Dependencies are automatically managed by uv scripts
```

### Running Reports

1. Configure AWS credentials for S3 access
2. Optionally set GITHUB_TOKEN for higher API rate limits
3. Run the desired script with uv

## 📊 Example Output

The test coverage report provides insights like:

- Overall coverage: 75.3% (450/597 releases tested)
- Pipelines below 50% coverage: 12 pipelines need attention
- Latest releases needing tests: 8 recent releases untested
- Priority: Focus on pipelines with 0-25% coverage first

## 🔗 References

https://www.hashicorp.com/blog/managing-github-with-terraform

https://github.com/ipdxco/awesome-github-as-code-users
