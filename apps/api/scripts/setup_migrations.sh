#!/bin/bash
# Migration setup script for PostgreSQL schema routing

echo "🚀 Setting up PostgreSQL schema routing from scratch..."

# Step 1: Ensure schemas exist
echo "📁 Creating PostgreSQL schemas..."
python manage.py ensure_schemas

# Step 2: Remove existing migrations (if any)
echo "🗑️  Removing existing migrations..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

# Step 3: Create fresh migrations
echo "📝 Creating fresh migrations with schema routing..."
python manage.py makemigrations

# Step 4: Apply migrations
echo "⚡ Applying migrations..."
python manage.py migrate

echo "✅ Schema routing setup complete!"
echo ""
echo "Your database now has the following schema organization:"
echo "- users: User management, accounts, roles"
echo "- contracts: All contract types and amendments" 
echo "- energy: Energy operations and infrastructure"
echo "- finance: Billing, payments, and pricing"
echo "- support: Customer support and public pricing"
echo "- metering: Metering infrastructure"
echo "- public: Django core tables only"
