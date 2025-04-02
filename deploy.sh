#!/bin/bash

# Deployment Script for Inventory Management System
# This script automates the deployment process for the Inventory Management System

# Exit on error
set -e

echo "Starting deployment of Inventory Management System..."

# Check if Python 3.10+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Check Python version
python_version=$(python3 --version | cut -d " " -f 2)
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 10 ]); then
    echo "Python 3.10 or higher is required. Current version: $python_version"
    echo "Please upgrade Python and try again."
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
fi

# Create deployment directory
DEPLOY_DIR="/opt/inventory_system"
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Creating deployment directory..."
    sudo mkdir -p $DEPLOY_DIR
    sudo chown $(whoami):$(whoami) $DEPLOY_DIR
fi

# Copy application files
echo "Copying application files..."
cp -r . $DEPLOY_DIR

# Create virtual environment
echo "Setting up virtual environment..."
cd $DEPLOY_DIR
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file
echo "Creating environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=postgres://inventory_user:inventory_password@localhost:5432/inventory_db
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
fi

# Setup database
echo "Setting up database..."
sudo -u postgres psql -c "CREATE USER inventory_user WITH PASSWORD 'inventory_password';" || echo "User already exists"
sudo -u postgres psql -c "CREATE DATABASE inventory_db OWNER inventory_user;" || echo "Database already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;"

# Apply migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if needed
if [ "$1" == "--create-superuser" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser
fi

# Setup Gunicorn service
echo "Setting up Gunicorn service..."
sudo bash -c 'cat > /etc/systemd/system/inventory.service << EOF
[Unit]
Description=Inventory Management System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/inventory_system
ExecStart=/opt/inventory_system/venv/bin/gunicorn inventory_project.wsgi:application --workers 3 --bind 127.0.0.1:8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF'

# Setup Nginx configuration
echo "Setting up Nginx configuration..."
if command -v nginx &> /dev/null; then
    sudo bash -c 'cat > /etc/nginx/sites-available/inventory << EOF
server {
    listen 80;
    server_name localhost;

    location /static/ {
        alias /opt/inventory_system/static/;
    }

    location /media/ {
        alias /opt/inventory_system/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF'

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
    
    # Test Nginx configuration
    sudo nginx -t
    
    # Restart Nginx
    sudo systemctl restart nginx
else
    echo "Nginx is not installed. Skipping Nginx configuration."
fi

# Set proper permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data $DEPLOY_DIR
sudo chmod -R 755 $DEPLOY_DIR

# Start the service
echo "Starting the service..."
sudo systemctl daemon-reload
sudo systemctl enable inventory
sudo systemctl start inventory

echo "Deployment completed successfully!"
echo "You can access the application at: http://localhost"
echo "For more information, refer to the admin_guide.md file."
