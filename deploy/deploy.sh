  GNU nano 6.2                            deploy.sh *                                   
#!/bin/bash
set -e

SERVICE_NAME="craftcore-api"

echo "🚀 Starting deployment..."

echo "🔄 Pulling latest changes..."
git fetch origin
git reset --hard origin/main || git reset --hard origin/master

echo "📦 Installing dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

echo "🔄 Restarting service..."
if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
    sudo systemctl restart "${SERVICE_NAME}"
    echo "✅ Service restarted"
elif systemctl list-unit-files | grep -q "${SERVICE_NAME}"; then
    sudo systemctl restart "${SERVICE_NAME}" || echo "⚠️  Failed to restart service"
else
    echo "⚠️  Service '${SERVICE_NAME}' not found, skipping restart"
    echo "💡 You may need to restart the application manually"
fi

echo "✅ Deployment completed successfully!"