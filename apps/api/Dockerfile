FROM python:3.11-slim

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
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app
RUN mkdir -p logs

# Copy and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Specify the command to run on container startup
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "utilitybyte.wsgi:application"]
