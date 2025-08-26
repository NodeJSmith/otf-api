#!/usr/bin/env python3
"""
Validation script to ensure TypeScript types stay in sync with Python models.
This script should be run as part of the automated sync pipeline.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Set
import yaml

# Add the Python package to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "python" / "src"))

try:
    from otf_api import models
    from otf_api.models.base import OtfItemBase
    from pydantic import BaseModel
except ImportError as e:
    print(f"Error importing Python modules: {e}")
    sys.exit(1)

def get_python_models() -> Dict[str, type]:
    """Get all Python Pydantic models."""
    all_models = {}
    
    for name in models.__all__:
        obj = getattr(models, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel):
            all_models[name] = obj
    
    return all_models

def get_python_model_fields(model: type) -> Set[str]:
    """Get field names from Python model (using Python field names, not aliases)."""
    return set(model.model_fields.keys())

def get_schema_model_fields(schema_path: Path, model_name: str) -> Set[str]:
    """Get field names from OpenAPI schema."""
    try:
        with open(schema_path) as f:
            schema = yaml.safe_load(f)
        
        if not schema.get('components', {}).get('schemas', {}).get(model_name):
            return set()
        
        model_schema = schema['components']['schemas'][model_name]
        return set(model_schema.get('properties', {}).keys())
    
    except Exception as e:
        print(f"Error reading schema: {e}")
        return set()

def validate_sync() -> bool:
    """Validate that schema reflects Python model field names exactly."""
    print("🔍 Validating TypeScript-Python sync...")
    
    # Paths
    schema_path = Path(__file__).parent.parent / "schema" / "openapi.yaml"
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    # Get Python models
    python_models = get_python_models()
    print(f"📋 Found {len(python_models)} Python models")
    
    # Validation results
    all_valid = True
    validation_results = {}
    
    for model_name, model_class in python_models.items():
        print(f"\n🔍 Validating {model_name}...")
        
        # Get field names
        python_fields = get_python_model_fields(model_class)
        schema_fields = get_schema_model_fields(schema_path, model_name)
        
        # Compare
        missing_in_schema = python_fields - schema_fields
        extra_in_schema = schema_fields - python_fields
        
        validation_results[model_name] = {
            'python_fields': len(python_fields),
            'schema_fields': len(schema_fields),
            'missing_in_schema': list(missing_in_schema),
            'extra_in_schema': list(extra_in_schema),
            'valid': len(missing_in_schema) == 0 and len(extra_in_schema) == 0
        }
        
        if validation_results[model_name]['valid']:
            print(f"  ✅ {model_name}: {len(python_fields)} fields match")
        else:
            print(f"  ❌ {model_name}: Field mismatch detected")
            all_valid = False
            
            if missing_in_schema:
                print(f"     Missing in schema: {', '.join(missing_in_schema)}")
            if extra_in_schema:
                print(f"     Extra in schema: {', '.join(extra_in_schema)}")
    
    # Summary
    valid_count = sum(1 for r in validation_results.values() if r['valid'])
    total_count = len(validation_results)
    
    print(f"\n📊 Summary: {valid_count}/{total_count} models in sync")
    
    if all_valid:
        print("✅ All models are properly synced! Python fields are source of truth.")
    else:
        print("❌ Sync validation failed! Schema does not match Python models.")
        print("\n💡 To fix:")
        print("   1. Run: cd python && uv run python ../scripts/generate_openapi.py")
        print("   2. Run: cd typescript && npm run generate-types")
        print("   3. Update TypeScript transformation code to match generated types")
    
    return all_valid

def main():
    """Main function."""
    try:
        is_valid = validate_sync()
        sys.exit(0 if is_valid else 1)
    except Exception as e:
        print(f"❌ Validation script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()