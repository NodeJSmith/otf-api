"""Tests for OpenAPI schema generation from Pydantic models."""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from pydantic import BaseModel

# Add the scripts directory to path to import the generator
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_openapi import (
    generate_openapi_spec,
    get_all_models,
    get_model_schema_with_refs,
    extract_definitions,
    clean_schema_refs,
)

from otf_api import models
from otf_api.models import MemberDetail, StudioDetail, Workout, BookingV2, OtfClass


class TestSchemaGeneration:
    """Test OpenAPI schema generation."""

    def test_get_all_models_returns_only_pydantic_models(self):
        """Test that get_all_models only returns Pydantic models."""
        all_models = get_all_models()
        
        # Should have models
        assert len(all_models) > 0
        
        # All should be Pydantic BaseModel subclasses
        for name, model in all_models.items():
            assert isinstance(model, type)
            assert issubclass(model, BaseModel)
        
        # Should include key models
        expected_models = ["MemberDetail", "StudioDetail", "Workout", "BookingV2", "OtfClass"]
        for expected in expected_models:
            assert expected in all_models, f"Expected model {expected} not found"

    def test_model_schema_generation_for_key_models(self):
        """Test that schemas are generated correctly for key models."""
        key_models = [MemberDetail, StudioDetail, Workout, BookingV2, OtfClass]
        
        for model in key_models:
            schema = get_model_schema_with_refs(model)
            
            # Should have basic schema structure
            assert isinstance(schema, dict)
            assert "type" in schema
            assert schema["type"] == "object"
            
            # Should have properties
            assert "properties" in schema
            assert isinstance(schema["properties"], dict)
            assert len(schema["properties"]) > 0
            
            # Should have title matching model name
            assert "title" in schema
            assert schema["title"] == model.__name__

    def test_extract_definitions_removes_defs_from_schema(self):
        """Test that extract_definitions properly extracts and removes $defs."""
        # Create a mock schema with $defs
        schema = {
            "type": "object",
            "properties": {"test": {"$ref": "#/$defs/TestModel"}},
            "$defs": {
                "TestModel": {"type": "string"}
            }
        }
        
        definitions = extract_definitions(schema)
        
        # Should extract the definition
        assert "TestModel" in definitions
        assert definitions["TestModel"] == {"type": "string"}
        
        # Should remove $defs from original schema
        assert "$defs" not in schema

    def test_clean_schema_refs_converts_pydantic_to_openapi_refs(self):
        """Test that schema refs are converted from Pydantic to OpenAPI format."""
        schema = {
            "type": "object",
            "properties": {
                "member": {"$ref": "#/$defs/MemberDetail"},
                "studio": {"$ref": "#/$defs/StudioDetail"}
            },
            "items": [
                {"$ref": "#/$defs/ItemModel"}
            ]
        }
        
        cleaned = clean_schema_refs(schema)
        
        # Check that refs are converted
        assert cleaned["properties"]["member"]["$ref"] == "#/components/schemas/MemberDetail"
        assert cleaned["properties"]["studio"]["$ref"] == "#/components/schemas/StudioDetail"
        assert cleaned["items"][0]["$ref"] == "#/components/schemas/ItemModel"

    def test_generate_full_openapi_spec(self):
        """Test generation of full OpenAPI specification."""
        spec = generate_openapi_spec()
        
        # Check basic OpenAPI structure
        assert "openapi" in spec
        assert spec["openapi"] == "3.0.3"
        
        # Check info section
        assert "info" in spec
        info = spec["info"]
        assert "title" in info
        assert "version" in info
        assert info["version"] == "0.15.4"
        
        # Check servers
        assert "servers" in spec
        assert len(spec["servers"]) >= 1
        
        # Check components
        assert "components" in spec
        components = spec["components"]
        
        # Check security schemes
        assert "securitySchemes" in components
        assert "CognitoAuth" in components["securitySchemes"]
        assert "SigV4Auth" in components["securitySchemes"]
        
        # Check schemas
        assert "schemas" in components
        schemas = components["schemas"]
        assert len(schemas) > 0
        
        # Should include key models
        expected_schemas = ["MemberDetail", "StudioDetail", "Workout", "BookingV2", "OtfClass"]
        for expected in expected_schemas:
            assert expected in schemas, f"Expected schema {expected} not found"

    def test_generated_schemas_have_valid_structure(self):
        """Test that generated schemas have valid OpenAPI structure."""
        spec = generate_openapi_spec()
        schemas = spec["components"]["schemas"]
        
        for name, schema in schemas.items():
            # Basic schema validation
            assert isinstance(schema, dict), f"Schema {name} is not a dict"
            
            # Should have type (most will be object)
            if "type" in schema:
                assert isinstance(schema["type"], str)
            
            # If has properties, should be valid
            if "properties" in schema:
                assert isinstance(schema["properties"], dict)
                
                # Check property structure
                for prop_name, prop_schema in schema["properties"].items():
                    assert isinstance(prop_schema, dict), f"Property {prop_name} in {name} is not a dict"
            
            # Check that refs use OpenAPI format
            self._validate_refs_in_schema(schema, name)

    def _validate_refs_in_schema(self, schema: Any, context: str) -> None:
        """Recursively validate that all $ref use OpenAPI format."""
        if isinstance(schema, dict):
            for key, value in schema.items():
                if key == "$ref" and isinstance(value, str):
                    assert value.startswith("#/components/schemas/"), \
                        f"Invalid ref format '{value}' in {context}"
                else:
                    self._validate_refs_in_schema(value, f"{context}.{key}")
        elif isinstance(schema, list):
            for i, item in enumerate(schema):
                self._validate_refs_in_schema(item, f"{context}[{i}]")

    def test_schema_generation_is_deterministic(self):
        """Test that schema generation produces consistent results."""
        spec1 = generate_openapi_spec()
        spec2 = generate_openapi_spec()
        
        # Should have same number of schemas
        assert len(spec1["components"]["schemas"]) == len(spec2["components"]["schemas"])
        
        # Should have same schema names
        schemas1 = set(spec1["components"]["schemas"].keys())
        schemas2 = set(spec2["components"]["schemas"].keys())
        assert schemas1 == schemas2

    def test_yaml_output_is_valid(self):
        """Test that generated YAML is valid and can be parsed."""
        spec = generate_openapi_spec()
        
        # Convert to YAML
        yaml_content = yaml.dump(spec, default_flow_style=False, sort_keys=False, indent=2)
        
        # Should be able to parse it back
        parsed_spec = yaml.safe_load(yaml_content)
        
        # Should be equivalent
        assert parsed_spec["openapi"] == spec["openapi"]
        assert parsed_spec["info"]["title"] == spec["info"]["title"]
        assert len(parsed_spec["components"]["schemas"]) == len(spec["components"]["schemas"])


class TestModelSpecificSchemas:
    """Test schemas for specific important models."""

    def test_member_detail_schema(self):
        """Test MemberDetail schema has expected fields."""
        schema = get_model_schema_with_refs(MemberDetail)
        properties = schema["properties"]
        
        # Should have key member fields
        expected_fields = ["member_uuid", "first_name", "last_name", "email"]
        for field in expected_fields:
            assert field in properties, f"MemberDetail missing field: {field}"

    def test_studio_detail_schema(self):
        """Test StudioDetail schema has expected fields.""" 
        schema = get_model_schema_with_refs(StudioDetail)
        properties = schema["properties"]
        
        # Should have key studio fields
        expected_fields = ["studio_uuid", "name", "contact_email"]
        for field in expected_fields:
            assert field in properties, f"StudioDetail missing field: {field}"

    def test_workout_schema(self):
        """Test Workout schema has expected fields."""
        schema = get_model_schema_with_refs(Workout)
        properties = schema["properties"]
        
        # Should have key workout fields
        expected_fields = ["performance_summary_id", "booking_id", "class_history_uuid"]
        for field in expected_fields:
            assert field in properties, f"Workout missing field: {field}"

    def test_booking_v2_schema(self):
        """Test BookingV2 schema has expected fields."""
        schema = get_model_schema_with_refs(BookingV2)
        properties = schema["properties"]
        
        # Should have key booking fields
        expected_fields = ["booking_id", "member_uuid", "checked_in"]
        for field in expected_fields:
            assert field in properties, f"BookingV2 missing field: {field}"

    def test_otf_class_schema(self):
        """Test OtfClass schema has expected fields."""
        schema = get_model_schema_with_refs(OtfClass)
        properties = schema["properties"]
        
        # Should have key class fields  
        expected_fields = ["class_uuid", "name", "class_type"]
        for field in expected_fields:
            assert field in properties, f"OtfClass missing field: {field}"


@pytest.fixture
def temp_schema_file(tmp_path):
    """Create a temporary file for testing schema output."""
    return tmp_path / "test_openapi.yaml"


class TestSchemaFileGeneration:
    """Test file generation functionality."""

    def test_schema_file_generation(self, temp_schema_file):
        """Test that schema can be written to file and read back."""
        from generate_openapi import write_openapi_spec
        
        spec = generate_openapi_spec()
        write_openapi_spec(spec, temp_schema_file)
        
        # File should exist
        assert temp_schema_file.exists()
        
        # Should be valid YAML
        with open(temp_schema_file) as f:
            loaded_spec = yaml.safe_load(f)
        
        # Should match original
        assert loaded_spec["openapi"] == spec["openapi"]
        assert loaded_spec["info"]["title"] == spec["info"]["title"]