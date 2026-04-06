#!/usr/bin/env python3
"""
Filu-X JSON Validator - Simplified version with combined schema
"""

import json
import jsonschema
import argparse
from pathlib import Path

def validate_filu_x(file_path: Path, schema_path: Path):
    """Validoi Filu-X-tiedosto yhdistetyllä schemalla"""
    
    # Tarkista että tiedosto on olemassa
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    # Lataa schema
    if not schema_path.exists():
        print(f"❌ Schema not found: {schema_path}")
        return False
    
    print(f"\n📄 Validating: {file_path}")
    print(f"📖 Using schema: {schema_path}")
    
    with open(schema_path) as f:
        schema = json.load(f)
    
    # Lataa validoitava tiedosto
    with open(file_path) as f:
        data = json.load(f)
    
    # Validoi
    try:
        jsonschema.validate(data, schema)
        print(f"✅ {file_path}: Valid Filu-X document")
        return True
        
    except jsonschema.ValidationError as e:
        print(f"❌ {file_path}: Invalid - {e.message}")
        print(f"   Path: {list(e.path)}")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error - {e}")
        return False

def validate_all(schema_path: Path):
    """Validoi kaikki examples/ alakansioiden JSON-tiedostot"""
    examples_dir = Path("examples")
    
    if not examples_dir.exists():
        print(f"❌ Examples directory not found: {examples_dir}")
        return
    
    json_files = list(examples_dir.rglob("*.json"))
    
    if not json_files:
        print("❌ No JSON files found in examples/")
        return
    
    print(f"🔍 Found {len(json_files)} JSON files to validate\n")
    print("=" * 60)
    
    valid = 0
    for json_file in sorted(json_files):
        if validate_filu_x(json_file, schema_path):
            valid += 1
        print("-" * 40)
    
    print(f"\n📊 Summary: {valid}/{len(json_files)} valid")
    
    if valid == len(json_files):
        print("✅ All examples are valid!")
    else:
        print(f"❌ {len(json_files) - valid} examples failed validation")

def main():
    parser = argparse.ArgumentParser(description="Validate Filu-X JSON files")
    parser.add_argument("file", nargs="?", help="Filu-X JSON file to validate (optional)")
    parser.add_argument("--schema", default="./spec/001.000.000/schema-combined.json",
                       help="Schema file (default: ./spec/001.000.000/schema-combined.json)")
    parser.add_argument("--all", action="store_true", 
                       help="Validate all examples in examples/ directory")
    
    args = parser.parse_args()
    
    schema_path = Path(args.schema)
    
    if args.all:
        validate_all(schema_path)
    elif args.file:
        validate_filu_x(Path(args.file), schema_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
