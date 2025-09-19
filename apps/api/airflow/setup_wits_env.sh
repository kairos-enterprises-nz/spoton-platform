#!/bin/bash
"""
WITS Environment Setup Script
Sets up required environment variables for NZX SFTP connection
"""

echo "🔧 WITS Environment Setup"
echo "========================="
echo ""

# Check if .env file exists
ENV_FILE="/app/.env"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE=".env"
fi

echo "📝 Setting up NZX SFTP connection variables..."
echo ""

# Function to add or update environment variable
update_env_var() {
    local var_name="$1"
    local var_value="$2"
    local env_file="$3"
    
    if grep -q "^${var_name}=" "$env_file" 2>/dev/null; then
        # Update existing
        sed -i "s/^${var_name}=.*/${var_name}=${var_value}/" "$env_file"
        echo "✅ Updated ${var_name}"
    else
        # Add new
        echo "${var_name}=${var_value}" >> "$env_file"
        echo "✅ Added ${var_name}"
    fi
}

# Default values (update these with real values)
NZX_HOST="192.168.1.10"
NZX_PORT="2222"
NZX_USER="wits"
NZX_PASS="your-nzx-password-here"
NZX_REMOTE_PATH="/wits/prices"
NZX_TIMEOUT="30"

echo "Setting up with default values:"
echo "  NZX_HOST: $NZX_HOST"
echo "  NZX_PORT: $NZX_PORT"
echo "  NZX_USER: $NZX_USER"
echo "  NZX_PASS: [MASKED]"
echo "  NZX_REMOTE_PATH: $NZX_REMOTE_PATH"
echo ""

# Update environment file
update_env_var "NZX_HOST" "$NZX_HOST" "$ENV_FILE"
update_env_var "NZX_PORT" "$NZX_PORT" "$ENV_FILE"
update_env_var "NZX_USER" "$NZX_USER" "$ENV_FILE"
update_env_var "NZX_PASS" "$NZX_PASS" "$ENV_FILE"
update_env_var "NZX_REMOTE_PATH" "$NZX_REMOTE_PATH" "$ENV_FILE"
update_env_var "NZX_TIMEOUT" "$NZX_TIMEOUT" "$ENV_FILE"

echo ""
echo "🎯 Next Steps:"
echo "1. Edit $ENV_FILE and update NZX_PASS with the real password"
echo "2. Verify NZX_HOST is correct for your environment"
echo "3. Test connection: python3 debug_wits_fetch.py"
echo "4. Restart Airflow to load new environment variables"
echo ""
echo "⚠️  IMPORTANT: Never commit real passwords to version control!"
echo ""
echo "📋 Current environment file: $ENV_FILE" 