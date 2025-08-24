#!/usr/bin/env python3
"""Generate OpenAPI specification from Python models."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Set, get_origin, get_args
import yaml

# Add the Python package to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "python" / "src"))

try:
    from pydantic import BaseModel
    from otf_api import models
    from otf_api.models.base import OtfItemBase
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're in the correct directory and dependencies are installed")
    sys.exit(1)

def get_all_models() -> Dict[str, type]:
    """Get all Pydantic models from otf_api.models."""
    all_models = {}
    
    # Get all exported models from the models module
    for name in models.__all__:
        obj = getattr(models, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel):
            all_models[name] = obj
    
    return all_models

def get_model_schema_with_refs(model: type) -> Dict[str, Any]:
    """Get JSON schema for a model, extracting references."""
    try:
        # Use Python field names as source of truth, not validation_alias names
        schema = model.model_json_schema(by_alias=False)
        return schema
    except Exception as e:
        print(f"Warning: Could not generate schema for {model.__name__}: {e}")
        return {
            "type": "object",
            "description": f"Schema generation failed for {model.__name__}"
        }

def extract_definitions(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Extract $defs from schema and return them as separate definitions."""
    definitions = {}
    if "$defs" in schema:
        definitions.update(schema["$defs"])
        # Remove $defs from the main schema
        del schema["$defs"]
    return definitions

def clean_schema_refs(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Pydantic $ref format to OpenAPI format."""
    if isinstance(schema, dict):
        cleaned = {}
        for key, value in schema.items():
            if key == "$ref" and isinstance(value, str):
                # Convert from "#/$defs/ModelName" to "#/components/schemas/ModelName"
                if value.startswith("#/$defs/"):
                    model_name = value[8:]  # Remove "#/$defs/"
                    cleaned[key] = f"#/components/schemas/{model_name}"
                else:
                    cleaned[key] = value
            else:
                cleaned[key] = clean_schema_refs(value)
        return cleaned
    elif isinstance(schema, list):
        return [clean_schema_refs(item) for item in schema]
    else:
        return schema

def generate_openapi_spec() -> Dict[str, Any]:
    """Generate OpenAPI specification from otf_api models."""
    
    print("Discovering Pydantic models...")
    all_models = get_all_models()
    print(f"Found {len(all_models)} models: {', '.join(all_models.keys())}")
    
    # Generate schemas for all models
    all_schemas = {}
    all_definitions = {}
    
    for name, model in all_models.items():
        print(f"Processing {name}...")
        schema = get_model_schema_with_refs(model)
        
        # Extract any nested definitions
        definitions = extract_definitions(schema)
        all_definitions.update(definitions)
        
        # Clean the main schema
        cleaned_schema = clean_schema_refs(schema)
        all_schemas[name] = cleaned_schema
    
    # Also add any extracted definitions as top-level schemas
    for def_name, def_schema in all_definitions.items():
        if def_name not in all_schemas:
            all_schemas[def_name] = clean_schema_refs(def_schema)
    
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "OrangeTheory Fitness API",
            "description": "Unofficial API specification for OrangeTheory Fitness services. Generated from Python Pydantic models.",
            "version": "0.15.4",
            "contact": {
                "name": "OTF API",
                "url": "https://github.com/NodeJSmith/otf-api"
            },
            "license": {
                "name": "MIT"
            }
        },
        "servers": [
            {
                "url": "https://api.orangetheory.co",
                "description": "Main API server"
            },
            {
                "url": "https://api.orangetheory.io",
                "description": "New API server"
            },
            {
                "url": "https://api.yuzu.orangetheory.com",
                "description": "Telemetry API server"
            }
        ],
        "security": [
            {"CognitoAuth": []},
            {"SigV4Auth": []}
        ],
        "components": {
            "securitySchemes": {
                "CognitoAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "AWS Cognito JWT token"
                },
                "SigV4Auth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization",
                    "description": "AWS SigV4 signature"
                }
            },
            "schemas": all_schemas
        }
    }
    
    return spec

def write_openapi_spec(spec: Dict[str, Any], output_file: Path) -> None:
    """Write OpenAPI spec to YAML file."""
    output_file.parent.mkdir(exist_ok=True)
    
    # Write as YAML
    with open(output_file, 'w') as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"Generated OpenAPI specification with {len(spec['components']['schemas'])} schemas")
    print(f"Written to: {output_file}")

def main():
    """Main function."""
    try:
        spec = generate_openapi_spec()
        
        # Write to schema directory
        schema_dir = Path(__file__).parent.parent / "schema"
        schema_file = schema_dir / "openapi.yaml"
        
        write_openapi_spec(spec, schema_file)
        
        # Also write a JSON version for debugging
        json_file = schema_dir / "openapi.json"
        with open(json_file, 'w') as f:
            json.dump(spec, f, indent=2)
        
        print(f"Also created JSON version at: {json_file}")
        
    except Exception as e:
        print(f"Error generating OpenAPI specification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()