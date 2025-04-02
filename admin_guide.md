# Administrator Guide - Inventory Management System

## Table of Contents
1. Introduction
2. System Architecture
3. Installation and Setup
4. Database Configuration
5. User Management
6. System Configuration
7. Backup and Recovery
8. Maintenance
9. Security
10. Troubleshooting

## 1. Introduction

This Administrator Guide provides technical information for installing, configuring, and maintaining the Inventory Management System. It is intended for system administrators and IT personnel responsible for deploying and supporting the application.

## 2. System Architecture

The Inventory Management System is built using the following technologies:

- **Backend**: Django (Python) with Django REST Framework
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Database**: PostgreSQL
- **Web Server**: Gunicorn (recommended) with Nginx

The system follows a Model-View-Controller (MVC) architecture:
- Models: Django ORM for database interactions
- Views: Django views and REST API endpoints
- Controllers: JavaScript for client-side logic

## 3. Installation and Setup

### System Requirements
- Python 3.10 or higher
- PostgreSQL 12 or higher
- Nginx (recommended for production)
- Modern web browser for client access

### Installation Steps

#### 1. Set up Python environment
```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

#### 2. Configure environment variables
Create a `.env` file in the project root with the following variables:
```
DEBUG=False
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgres://user:password@localhost:5432/inventory_db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

#### 3. Initialize the database
```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata initial_data.json
```

#### 4. Collect static files
```bash
python manage.py collectstatic
```

#### 5. Test the installation
```bash
python manage.py runserver
```
Navigate to http://localhost:8000 to verify the installation.

#### 6. Production deployment with Gunicorn and Nginx
Install Gunicorn:
```bash
pip install gunicorn
```

Create a systemd service file (on Linux):
```
[Unit]
Description=Inventory Management System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/inventory_system
ExecStart=/path/to/inventory_system/venv/bin/gunicorn inventory_project.wsgi:application --workers 3 --bind 127.0.0.1:8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Configure Nginx:
```
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /static/ {
        alias /path/to/inventory_system/static/;
    }

    location /media/ {
        alias /path/to/inventory_system/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 4. Database Configuration

### PostgreSQL Setup
1. Install PostgreSQL:
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

2. Create database and user:
```bash
sudo -u postgres psql
postgres=# CREATE DATABASE inventory_db;
postgres=# CREATE USER inventory_user WITH PASSWORD 'your_password';
postgres=# ALTER ROLE inventory_user SET client_encoding TO 'utf8';
postgres=# ALTER ROLE inventory_user SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE inventory_user SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
postgres=# \q
```

3. Update the `DATABASE_URL` in your `.env` file:
```
DATABASE_URL=postgres://inventory_user:your_password@localhost:5432/inventory_db
```

### Database Backup
To backup the database:
```bash
pg_dump -U inventory_user -d inventory_db -f backup.sql
```

### Database Restore
To restore from a backup:
```bash
psql -U inventory_user -d inventory_db -f backup.sql
```

## 5. User Management

### User Roles
The system has the following predefined roles:
- **Admin**: Full access to all system features
- **Manager**: Can approve requisitions and access reports
- **Controller**: Can check requisitions before approval
- **Store Keeper**: Manages inventory and issues items
- **Procurement**: Handles purchase requisitions
- **Staff**: Can create requisitions and view inventory

### Creating Users
1. Log in as an administrator
2. Navigate to Admin > Users
3. Click "Add New User"
4. Fill in the required fields:
   - Username
   - Email
   - First Name
   - Last Name
   - Role
   - Department
   - Password
5. Click "Save" to create the user

### Managing User Permissions
User permissions are role-based. To modify permissions:
1. Log in as an administrator
2. Navigate to Admin > Users
3. Edit the user and change their role
4. Save the changes

## 6. System Configuration

### Application Settings
Core application settings are stored in `settings.py`. For production, use environment variables instead of modifying this file directly.

### Email Configuration
To configure email notifications:
1. Update the following settings in your `.env` file:
```
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=inventory@example.com
```

2. Restart the application for changes to take effect

### Customizing the Interface
To customize the application branding:
1. Replace the logo file at `/static/img/logo.png`
2. Modify the CSS variables in `/static/css/style.css`
3. Update the company name in the footer template

## 7. Backup and Recovery

### Regular Backup Strategy
Implement a regular backup strategy:
1. Database backups (daily recommended):
```bash
pg_dump -U inventory_user -d inventory_db -f backup_$(date +%Y%m%d).sql
```

2. Media files backup (weekly recommended):
```bash
tar -czf media_backup_$(date +%Y%m%d).tar.gz /path/to/inventory_system/media/
```

3. Configuration files backup (after changes):
```bash
cp /path/to/inventory_system/.env /path/to/backup/.env
```

### Recovery Procedure
To recover the system:
1. Restore the database:
```bash
psql -U inventory_user -d inventory_db -f backup.sql
```

2. Restore media files:
```bash
tar -xzf media_backup.tar.gz -C /path/to/inventory_system/
```

3. Restore configuration files:
```bash
cp /path/to/backup/.env /path/to/inventory_system/.env
```

## 8. Maintenance

### Regular Maintenance Tasks
1. **Database maintenance** (monthly):
```bash
sudo -u postgres psql -d inventory_db -c "VACUUM ANALYZE;"
```

2. **Log rotation** (configure in `/etc/logrotate.d/`):
```
/path/to/inventory_system/logs/*.log {
    weekly
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

3. **Check for updates** (quarterly):
```bash
pip list --outdated
```

### Upgrading the Application
To upgrade to a new version:
1. Backup the database and configuration
2. Pull the latest code:
```bash
git pull origin main
```
3. Install any new dependencies:
```bash
pip install -r requirements.txt
```
4. Apply database migrations:
```bash
python manage.py migrate
```
5. Collect static files:
```bash
python manage.py collectstatic --noinput
```
6. Restart the application:
```bash
sudo systemctl restart inventory
```

## 9. Security

### Security Best Practices
1. **Keep software updated**:
   - Regularly update Django, Python, and all dependencies
   - Apply security patches promptly

2. **Secure the database**:
   - Use strong passwords
   - Restrict database access to the application server
   - Enable SSL for database connections

3. **Protect sensitive data**:
   - Store secrets in environment variables, not in code
   - Encrypt sensitive data in the database
   - Use HTTPS for all connections

4. **Implement access controls**:
   - Use role-based permissions
   - Enforce strong password policies
   - Implement session timeouts

### SSL Configuration
To secure the application with SSL:
1. Obtain an SSL certificate (e.g., using Let's Encrypt)
2. Configure Nginx:
```
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    
    # Other configurations
    location /static/ {
        alias /path/to/inventory_system/static/;
    }

    location /media/ {
        alias /path/to/inventory_system/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 10. Troubleshooting

### Common Issues and Solutions

#### Application won't start
**Issue**: The application fails to start after deployment
**Solution**:
- Check the application logs: `/path/to/inventory_system/logs/app.log`
- Verify that all dependencies are installed: `pip install -r requirements.txt`
- Ensure the database is accessible: `python manage.py dbshell`
- Check for syntax errors: `python manage.py check`

#### Database connection errors
**Issue**: The application cannot connect to the database
**Solution**:
- Verify database credentials in `.env`
- Check if PostgreSQL is running: `sudo systemctl status postgresql`
- Ensure the database exists: `sudo -u postgres psql -l`
- Check network connectivity: `ping database_host`

#### Static files not loading
**Issue**: CSS, JavaScript, or images are not loading
**Solution**:
- Run `python manage.py collectstatic`
- Check Nginx configuration for static files path
- Verify file permissions: `chmod -R 755 /path/to/static/`
- Clear browser cache

#### Performance issues
**Issue**: The application is slow
**Solution**:
- Check database performance: `EXPLAIN ANALYZE` for slow queries
- Increase Gunicorn workers: `--workers=4`
- Implement caching: Configure Django's cache framework
- Optimize database indexes

### Logging
Application logs are stored in:
- Application logs: `/path/to/inventory_system/logs/app.log`
- Error logs: `/path/to/inventory_system/logs/error.log`
- Access logs: `/var/log/nginx/access.log`

To increase log verbosity, modify the `LOGGING` setting in `settings.py`.

### Getting Support
For additional support:
- Check the project documentation
- Review the issue tracker on GitHub
- Contact the development team at support@example.com
