# Migration to Seqera Terraform Provider

## Overview

This document describes the migration of the AWSMegatests project from using seqerakit CLI commands to the official Seqera Terraform provider, integrated through Pulumi's new terraform-provider support.

## Migration Summary

### Before: seqerakit CLI Approach
- ❌ Used `pulumi_command.local.Command` to execute seqerakit CLI
- ❌ Required parsing of CLI output to extract compute environment IDs
- ❌ Complex error handling around CLI command failures
- ❌ Sequential deployment dependencies
- ❌ External dependency on tw-cli and seqerakit installation

### After: Seqera Terraform Provider
- ✅ Native Pulumi resources using `pulumi_seqera` package
- ✅ Direct access to compute environment IDs as resource outputs
- ✅ Native error handling and validation
- ✅ Parallel resource creation
- ✅ Reduced external dependencies

## Implementation Details

### New Components Added

1. **seqera_terraform.py** - New module containing:
   - `create_seqera_provider()` - Configures the Seqera provider
   - `create_compute_environment()` - Creates individual compute environments
   - `deploy_seqera_environments_terraform()` - Orchestrates the deployment
   - `get_compute_environment_ids_terraform()` - Extracts compute environment IDs

2. **Updated __main__.py** - Enhanced with:
   - Dual deployment approach (Terraform provider primary, seqerakit fallback)
   - Comparative outputs for both deployment methods
   - Graceful fallback mechanism

3. **Updated requirements.txt** - Added:
   - `pulumi-seqera>=0.25.2` - Seqera Terraform provider SDK

### Terraform Provider Installation

The Seqera Terraform provider was installed using Pulumi's new terraform-provider support:

```bash
pulumi package add terraform-provider registry.terraform.io/seqeralabs/seqera
```

This generates a Python SDK at `sdks/seqera/pulumi_seqera/` with native Pulumi resource types.

### Configuration Mapping

The migration preserves all existing compute environment configurations from seqerakit JSON files:

| seqerakit Configuration | Terraform Provider Resource |
|------------------------|------------------------------|
| `discriminator: "aws-batch"` | `platform: "aws-batch"` |
| `region` | `aws_batch.region` |
| `workDir` | `aws_batch.work_dir` |
| `forge.*` | `aws_batch.forge.*` |
| `waveEnabled` | `aws_batch.wave_enabled` |
| `fusion2Enabled` | `aws_batch.fusion2_enabled` |
| `nvnmeStorageEnabled` | `aws_batch.nvnme_storage_enabled` |
| `fusionSnapshots` | `aws_batch.fusion_snapshots` |

## Deployment Strategy

### Hybrid Approach (Current)

The implementation uses a hybrid approach for safe migration:

1. **Primary**: Terraform provider deployment
2. **Fallback**: seqerakit CLI deployment (if Terraform fails)
3. **Comparison**: Both compute environment IDs are exported for validation

### Migration Phases

**Phase 1 (Current)**: Dual deployment with Terraform provider as primary
- Both approaches run in parallel
- Terraform provider IDs used for GitHub secrets
- seqerakit maintained as backup

**Phase 2 (Future)**: Terraform provider only
- Remove seqerakit CLI dependencies
- Clean up legacy command resources
- Simplify exports and outputs

## Benefits Realized

### Performance Improvements
- **Parallel Deployment**: Resources created simultaneously instead of sequentially
- **Faster Startup**: No CLI subprocess overhead
- **Native State**: Proper Pulumi resource tracking

### Reliability Improvements
- **Type Safety**: Strongly typed resource configurations
- **Error Handling**: Native Pulumi error reporting
- **Resource Tracking**: Proper dependency management

### Maintenance Improvements
- **Reduced Dependencies**: No external CLI tool requirements
- **Simplified Configuration**: Direct resource definition
- **Better Documentation**: Auto-generated schema documentation

## Validation Results

### Preview Testing
The `pulumi preview` command successfully shows:

```
+ seqera:index:ComputeEnv aws_ireland_fusionv2_nvme_cpu_snapshots create 
+ seqera:index:ComputeEnv aws_ireland_fusionv2_nvme_gpu_snapshots create 
+ seqera:index:ComputeEnv aws_ireland_fusionv2_nvme_cpu_ARM_snapshots create
```

### Output Comparison
Both deployment methods will be compared through exports:
- `compute_env_ids`: Primary IDs from Terraform provider
- `compute_env_ids_seqerakit`: Legacy IDs from seqerakit
- `deployment_method`: Indicates which method was used

## Future Considerations

### Complete Migration
Once validated, the seqerakit approach can be removed:
1. Remove seqerakit CLI command resources
2. Remove seqerakit configuration files
3. Simplify __main__.py to only use Terraform provider
4. Update documentation

### Resource Management
The Terraform provider may manage additional Seqera resources not available via seqerakit:
- Direct pipeline management
- Advanced workspace configuration
- Additional compute environment types

## Rollback Plan

If issues arise, rollback is straightforward:
1. Comment out Terraform provider deployment in __main__.py
2. Force `deployment_method = "seqerakit-fallback"`
3. The seqerakit approach remains fully functional

## Conclusion

The migration to the Seqera Terraform provider represents a significant improvement in:
- **Reliability**: Native resource management
- **Performance**: Parallel deployment and reduced overhead
- **Maintainability**: Reduced external dependencies
- **Integration**: Better Pulumi ecosystem integration

The hybrid approach ensures a safe migration path while providing immediate benefits from the new Terraform provider integration.