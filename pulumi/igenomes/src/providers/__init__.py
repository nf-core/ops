"""Cloud provider configurations for iGenomes infrastructure."""

from .aws import create_aws_provider

__all__ = ["create_aws_provider"]
