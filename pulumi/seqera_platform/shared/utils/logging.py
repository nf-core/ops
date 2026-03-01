"""Logging utilities for AWS Megatests infrastructure."""

import pulumi
from typing import Optional


def log_info(message: str, context: Optional[str] = None) -> None:
    """Log an informational message with optional context.

    Args:
        message: The message to log
        context: Optional context prefix
    """
    formatted_message = f"[{context}] {message}" if context else message
    pulumi.log.info(formatted_message)


def log_error(message: str, context: Optional[str] = None) -> None:
    """Log an error message with optional context.

    Args:
        message: The error message to log
        context: Optional context prefix
    """
    formatted_message = f"[{context}] {message}" if context else message
    pulumi.log.error(formatted_message)


def log_warning(message: str, context: Optional[str] = None) -> None:
    """Log a warning message with optional context.

    Args:
        message: The warning message to log
        context: Optional context prefix
    """
    formatted_message = f"[{context}] {message}" if context else message
    pulumi.log.warn(formatted_message)


def log_step(step_number: int, step_name: str, description: str) -> None:
    """Log a deployment step with consistent formatting.

    Args:
        step_number: The step number
        step_name: Short name for the step
        description: Detailed description of what the step does
    """
    log_info(f"Step {step_number}: {step_name} - {description}")


def log_resource_creation(resource_type: str, resource_name: str) -> None:
    """Log resource creation with consistent formatting.

    Args:
        resource_type: Type of resource being created
        resource_name: Name of the resource
    """
    log_info(f"Creating {resource_type}: {resource_name}", "Resource")


def log_resource_success(resource_type: str, resource_name: str) -> None:
    """Log successful resource creation.

    Args:
        resource_type: Type of resource that was created
        resource_name: Name of the resource
    """
    log_info(f"Successfully created {resource_type}: {resource_name}", "Resource")
