#!/usr/bin/env python
"""
Script to test that contenttypes migration fix prevents 500 errors.
"""
import os
import sys

# Only setup Django if not already configured
try:
    from django.conf import settings
    if not settings.configured:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
        django.setup()
except ImportError:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
    django.setup()

from django.contrib.contenttypes.models import ContentType
from django.db import connections

def test_contenttypes_fix():
    """Test that ContentType model works without 500 errors."""
    print("🧪 Testing ContentType model functionality...")
    
    try:
        # This should not throw a 500 error
        count = ContentType.objects.count()
        print(f"✅ OK: ContentType.objects.count() = {count}")
        
        # Test that we can query content types
        if count > 0:
            first_ct = ContentType.objects.first()
            print(f"✅ OK: First ContentType: {first_ct.app_label}.{first_ct.model}")
        
        # Test that the table structure is correct
        connection = connections['default']
        cursor = connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'django_content_type'
            ORDER BY column_name
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'name' in columns:
            print("❌ FAIL: django_content_type still has deprecated 'name' column")
            return 1
        else:
            print("✅ OK: django_content_type doesn't have deprecated 'name' column")
        
        print("✅ All ContentType tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ ERROR: ContentType test failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(test_contenttypes_fix()) 