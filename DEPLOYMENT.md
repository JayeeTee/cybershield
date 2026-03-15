# 🚀 CyberShield Deployment Guide

**Production Deployment Documentation**
**Date:** March 2, 2026

---

## 📋 Prerequisites

- Docker & Docker Compose installed
- Domain name (e.g., cybershield.example.com)
- SSL certificates (Let's Encrypt recommended)
- PostgreSQL 14+ (or use Docker)
- Redis (or use Docker)
- Minimum 4GB RAM, 2 CPU cores

---

## 🏗️ Architecture

```
┌─────────────┐
│   Nginx     │ (HTTPS, Reverse Proxy)
│   Port 443  │
└──────┬──────┘
       │
   ┌───┴────────────────┐
   │                    │
┌──▼──────┐      ┌─────▼───┐
│Frontend │      │ Backend │
│React    │      │FastAPI  │
│Port 80  │      │Port 8000│
└─────────┘      └────┬────┘
                      │
            ┌─────────┴─────────┐
            │                   │
        ┌───▼─────┐      ┌─────▼───┐
        │PostgreSQL│     │  Redis  │
        │Port 5432 │     │Port 6379│
        └──────────┘      └─────────┘
```

---

## 🐳 Docker Deployment

### 1. Clone Repository

\`\`\`bash
git clone https://github.com/JayeeTee/cybershield.git
cd cybershield
\`\`\`

### 2. Configure Environment

\`\`\`bash
# Copy example environment
cp .env.example .env

# Edit .env with your values
nano .env
\`\`\`

**Required Environment Variables:**
\`\`\`env
# Database
DATABASE_URL=postgresql://cybershield:SECURE_PASSWORD@db:5432/cybershield

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET=YOUR_SUPER_SECURE_JWT_SECRET_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
\`\`\`

### 3. SSL Certificates

**Option A: Let's Encrypt (Recommended)**

\`\`\`bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d cybershield.example.com

# Copy to project
sudo cp /etc/letsencrypt/live/cybershield.example.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/cybershield.example.com/privkey.pem ./ssl/key.pem
sudo chown $USER:$USER ./ssl/*.pem
\`\`\`

**Option B: Self-Signed (Development Only)**

\`\`\`bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/CN=localhost"
\`\`\`

### 4. Build & Deploy

\`\`\`bash
# Build all containers
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
\`\`\`

### 5. Initialize Database

\`\`\`bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Create admin user
docker-compose -f docker-compose.prod.yml exec api python scripts/create_admin.py
\`\`\`

---

## 🔧 Manual Deployment (No Docker)

### Backend Setup

\`\`\`bash
# Install Python 3.10+
sudo apt-get install python3.10 python3.10-venv postgresql-client

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
export DATABASE_URL="postgresql://cybershield:password@localhost:5432/cybershield"
export JWT_SECRET="your-secret-key"

# Run migrations
alembic upgrade head

# Start with Gunicorn
gunicorn cybershield.api.app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
\`\`\`

### Frontend Setup

\`\`\`bash
# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install dependencies
cd web/dashboard
npm install

# Build production bundle
npm run build

# Serve with Nginx
sudo cp -r build/* /var/www/cybershield/
\`\`\`

---

## 🌐 Nginx Configuration

\`\`\`nginx
# /etc/nginx/sites-available/cybershield
server {
    listen 443 ssl http2;
    server_name cybershield.example.com;

    ssl_certificate /etc/letsencrypt/live/cybershield.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cybershield.example.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/cybershield;
        try_files $uri /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name cybershield.example.com;
    return 301 https://$server_name$request_uri;
}
\`\`\`

Enable site:
\`\`\`bash
sudo ln -s /etc/nginx/sites-available/cybershield /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
\`\`\`

---

## 🔒 Security Checklist

- ✅ HTTPS enabled with valid SSL certificate
- ✅ JWT secret is strong and unique
- ✅ Database password is secure
- ✅ Firewall configured (UFW or iptables)
- ✅ Rate limiting enabled
- ✅ CORS configured properly
- ✅ Environment variables secured
- ✅ Regular backups scheduled
- ✅ Security headers in Nginx
- ✅ WebSocket authentication

**Firewall Rules:**
\`\`\`bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
\`\`\`

---

## 📊 Monitoring

### Health Check Endpoint

\`\`\`bash
curl https://cybershield.example.com/api/v1/health
\`\`\`

### Docker Logs

\`\`\`bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f frontend
\`\`\`

### Prometheus + Grafana (Optional)

Add to \`docker-compose.prod.yml\`:
\`\`\`yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
\`\`\`

---

## 🔄 Backup Strategy

### Database Backup

\`\`\`bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec db pg_dump cybershield > backup_$(date +%Y%m%d).sql

# Automated backup (cron)
0 2 * * * cd /path/to/cybershield && docker-compose -f docker-compose.prod.yml exec -T db pg_dump cybershield > /backups/cybershield_$(date +\%Y\%m\%d).sql
\`\`\`

### Restore Database

\`\`\`bash
cat backup_20260302.sql | docker-compose -f docker-compose.prod.yml exec -T db psql cybershield
\`\`\`

---

## 🚦 Scaling

### Horizontal Scaling

\`\`\`bash
# Scale API workers
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Use load balancer (HAProxy/Nginx) to distribute traffic
\`\`\`

### Vertical Scaling

Increase resources in \`docker-compose.prod.yml\`:
\`\`\`yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
\`\`\`

---

## 🔧 Maintenance

### Update Application

\`\`\`bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.prod.yml build

# Restart services (zero downtime)
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
\`\`\`

### View Logs

\`\`\`bash
# Real-time logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Save logs to file
docker-compose -f docker-compose.prod.yml logs > logs_$(date +%Y%m%d).txt
\`\`\`

---

## 🆘 Troubleshooting

### Common Issues

**1. Container won't start**
\`\`\`bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check container status
docker-compose -f docker-compose.prod.yml ps

# Restart specific service
docker-compose -f docker-compose.prod.yml restart api
\`\`\`

**2. Database connection failed**
\`\`\`bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps db

# Test connection
docker-compose -f docker-compose.prod.yml exec db psql -U cybershield -d cybershield
\`\`\`

**3. SSL certificate errors**
\`\`\`bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Copy new certificates
sudo cp /etc/letsencrypt/live/cybershield.example.com/*.pem ./ssl/

# Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx
\`\`\`

---

## 📞 Support

- **Documentation:** /docs (FastAPI Swagger UI)
- **Health Check:** /api/v1/health
- **Logs:** /var/log/cybershield/
- **GitHub Issues:** https://github.com/JayeeTee/cybershield/issues

---

## ✅ Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database initialized
- [ ] Migrations run
- [ ] Admin user created
- [ ] Firewall configured
- [ ] Backups scheduled
- [ ] Monitoring enabled
- [ ] Health check passing
- [ ] All tests passing

---

**Deployment Complete!** 🎉

Access your CyberShield instance at: https://cybershield.example.com
