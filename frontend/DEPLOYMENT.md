# Frontend Deployment Guide

Complete guide for deploying the Assembly Time-Tracking Dashboard to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Nginx Configuration](#nginx-configuration)
6. [SSL/HTTPS Setup](#sslhttps-setup)
7. [Performance Optimization](#performance-optimization)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **Docker**: 20.x or higher (for containerized deployment)
- **Nginx**: 1.20.x or higher (for manual deployment)
- **Operating System**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+

### Backend Requirements

- Backend API must be running and accessible
- WebSocket endpoint must be available
- CORS configured to allow frontend domain

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd Assembly-Time-Tracking-Workflow/frontend
```

### 2. Configure Environment Variables

Create production environment file:

```bash
cp .env.production.example .env.production
```

Edit `.env.production`:

```bash
# Production API endpoints
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com

# App configuration
VITE_APP_NAME=Assembly Time Tracking Dashboard
VITE_APP_VERSION=1.0.0
VITE_APP_ENV=production

# Feature flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_REPORTS=true
VITE_ENABLE_FORECASTING=true
```

**Important**: Never commit `.env.production` to version control!

## Docker Deployment

### Option 1: Standalone Container

#### Build Image

```bash
docker build -t assembly-tracking-frontend:latest .
```

#### Run Container

```bash
docker run -d \
  --name assembly-frontend \
  --restart unless-stopped \
  -p 80:80 \
  assembly-tracking-frontend:latest
```

#### Verify Deployment

```bash
# Check container status
docker ps

# Check logs
docker logs assembly-frontend

# Test health endpoint
curl http://localhost/health
```

### Option 2: Docker Compose (Recommended)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: assembly-frontend
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - assembly-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s

  backend:
    # Your backend configuration
    container_name: assembly-backend
    ports:
      - "8000:8000"
    networks:
      - assembly-network

networks:
  assembly-network:
    driver: bridge
```

Deploy with Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## Manual Deployment

### 1. Install Dependencies

```bash
npm ci --only=production
```

### 2. Build for Production

```bash
# Create production build
npm run build

# Output will be in dist/ directory
ls -la dist/
```

### 3. Deploy Build Files

#### Option A: Local Server

```bash
# Copy to web server directory
sudo cp -r dist/* /var/www/html/assembly-tracking/
sudo chown -R www-data:www-data /var/www/html/assembly-tracking/
```

#### Option B: Remote Server

```bash
# Using rsync
rsync -avz --delete dist/ user@yourserver.com:/var/www/html/assembly-tracking/

# Using scp
scp -r dist/* user@yourserver.com:/var/www/html/assembly-tracking/
```

## Nginx Configuration

### 1. Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/assembly-tracking
```

Copy contents from `nginx.conf` or use this template:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    root /var/www/html/assembly-tracking;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/xml+rss
               application/json application/javascript;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api {
        proxy_pass http://backend-server:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://backend-server:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 2. Enable Site

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/assembly-tracking /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
# Install certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

Certbot will automatically update your nginx config to use HTTPS.

### Manual SSL Certificate

If using a custom certificate:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

## Performance Optimization

### Build Optimizations

The production build automatically includes:

1. **Code Splitting**: Automatic route-based splitting
2. **Tree Shaking**: Removes unused code
3. **Minification**: JavaScript and CSS minification
4. **Asset Optimization**: Image and font optimization
5. **Content Hashing**: For cache busting

### Nginx Optimizations

Add to nginx config:

```nginx
# Enable HTTP/2
listen 443 ssl http2;

# Increase worker connections
events {
    worker_connections 2048;
}

# Enable caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    # ... other proxy settings
}
```

### CDN Configuration (Optional)

For global performance, use a CDN:

```bash
# Upload dist/assets/* to CDN
# Update VITE_CDN_URL in .env.production
VITE_CDN_URL=https://cdn.yourdomain.com
```

## Monitoring

### Health Checks

```bash
# HTTP health check
curl http://yourdomain.com/health

# Expected response: "healthy"
```

### Docker Monitoring

```bash
# Container stats
docker stats assembly-frontend

# Container logs
docker logs -f assembly-frontend --tail 100

# Health status
docker inspect assembly-frontend | grep -A 5 Health
```

### Application Monitoring

Add monitoring tools:

1. **Sentry** - Error tracking
2. **Google Analytics** - User analytics
3. **New Relic** - Performance monitoring
4. **Prometheus + Grafana** - Metrics

### Log Files

```bash
# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f frontend
```

## Troubleshooting

### Common Issues

#### 1. White Screen / Blank Page

**Cause**: Incorrect base URL or missing assets

**Solution**:
```bash
# Check vite.config.ts base setting
# Verify VITE_API_URL is correct
# Check nginx root path
# View browser console for errors
```

#### 2. API Connection Failed

**Cause**: CORS or proxy misconfiguration

**Solution**:
```bash
# Check nginx proxy_pass URL
# Verify backend is accessible
# Check CORS headers in backend
# Test API endpoint directly: curl https://api.yourdomain.com/api/v1/workers
```

#### 3. WebSocket Not Connecting

**Cause**: WebSocket proxy not configured

**Solution**:
```nginx
# Ensure nginx has WebSocket proxy config
location /ws {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

#### 4. 404 on Routes

**Cause**: SPA fallback not configured

**Solution**:
```nginx
# Add to nginx config
location / {
    try_files $uri $uri/ /index.html;
}
```

#### 5. Docker Build Fails

**Cause**: Missing dependencies or network issues

**Solution**:
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t assembly-tracking-frontend .

# Check .dockerignore
cat .dockerignore
```

### Performance Issues

#### Slow Initial Load

```bash
# Check bundle size
npm run build -- --report

# Analyze with webpack-bundle-analyzer
# Consider code splitting
```

#### High Memory Usage

```bash
# Check Docker memory limits
docker stats assembly-frontend

# Increase memory limit in docker-compose.yml
services:
  frontend:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Rollback Procedure

If deployment fails:

### Docker Rollback

```bash
# List images
docker images

# Run previous version
docker run -d --name assembly-frontend assembly-tracking-frontend:v1.0.0

# Or use docker-compose
docker-compose down
docker-compose up -d assembly-tracking-frontend:v1.0.0
```

### Manual Rollback

```bash
# Keep backup of previous build
cp -r /var/www/html/assembly-tracking /var/www/html/assembly-tracking.backup

# Restore backup
rm -rf /var/www/html/assembly-tracking
mv /var/www/html/assembly-tracking.backup /var/www/html/assembly-tracking
sudo systemctl reload nginx
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build Docker image
        run: docker build -t assembly-tracking-frontend:latest ./frontend

      - name: Push to registry
        run: docker push assembly-tracking-frontend:latest

      - name: Deploy to server
        run: |
          ssh user@server "docker pull assembly-tracking-frontend:latest"
          ssh user@server "docker-compose up -d"
```

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] Security headers configured in nginx
- [ ] Environment variables not exposed to client
- [ ] API proxy configured (no direct CORS)
- [ ] WebSocket over TLS (WSS)
- [ ] Docker containers run as non-root user
- [ ] Regular security updates applied
- [ ] Secrets not committed to repository
- [ ] Rate limiting configured in nginx
- [ ] Firewall rules configured

## Support

For issues or questions:
- Check application logs
- Review nginx error logs
- Verify backend connectivity
- Contact system administrator
