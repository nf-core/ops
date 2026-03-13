"""Configuration management for AWS Megatests infrastructure."""

from .settings import get_configuration, ConfigurationError

__all__ = ["get_configuration", "ConfigurationError"]
