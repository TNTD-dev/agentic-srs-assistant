"""IEEE 830 Software Requirements Specification (SRS) Pydantic Model.

This module defines the core data model for SRS documents following the IEEE 830 standard.
The model ensures all required sections are present and non-empty.
"""

from typing import Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class IEEE_SRS_Model(BaseModel):
    """Software Requirements Specification model following IEEE 830 standard.

    This model enforces the 6 required sections of an IEEE 830 SRS document:
    1. Introduction
    2. Overall Description
    3. System Features (Functional Requirements)
    4. External Interface Requirements
    5. Non-functional Requirements
    6. Appendices

    All 6 sections are required and must contain non-empty content (after whitespace
    stripping). Metadata fields are optional and can be used for versioning and
    project tracking.

    Attributes:
        introduction: Purpose, scope, definitions, acronyms, abbreviations, and
            references section.
        overall_description: Product perspective, product functions, user
            characteristics, constraints, assumptions, and dependencies.
        system_features: Detailed functional requirements and system features.
        external_interface: User interfaces, hardware interfaces, software
            interfaces, and communication interfaces.
        non_functional: Performance, security, reliability, scalability, usability,
            portability, and maintainability requirements.
        appendices: Glossary, data models, use case descriptions, change log, and
            other supporting information.
        version: Optional version number (e.g., "v1.0", "v1.2.3").
        project_name: Optional name of the project this SRS belongs to.
        last_updated: Optional ISO timestamp string of last update.

    Example:
        >>> srs = IEEE_SRS_Model(
        ...     introduction="This document specifies...",
        ...     overall_description="The system is designed to...",
        ...     system_features="Feature 1: User authentication...",
        ...     external_interface="UI: Web-based interface...",
        ...     non_functional="Performance: Response time < 200ms...",
        ...     appendices="Appendix A: Glossary..."
        ... )
        >>> srs.model_dump_json()
    """

    # Required sections (6 parts of IEEE 830)
    introduction: str = Field(
        ...,
        description="Purpose, scope, definitions, acronyms, abbreviations, and references",
    )
    overall_description: str = Field(
        ...,
        description="Product perspective, functions, user characteristics, constraints",
    )
    system_features: str = Field(
        ...,
        description="Detailed functional requirements and system features",
    )
    external_interface: str = Field(
        ...,
        description="User interfaces, hardware, software, and communication interfaces",
    )
    non_functional: str = Field(
        ...,
        description="Performance, security, reliability, scalability, and other non-functional requirements",
    )
    appendices: str = Field(
        ...,
        description="Glossary, data models, use cases, change log, and supporting information",
    )

    # Optional metadata fields
    version: Optional[str] = Field(
        None,
        description="Version number (e.g., 'v1.0', 'v1.2.3')",
    )
    project_name: Optional[str] = Field(
        None,
        description="Name of the project this SRS belongs to",
    )
    last_updated: Optional[str] = Field(
        None,
        description="ISO timestamp string of last update (e.g., '2024-01-25T10:30:00Z')",
    )

    @field_validator(
        "introduction",
        "overall_description",
        "system_features",
        "external_interface",
        "non_functional",
        "appendices",
        mode="before",
    )
    @classmethod
    def validate_required_sections(cls, v: str, info: ValidationInfo) -> str:
        """Validate that required sections are non-empty after stripping whitespace.

        Args:
            v: The field value to validate.
            info: Validation info containing field name.

        Returns:
            The validated string value (stripped).

        Raises:
            ValueError: If the field is empty or contains only whitespace.
        """
        if not isinstance(v, str):
            raise ValueError(f"Field must be a string, got {type(v).__name__}")
        if not v.strip():
            field_name = info.field_name if hasattr(info, "field_name") else "field"
            raise ValueError(
                f"Required section '{field_name}' cannot be empty or contain only whitespace. "
                f"All 6 sections must have content."
            )
        return v.strip()

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "introduction": (
                    "This document specifies the requirements for the E-commerce Platform. "
                    "The purpose of this SRS is to provide a detailed specification of the "
                    "system's functional and non-functional requirements."
                ),
                "overall_description": (
                    "The system is designed to provide an online shopping platform for customers. "
                    "The product will integrate with payment gateways and inventory management systems."
                ),
                "system_features": (
                    "Feature 1: User Authentication\n"
                    "The system shall allow users to register and login securely.\n\n"
                    "Feature 2: Product Catalog\n"
                    "The system shall display products with images, descriptions, and prices."
                ),
                "external_interface": (
                    "UI: Web-based interface accessible via modern browsers.\n"
                    "API: RESTful API for mobile applications.\n"
                    "Payment Gateway: Integration with Stripe payment processor."
                ),
                "non_functional": (
                    "Performance: Response time < 200ms for 95% of requests.\n"
                    "Security: All communications must use HTTPS/TLS 1.3.\n"
                    "Reliability: System uptime target of 99.9%."
                ),
                "appendices": (
                    "Appendix A: Glossary\n"
                    "API: Application Programming Interface\n"
                    "SRS: Software Requirements Specification\n\n"
                    "Appendix B: Data Models\n"
                    "User entity with fields: id, email, name, created_at"
                ),
                "version": "v1.0",
                "project_name": "E-commerce Platform",
                "last_updated": "2024-01-25T10:30:00Z",
            }
        }

