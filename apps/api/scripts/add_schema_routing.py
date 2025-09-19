#!/usr/bin/env python3
"""
Script to add proper schema routing to Django models
"""

import os
import re

# Schema mapping based on app labels
SCHEMA_MAPPING = {
    'users': 'users',
    'user_details': 'users', 
    'contracts': 'contracts',
    'billing': 'finance',
    'pricing': 'finance',
    'connections': 'energy',
    'tariffs': 'energy',
    'tariff_profile': 'energy',
    'validation': 'energy',
    'export_core': 'energy',
    'metering': 'metering',
    'address_plans': 'support',
    'public_pricing': 'support',
}

def add_schema_to_models():
    """Add schema routing to all models"""
    
    for app_name, schema_name in SCHEMA_MAPPING.items():
        # Find models.py files for this app
        models_files = []
        
        # Check different possible locations
        possible_paths = [
            f'{app_name}/models.py',
            f'core/{app_name}/models.py',
            f'energy/{app_name}/models.py',
            f'finance/{app_name}/models.py',
            f'web_support/{app_name}/models.py',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                models_files.append(path)
        
        # Process each models file
        for models_file in models_files:
            print(f"Processing {models_file} -> {schema_name} schema")
            
            with open(models_file, 'r') as f:
                content = f.read()
            
            # Find class Meta: blocks and add db_table if not present
            # This is a simple regex - for production use, you'd want a proper AST parser
            pattern = r'(class\s+(\w+)\(.*?models\.Model.*?\):.*?)(class Meta:.*?)(\n\s+def|\n\nclass|\nclass|\Z)'
            
            def add_db_table(match):
                model_class = match.group(2)
                meta_block = match.group(3)
                after_meta = match.group(4)
                
                # Convert CamelCase to snake_case for table name
                table_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', model_class)
                table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', table_name).lower()
                
                # Add app prefix if not already present
                if not table_name.startswith(app_name):
                    table_name = f"{app_name}_{table_name}"
                
                # Check if db_table already exists
                if 'db_table' not in meta_block:
                    # Add db_table after class Meta:
                    new_meta = meta_block + f"\n        db_table = '{schema_name}.{table_name}'"
                else:
                    new_meta = meta_block
                
                return match.group(1) + new_meta + after_meta
            
            # Apply the transformation
            new_content = re.sub(pattern, add_db_table, content, flags=re.DOTALL)
            
            # Write back if changed
            if new_content != content:
                with open(models_file, 'w') as f:
                    f.write(new_content)
                print(f"  ✅ Updated {models_file}")
            else:
                print(f"  ⏭️  No changes needed for {models_file}")

if __name__ == '__main__':
    add_schema_routing()
    print("\n✅ Schema routing added to all models!")
    print("\nNext steps:")
    print("1. Run: python manage.py ensure_schemas")
    print("2. Delete existing migrations: find . -path '*/migrations/*.py' -not -name '__init__.py' -delete")
    print("3. Create new migrations: python manage.py makemigrations")
    print("4. Apply migrations: python manage.py migrate") 