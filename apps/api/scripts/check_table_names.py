#!/usr/bin/env python3
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'utilitybyte.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'users' ORDER BY tablename;")
    tables = cursor.fetchall()
    print("Tables in users schema:")
    for table in tables:
        print(f"  {table[0]}") 