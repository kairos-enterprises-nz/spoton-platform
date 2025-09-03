import os
import django
from django.conf import settings
from django.apps import apps

def clean_all_migrations():
    """
    Deletes all migration files except __init__.py from all installed apps.
    """
    for app_config in apps.get_app_configs():
        # Skip third-party apps
        if 'site-packages' in app_config.path:
            continue
            
        migrations_path = os.path.join(app_config.path, 'migrations')
        if not os.path.exists(migrations_path):
            continue
            
        print(f"Cleaning migrations for {app_config.name}...")
        for filename in os.listdir(migrations_path):
            if filename.endswith('.py') and filename != '__init__.py':
                file_path = os.path.join(migrations_path, filename)
                os.remove(file_path)
                print(f"  - Deleted {filename}")

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
    django.setup()
    clean_all_migrations()
