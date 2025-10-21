# Seqera Platform Multi-Workspace Infrastructure

This directory contains Pulumi infrastructure-as-code for managing multiple Seqera Platform workspaces for nf-core.

## Structure

```
seqera_platform/
├── shared/                       # Shared Python modules
│   ├── providers/                # Provider factory functions (AWS, GitHub, Seqera)
│   ├── infrastructure/           # Reusable infrastructure modules (S3, IAM, compute envs)
│   ├── integrations/             # GitHub and Seqera integrations
│   ├── config/                   # Configuration management
│   └── utils/                    # Utility functions
├── awsmegatests/                 # AWS Megatests workspace
│   ├── __main__.py               # Main Pulumi program
│   ├── workspace_config.py       # Workspace-specific configuration
│   ├── Pulumi.yaml               # Pulumi project definition
│   └── pyproject.toml            # Python dependencies
└── resource_optimization/        # Resource Optimization workspace
    ├── __main__.py               # Main Pulumi program
    ├── workspace_config.py       # Workspace-specific configuration
    ├── Pulumi.yaml               # Pulumi project definition
    └── pyproject.toml            # Python dependencies
```

## Workspaces

### AWS Megatests (`awsmegatests/`)

Full testing infrastructure for nf-core pipelines with:
- **Compute Environments**: CPU, GPU, and ARM
- **S3 Bucket**: `nf-core-awsmegatests`
- **GitHub Integration**: Full CI/CD integration
- **Workspace Participants**: nf-core team members

**Usage:**
```bash
cd awsmegatests
uv sync
uv run pulumi preview
uv run pulumi up
```

### Resource Optimization (`resource_optimization/`)

Dedicated workspace for resource optimization testing with:
- **Compute Environments**: CPU only (no ARM or GPU)
- **S3 Bucket**: `nf-core-resource-optimization`
- **Purpose**: Testing and analyzing pipeline resource requirements

**Usage:**
```bash
cd resource_optimization
uv sync
uv run pulumi preview
uv run pulumi up
```

## Shared Modules

The `shared/` directory contains reusable code shared across all workspaces:

- **`providers/`**: Factory functions for creating Pulumi providers
- **`infrastructure/`**: Modules for S3, IAM, compute environments, and credentials
- **`integrations/`**: GitHub and Seqera Platform integrations
- **`config/`**: Configuration management and ESC integration
- **`utils/`**: Logging, constants, and helper functions

## Configuration

Each workspace has a `workspace_config.py` file that defines:
- Workspace name and organization
- Enabled compute environments (CPU, GPU, ARM)
- AWS region and S3 bucket names
- GitHub integration settings
- Workspace participant settings

Example:
```python
def get_workspace_config():
    return {
        "workspace_name": "AWSmegatests",
        "compute_environments": {
            "cpu": {"enabled": True, ...},
            "gpu": {"enabled": True, ...},
            "arm": {"enabled": True, ...},
        },
        ...
    }
```

## Adding a New Workspace

1. Create a new directory under `seqera_platform/`:
   ```bash
   mkdir seqera_platform/new_workspace
   ```

2. Copy template files from an existing workspace:
   ```bash
   cp awsmegatests/{Pulumi.yaml,pyproject.toml,requirements.txt,.gitignore} new_workspace/
   ```

3. Create `workspace_config.py` with your specific configuration

4. Create `__main__.py` that imports from `shared/` and uses your workspace config

5. Update the Pulumi project name in `Pulumi.yaml`

6. Initialize and deploy:
   ```bash
   cd new_workspace
   uv sync
   pulumi stack init prod
   pulumi up
   ```

## Dependencies

- Python >= 3.12
- uv (Python package manager)
- Pulumi >= 3.173.0
- Pulumi AWS Provider >= 6.81.0
- Pulumi GitHub Provider >= 6.4.0
- Pulumi Command Provider >= 1.0.1

## Environment Variables

Required for deployment:
- `TOWER_ACCESS_TOKEN`: Seqera Platform API token
- `GITHUB_TOKEN`: GitHub personal access token
- `AWS_*`: AWS credentials (usually via ESC)

## Migration from Legacy Structure

The legacy `pulumi/AWSMegatests/` directory is still operational. Once this new structure is validated:

1. Test the new `awsmegatests/` workspace in a separate Pulumi stack
2. Compare outputs and resources
3. Migrate production traffic
4. Deprecate the legacy directory

## Notes

- Each workspace is a separate Pulumi project with independent state
- Workspaces share code via the `shared/` module
- Each workspace can have different compute environment configurations
- S3 buckets and IAM resources are workspace-specific (no sharing)

## Troubleshooting

**Import errors from shared module:**
```python
# Each __main__.py adds the shared path to sys.path:
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))
```

**Different configurations per workspace:**
Modify `workspace_config.py` in each workspace to enable/disable features.
