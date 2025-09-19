#!/bin/sh

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}

echo "🔄 Waiting for DB at $DB_HOST:$DB_PORT..."

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  echo "⏳ DB not ready yet — sleeping..."
  sleep 1
done

echo "✅ DB is ready — continuing..."

echo "⚙️ Running migrations..."
python manage.py migrate

echo "🎒 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn utilitybyte.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 120
