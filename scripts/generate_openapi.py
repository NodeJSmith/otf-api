#!/usr/bin/env python3
"""Generate OpenAPI schema from Pydantic models for TypeScript consumption."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Type
import inspect

import yaml
from pydantic import BaseModel

# Add src to path so we can import otf_api modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import otf_api.models as models


def get_all_pydantic_models() -> Dict[str, Type[BaseModel]]:
    """Discover all Pydantic models from otf_api.models.__all__."""
    pydantic_models = {}
    
    # Get all exported items from models module
    for name in models.__all__:
        try:
            obj = getattr(models, name)
            # Check if it's a Pydantic model (class that inherits from BaseModel)
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseModel) and 
                obj is not BaseModel):
                pydantic_models[name] = obj
        except (AttributeError, TypeError):
            # Skip non-model items like functions, constants, etc.
            continue
    
    return pydantic_models


def generate_openapi_schema() -> Dict[str, Any]:
    """Generate complete OpenAPI schema from all discovered models."""
    
    # Discover all Pydantic models automatically
    models_dict = get_all_pydantic_models()
    
    print(f"Found {len(models_dict)} Pydantic models:")
    for name in sorted(models_dict.keys()):
        print(f"  - {name}")
    
    # Generate a combined schema with all models
    all_schemas = []
    for model in models_dict.values():
        all_schemas.append(model)
    
    # Use Pydantic's built-in schema generation for all models at once
    from pydantic import TypeAdapter
    
    # Create a union of all models to generate a complete schema
    combined_schema = {}
    all_definitions = {}
    
    for name, model in models_dict.items():
        try:
            # Generate schema using model field names (not aliases)
            # This ensures we get snake_case field names that match Python usage
            schema = model.model_json_schema(by_alias=False)
            
            # Process the main schema
            main_schema = {k: v for k, v in schema.items() if k != "$defs"}
            combined_schema[name] = main_schema
            
            # Collect all $defs from all schemas
            if "$defs" in schema:
                for def_name, def_value in schema["$defs"].items():
                    # Flatten nested $defs recursively
                    _flatten_defs(def_value, all_definitions)
                    all_definitions[def_name] = def_value
                    
        except Exception as e:
            print(f"Warning: Could not generate schema for {name}: {e}")
            continue
    
    # Update all references to use components/schemas
    _update_all_refs(combined_schema)
    _update_all_refs(all_definitions)
    
    # Merge all schemas
    final_schemas = {**combined_schema, **all_definitions}
    
    # Create OpenAPI document structure
    openapi_doc = {
        "openapi": "3.0.3",
        "info": {
            "title": "OTF API Models",
            "version": getattr(models, "__version__", "1.0.0"),
            "description": "Generated TypeScript models from Python Pydantic models",
        },
        "components": {
            "schemas": final_schemas
        }
    }
    
    return openapi_doc


def _flatten_defs(schema: Dict[str, Any], all_definitions: Dict[str, Any]) -> None:
    """Recursively flatten nested $defs."""
    if isinstance(schema, dict) and "$defs" in schema:
        for def_name, def_value in schema["$defs"].items():
            _flatten_defs(def_value, all_definitions)
            all_definitions[def_name] = def_value
        # Remove nested $defs after flattening
        del schema["$defs"]


def _update_all_refs(obj: Any) -> None:
    """Recursively update all $ref paths to use components/schemas format."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "$ref" and isinstance(value, str):
                if value.startswith("#/$defs/"):
                    def_name = value.replace("#/$defs/", "")
                    obj[key] = f"#/components/schemas/{def_name}"
            else:
                _update_all_refs(value)
    elif isinstance(obj, list):
        for item in obj:
            _update_all_refs(item)


def main():
    """Generate and save OpenAPI schema."""
    try:
        schema = generate_openapi_schema()
        
        # Create schema directory
        schema_dir = Path(__file__).parent.parent / "schema"
        schema_dir.mkdir(exist_ok=True)
        
        # Write YAML file
        yaml_file = schema_dir / "openapi.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(schema, f, default_flow_style=False, sort_keys=False)
        
        # Also write JSON file for backup
        json_file = schema_dir / "openapi.json"
        with open(json_file, "w") as f:
            json.dump(schema, f, indent=2)
        
        print(f"\n✅ Generated OpenAPI schema:")
        print(f"   YAML: {yaml_file}")
        print(f"   JSON: {json_file}")
        print(f"   Models: {len(schema['components']['schemas'])}")
        
    except Exception as e:
        print(f"❌ Error generating schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()