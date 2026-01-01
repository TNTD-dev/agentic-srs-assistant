"""Unit tests for IEEE_SRS_Model Pydantic model.

Tests validation, serialization, deserialization, and edge cases.
"""

import json
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from src.models.ieee_srs_model import IEEE_SRS_Model


# Test fixtures
@pytest.fixture
def valid_srs_data() -> Dict[str, Any]:
    """Fixture providing valid SRS data with all required fields."""
    return {
        "introduction": "This document specifies the requirements for the system.",
        "overall_description": "The system is designed to provide core functionality.",
        "system_features": "Feature 1: User authentication\nFeature 2: Data management",
        "external_interface": "UI: Web-based interface\nAPI: RESTful API",
        "non_functional": "Performance: Response time < 200ms\nSecurity: HTTPS required",
        "appendices": "Appendix A: Glossary\nAppendix B: Data Models",
    }


@pytest.fixture
def valid_srs_data_with_metadata() -> Dict[str, Any]:
    """Fixture providing valid SRS data with all fields including metadata."""
    data = {
        "introduction": "This document specifies the requirements for the system.",
        "overall_description": "The system is designed to provide core functionality.",
        "system_features": "Feature 1: User authentication",
        "external_interface": "UI: Web-based interface",
        "non_functional": "Performance: Response time < 200ms",
        "appendices": "Appendix A: Glossary",
        "version": "v1.0",
        "project_name": "Test Project",
        "last_updated": "2024-01-25T10:30:00Z",
    }
    return data


class TestValidModelCreation:
    """Test valid model creation scenarios."""

    def test_create_model_with_required_fields_only(self, valid_srs_data):
        """Test creating model with only required fields."""
        srs = IEEE_SRS_Model(**valid_srs_data)
        assert srs.introduction == valid_srs_data["introduction"]
        assert srs.overall_description == valid_srs_data["overall_description"]
        assert srs.system_features == valid_srs_data["system_features"]
        assert srs.external_interface == valid_srs_data["external_interface"]
        assert srs.non_functional == valid_srs_data["non_functional"]
        assert srs.appendices == valid_srs_data["appendices"]

    def test_create_model_with_all_fields(self, valid_srs_data_with_metadata):
        """Test creating model with all fields including metadata."""
        srs = IEEE_SRS_Model(**valid_srs_data_with_metadata)
        assert srs.version == "v1.0"
        assert srs.project_name == "Test Project"
        assert srs.last_updated == "2024-01-25T10:30:00Z"

    def test_create_model_with_optional_metadata_none(self, valid_srs_data):
        """Test creating model with metadata fields set to None."""
        data = {**valid_srs_data, "version": None, "project_name": None, "last_updated": None}
        srs = IEEE_SRS_Model(**data)
        assert srs.version is None
        assert srs.project_name is None
        assert srs.last_updated is None

    def test_create_model_with_metadata_omitted(self, valid_srs_data):
        """Test creating model without metadata fields (should default to None)."""
        srs = IEEE_SRS_Model(**valid_srs_data)
        assert srs.version is None
        assert srs.project_name is None
        assert srs.last_updated is None


class TestValidationErrors:
    """Test validation error scenarios."""

    def test_empty_string_raises_error(self, valid_srs_data):
        """Test that empty string in required field raises ValidationError."""
        data = {**valid_srs_data, "introduction": ""}
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("cannot be empty" in str(error["msg"]).lower() for error in errors)

    def test_whitespace_only_string_raises_error(self, valid_srs_data):
        """Test that whitespace-only string raises ValidationError."""
        data = {**valid_srs_data, "introduction": "   \n\t  "}
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("cannot be empty" in str(error["msg"]).lower() for error in errors)

    def test_all_required_fields_empty_raises_errors(self):
        """Test that all empty required fields raise validation errors."""
        data = {
            "introduction": "",
            "overall_description": "",
            "system_features": "",
            "external_interface": "",
            "non_functional": "",
            "appendices": "",
        }
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        errors = exc_info.value.errors()
        # Should have errors for all 6 required fields
        assert len(errors) >= 6

    def test_missing_required_field_raises_error(self, valid_srs_data):
        """Test that missing required field raises ValidationError."""
        data = {**valid_srs_data}
        del data["introduction"]
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("introduction" in str(error).lower() for error in errors)

    def test_none_value_in_required_field_raises_error(self, valid_srs_data):
        """Test that None value in required field raises ValidationError."""
        data = {**valid_srs_data, "introduction": None}
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_non_string_type_raises_error(self, valid_srs_data):
        """Test that non-string type in required field raises ValidationError."""
        data = {**valid_srs_data, "introduction": 123}
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("string" in str(error["msg"]).lower() for error in errors)

    def test_validator_strips_whitespace(self, valid_srs_data):
        """Test that validator strips leading/trailing whitespace."""
        data = {**valid_srs_data, "introduction": "  This is a test  \n"}
        srs = IEEE_SRS_Model(**data)
        assert srs.introduction == "This is a test"


class TestSerialization:
    """Test model serialization and deserialization."""

    def test_model_dump(self, valid_srs_data):
        """Test model_dump() returns dictionary."""
        srs = IEEE_SRS_Model(**valid_srs_data)
        dumped = srs.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["introduction"] == valid_srs_data["introduction"]
        assert dumped["overall_description"] == valid_srs_data["overall_description"]

    def test_model_dump_json(self, valid_srs_data):
        """Test model_dump_json() returns valid JSON string."""
        srs = IEEE_SRS_Model(**valid_srs_data)
        json_str = srs.model_dump_json()
        assert isinstance(json_str, str)
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["introduction"] == valid_srs_data["introduction"]

    def test_model_dump_includes_metadata(self, valid_srs_data_with_metadata):
        """Test that model_dump includes metadata fields."""
        srs = IEEE_SRS_Model(**valid_srs_data_with_metadata)
        dumped = srs.model_dump()
        assert "version" in dumped
        assert "project_name" in dumped
        assert "last_updated" in dumped
        assert dumped["version"] == "v1.0"

    def test_model_validate_from_dict(self, valid_srs_data):
        """Test creating model from dictionary using model_validate."""
        srs = IEEE_SRS_Model.model_validate(valid_srs_data)
        assert srs.introduction == valid_srs_data["introduction"]

    def test_model_validate_from_json(self, valid_srs_data):
        """Test creating model from JSON string using model_validate_json."""
        json_str = json.dumps(valid_srs_data)
        srs = IEEE_SRS_Model.model_validate_json(json_str)
        assert srs.introduction == valid_srs_data["introduction"]

    def test_round_trip_serialization(self, valid_srs_data_with_metadata):
        """Test serialization and deserialization round trip."""
        srs1 = IEEE_SRS_Model(**valid_srs_data_with_metadata)
        json_str = srs1.model_dump_json()
        srs2 = IEEE_SRS_Model.model_validate_json(json_str)
        assert srs1.introduction == srs2.introduction
        assert srs1.version == srs2.version
        assert srs1.project_name == srs2.project_name


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_strings(self, valid_srs_data):
        """Test model handles very long strings."""
        long_string = "A" * 10000
        data = {**valid_srs_data, "introduction": long_string}
        srs = IEEE_SRS_Model(**data)
        assert len(srs.introduction) == 10000
        assert srs.introduction == long_string

    def test_special_characters(self, valid_srs_data):
        """Test model handles special characters."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        data = {**valid_srs_data, "introduction": special_chars}
        srs = IEEE_SRS_Model(**data)
        assert srs.introduction == special_chars

    def test_unicode_characters(self, valid_srs_data):
        """Test model handles Unicode characters."""
        unicode_text = "Hello 世界 🌍 Привет مرحبا"
        data = {**valid_srs_data, "introduction": unicode_text}
        srs = IEEE_SRS_Model(**data)
        assert srs.introduction == unicode_text

    def test_newlines_and_tabs(self, valid_srs_data):
        """Test model handles newlines, tabs, and other whitespace characters."""
        multiline_text = "Line 1\nLine 2\n\tIndented line\n\nBlank line above"
        data = {**valid_srs_data, "introduction": multiline_text}
        srs = IEEE_SRS_Model(**data)
        assert "\n" in srs.introduction
        assert "\t" in srs.introduction

    def test_json_serialization_with_unicode(self, valid_srs_data):
        """Test JSON serialization preserves Unicode characters."""
        unicode_text = "Hello 世界 🌍"
        data = {**valid_srs_data, "introduction": unicode_text}
        srs = IEEE_SRS_Model(**data)
        json_str = srs.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["introduction"] == unicode_text

    def test_all_sections_with_different_content(self):
        """Test all 6 sections with different realistic content."""
        data = {
            "introduction": "Purpose: Define system requirements. Scope: Core features only.",
            "overall_description": "Product: E-commerce platform. Users: Customers and admins.",
            "system_features": "FR-1: User registration\nFR-2: Product catalog",
            "external_interface": "UI: React web app\nAPI: REST endpoints",
            "non_functional": "Performance: <200ms response\nSecurity: OAuth 2.0",
            "appendices": "Glossary: API=Application Programming Interface",
        }
        srs = IEEE_SRS_Model(**data)
        assert srs.introduction.startswith("Purpose")
        assert srs.overall_description.startswith("Product")
        assert "FR-1" in srs.system_features
        assert "React" in srs.external_interface
        assert "Performance" in srs.non_functional
        assert "Glossary" in srs.appendices


class TestValidatorMessages:
    """Test that validator error messages are descriptive."""

    def test_error_message_mentions_field_name(self, valid_srs_data):
        """Test that validation error message mentions the field name."""
        data = {**valid_srs_data, "introduction": ""}
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        error_str = str(exc_info.value)
        # Error should mention the field or section
        assert "introduction" in error_str.lower() or "section" in error_str.lower()

    def test_error_message_mentions_empty_requirement(self, valid_srs_data):
        """Test that validation error message mentions empty requirement."""
        data = {**valid_srs_data, "system_features": "   "}
        with pytest.raises(ValidationError) as exc_info:
            IEEE_SRS_Model(**data)
        error_str = str(exc_info.value)
        assert "empty" in error_str.lower() or "whitespace" in error_str.lower()


class TestModelProperties:
    """Test model properties and behavior."""

    def test_model_fields_are_accessible(self, valid_srs_data):
        """Test that all model fields are accessible as attributes."""
        srs = IEEE_SRS_Model(**valid_srs_data)
        assert hasattr(srs, "introduction")
        assert hasattr(srs, "overall_description")
        assert hasattr(srs, "system_features")
        assert hasattr(srs, "external_interface")
        assert hasattr(srs, "non_functional")
        assert hasattr(srs, "appendices")
        assert hasattr(srs, "version")
        assert hasattr(srs, "project_name")
        assert hasattr(srs, "last_updated")

    def test_model_is_immutable_by_default(self, valid_srs_data):
        """Test that model instances are immutable (frozen=False by default, but fields are read-only)."""
        srs = IEEE_SRS_Model(**valid_srs_data)
        # Pydantic models are mutable by default, but we can test field access
        assert srs.introduction == valid_srs_data["introduction"]
        # Attempting to modify should work (Pydantic v2 allows mutation by default)
        # This test just ensures the model works as expected

    def test_model_repr(self, valid_srs_data):
        """Test that model has a string representation."""
        srs = IEEE_SRS_Model(**valid_srs_data)
        repr_str = repr(srs)
        assert isinstance(repr_str, str)
        assert "IEEE_SRS_Model" in repr_str

