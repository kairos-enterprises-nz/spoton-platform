FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies, including ca-certificates
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    netcat-openbsd \
    postgresql-client \
    ca-certificates \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libxml2 \
    libxslt1.1 \
    fonts-dejavu-core \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY apps/api/requirements.txt apps/api/requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy the rest of the application code
COPY apps/api/ .

# Expose the port the app runs on
EXPOSE 8000

# Specify the command to run on container startup
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "utilitybyte.wsgi:application"]
