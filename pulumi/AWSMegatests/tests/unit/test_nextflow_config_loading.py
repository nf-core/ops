"""Test Nextflow configuration loading and merging functionality.

This test validates that the load_nextflow_config function properly merges
base configuration with environment-specific configurations.
"""

import os
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.compute_environments import (  # noqa: E402
    load_nextflow_config,
    ConfigurationError,
)


class TestNextflowConfigLoading:
    """Test Nextflow configuration loading and merging."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory with test config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create base config
            base_config_content = dedent("""
                // Base Nextflow configuration for AWS Batch compute environments
                // This configuration is shared across all compute environment types

                aws.batch.maxSpotAttempts = 5

                process {
                    maxRetries = 2
                    errorStrategy = { task.exitStatus in ((130..145) + 104 + 175) ? 'retry' : 'terminate' }
                }

                fusion {
                    tags = '[.command.*|.exitcode|.fusion.*](nextflow.io/metadata=true),[*](nextflow.io/temporary=true)'
                }
            """).strip()

            base_config_path = os.path.join(temp_dir, "nextflow-base.config")
            with open(base_config_path, "w") as f:
                f.write(base_config_content)

            # Create CPU config
            cpu_config_content = dedent("""
                // Nextflow configuration for CPU compute environments
                // Includes base configuration and CPU-specific settings

                includeConfig 'nextflow-base.config'

                process {
                    publishDir = [
                        path: { params.outdir },
                        mode: 'copy',
                        tags: [
                            'compute_env': 'aws_ireland_fusionv2_nvme_cpu_snapshots',
                            'architecture': 'x86_64',
                            'fusion': 'enabled'
                        ]
                    ]
                }
            """).strip()

            cpu_config_path = os.path.join(temp_dir, "nextflow-cpu.config")
            with open(cpu_config_path, "w") as f:
                f.write(cpu_config_content)

            # Create GPU config
            gpu_config_content = dedent("""
                // Nextflow configuration for GPU compute environments
                // Includes base configuration and GPU-specific settings

                includeConfig 'nextflow-base.config'

                process {
                    publishDir = [
                        path: { params.outdir },
                        mode: 'copy',
                        tags: [
                            'compute_env': 'aws_ireland_fusionv2_nvme_gpu_snapshots',
                            'architecture': 'x86_64',
                            'gpu': 'enabled',
                            'fusion': 'enabled'
                        ]
                    ]
                }
            """).strip()

            gpu_config_path = os.path.join(temp_dir, "nextflow-gpu.config")
            with open(gpu_config_path, "w") as f:
                f.write(gpu_config_content)

            yield {
                "temp_dir": temp_dir,
                "base_config_path": base_config_path,
                "cpu_config_path": cpu_config_path,
                "gpu_config_path": gpu_config_path,
                "base_content": base_config_content,
                "cpu_content": cpu_config_content,
                "gpu_content": gpu_config_content,
            }

    def test_load_nextflow_config_merges_base_and_env_configs(
        self, temp_config_dir, monkeypatch
    ):
        """Test that base config is properly merged with environment config."""
        # Mock the NEXTFLOW_CONFIG_FILES constant
        mock_config_files = {
            "cpu": temp_config_dir["cpu_config_path"],
            "gpu": temp_config_dir["gpu_config_path"],
        }

        # Patch the constants in the compute_environments module
        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
            mock_config_files,
        )

        # Load CPU config
        cpu_config = load_nextflow_config("cpu")

        # Verify base config content is included
        assert "aws.batch.maxSpotAttempts = 5" in cpu_config
        assert "maxRetries = 2" in cpu_config
        assert (
            "errorStrategy = { task.exitStatus in ((130..145) + 104 + 175) ? 'retry' : 'terminate' }"
            in cpu_config
        )
        assert "fusion {" in cpu_config
        assert (
            "tags = '[.command.*|.exitcode|.fusion.*](nextflow.io/metadata=true)"
            in cpu_config
        )

        # Verify environment-specific config content is included
        assert "'compute_env': 'aws_ireland_fusionv2_nvme_cpu_snapshots'" in cpu_config
        assert "'architecture': 'x86_64'" in cpu_config
        assert "'fusion': 'enabled'" in cpu_config

        # Verify includeConfig line is removed
        assert "includeConfig" not in cpu_config

        # Verify base config comes before environment config
        base_index = cpu_config.find("aws.batch.maxSpotAttempts")
        env_index = cpu_config.find("compute_env")
        assert base_index < env_index

    def test_load_nextflow_config_removes_include_statements(
        self, temp_config_dir, monkeypatch
    ):
        """Test that includeConfig statements are properly removed."""
        mock_config_files = {"gpu": temp_config_dir["gpu_config_path"]}

        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
            mock_config_files,
        )

        gpu_config = load_nextflow_config("gpu")

        # Verify includeConfig line is completely removed
        assert "includeConfig" not in gpu_config
        assert "nextflow-base.config" not in gpu_config

        # Verify the rest of the config is intact
        assert "'compute_env': 'aws_ireland_fusionv2_nvme_gpu_snapshots'" in gpu_config
        assert "'gpu': 'enabled'" in gpu_config

    def test_load_nextflow_config_works_without_base_config(self, monkeypatch):
        """Test that function works when base config doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create only environment config (no base config)
            env_config_content = dedent("""
                // Environment-only configuration
                process {
                    publishDir = [
                        path: { params.outdir },
                        tags: ['test': 'value']
                    ]
                }
            """).strip()

            env_config_path = os.path.join(temp_dir, "nextflow-test.config")
            with open(env_config_path, "w") as f:
                f.write(env_config_content)

            mock_config_files = {"test": env_config_path}
            monkeypatch.setattr(
                "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
                mock_config_files,
            )

            config = load_nextflow_config("test")

            # Should return just the environment config
            assert "Environment-only configuration" in config
            assert "'test': 'value'" in config
            assert "aws.batch.maxSpotAttempts" not in config  # No base config

    def test_load_nextflow_config_handles_multiple_include_statements(
        self, monkeypatch
    ):
        """Test that multiple includeConfig statements are all removed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config with multiple include statements
            multi_include_content = dedent("""
                // Configuration with multiple includes
                includeConfig 'base.config'
                includeConfig 'another.config'
                    includeConfig 'third.config'  // Indented include

                process {
                    publishDir = [path: { params.outdir }]
                }
            """).strip()

            config_path = os.path.join(temp_dir, "multi-include.config")
            with open(config_path, "w") as f:
                f.write(multi_include_content)

            mock_config_files = {"multi": config_path}
            monkeypatch.setattr(
                "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
                mock_config_files,
            )

            config = load_nextflow_config("multi")

            # All includeConfig statements should be removed
            assert "includeConfig" not in config
            assert "base.config" not in config
            assert "another.config" not in config
            assert "third.config" not in config

            # Rest of config should be intact
            assert "Configuration with multiple includes" in config
            assert "publishDir = [path: { params.outdir }]" in config

    def test_load_nextflow_config_raises_error_for_missing_env_type(self, monkeypatch):
        """Test that function raises error for undefined environment type."""
        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES", {}
        )

        with pytest.raises(
            ConfigurationError,
            match="No Nextflow config file defined for environment type: nonexistent",
        ):
            load_nextflow_config("nonexistent")

    def test_load_nextflow_config_raises_error_for_missing_file(self, monkeypatch):
        """Test that function raises error when config file doesn't exist."""
        mock_config_files = {"missing": "/nonexistent/path/config.conf"}
        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
            mock_config_files,
        )

        with pytest.raises(FileNotFoundError, match="Nextflow config file not found"):
            load_nextflow_config("missing")

    def test_load_nextflow_config_raises_error_for_unreadable_base_file(
        self, temp_config_dir, monkeypatch
    ):
        """Test that function raises error when base config file can't be read."""
        # Make base config file unreadable
        os.chmod(temp_config_dir["base_config_path"], 0o000)

        mock_config_files = {"cpu": temp_config_dir["cpu_config_path"]}
        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
            mock_config_files,
        )

        try:
            with pytest.raises(
                ConfigurationError, match="Failed to read base Nextflow config file"
            ):
                load_nextflow_config("cpu")
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_config_dir["base_config_path"], 0o644)

    def test_load_nextflow_config_raises_error_for_unreadable_env_file(
        self, temp_config_dir, monkeypatch
    ):
        """Test that function raises error when environment config file can't be read."""
        # Make environment config file unreadable
        os.chmod(temp_config_dir["cpu_config_path"], 0o000)

        mock_config_files = {"cpu": temp_config_dir["cpu_config_path"]}
        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
            mock_config_files,
        )

        try:
            with pytest.raises(
                ConfigurationError, match="Failed to read Nextflow config file"
            ):
                load_nextflow_config("cpu")
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_config_dir["cpu_config_path"], 0o644)

    def test_load_nextflow_config_preserves_config_structure(
        self, temp_config_dir, monkeypatch
    ):
        """Test that the merged config preserves proper Nextflow structure."""
        mock_config_files = {"cpu": temp_config_dir["cpu_config_path"]}
        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
            mock_config_files,
        )

        config = load_nextflow_config("cpu")

        # Should have proper comment structure
        assert "// Base Nextflow configuration" in config
        assert "// Nextflow configuration for CPU compute environments" in config

        # Should have proper block structure
        assert "process {" in config
        assert "fusion {" in config

        # Should preserve indentation and formatting
        lines = config.split("\n")

        # Find process block lines and verify indentation is preserved
        in_process_block = False
        for line in lines:
            if line.strip() == "process {":
                in_process_block = True
            elif in_process_block and line.strip() == "}":
                in_process_block = False
            elif in_process_block and line.strip() and not line.startswith("//"):
                # Lines inside process blocks should be indented
                assert line.startswith("    ") or line.startswith("\t"), (
                    f"Line not properly indented: '{line}'"
                )

    def test_merged_config_content_order(self, temp_config_dir, monkeypatch):
        """Test that merged config has base config first, then environment config."""
        mock_config_files = {"gpu": temp_config_dir["gpu_config_path"]}
        monkeypatch.setattr(
            "src.infrastructure.compute_environments.NEXTFLOW_CONFIG_FILES",
            mock_config_files,
        )

        config = load_nextflow_config("gpu")

        # Find positions of key markers
        base_marker_pos = config.find("aws.batch.maxSpotAttempts")
        env_marker_pos = config.find("'gpu': 'enabled'")

        # Base config should come before environment config
        assert base_marker_pos < env_marker_pos
        assert base_marker_pos != -1, "Base config content not found"
        assert env_marker_pos != -1, "Environment config content not found"

        # Verify proper structure by checking that base config content comes before env content
        lines = config.split("\n")

        # Find the line with aws.batch.maxSpotAttempts (from base config)
        base_config_line = None
        gpu_enabled_line = None

        for i, line in enumerate(lines):
            if "aws.batch.maxSpotAttempts" in line:
                base_config_line = i
            if "'gpu': 'enabled'" in line:
                gpu_enabled_line = i

        # Base config line should come before environment config line
        assert base_config_line is not None, (
            "Base config content not found in merged config"
        )
        assert gpu_enabled_line is not None, (
            "Environment config content not found in merged config"
        )
        assert base_config_line < gpu_enabled_line, (
            "Base config should come before environment config"
        )
