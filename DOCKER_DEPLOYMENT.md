# 🐳 KABAADWALA™ Docker Deployment Guide

## 🚀 **One-Click Local Deployment**

```bash
./deploy.sh
```

## 🌐 **One-Click VPS Deployment**

```bash
./vps-deploy.sh
```

## 📋 **What's Included**

### **Docker Configuration**
- **Dockerfile**: Python 3.12 slim with SQLite
- **docker-compose.yml**: Single service setup
- **settings_docker.py**: Production-ready settings
- **.dockerignore**: Optimized build context

### **Features**
- ✅ SQLite database (persistent via volume)
- ✅ Auto-migration on startup
- ✅ Auto-superuser creation (admin/admin123)
- ✅ Static files collection
- ✅ Media files persistence
- ✅ Restart policy

### **Default Credentials**
- **Username**: admin
- **Email**: admin@admin.com  
- **Password**: admin123

## 🔧 **Manual Commands**

### **Local Development**
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild
docker-compose build --no-cache
```

### **VPS Deployment**
```bash
# SSH to your VPS
ssh user@your-vps-ip

# Upload files
scp -r . user@your-vps-ip:/tmp/kabaadwala/

# Run deployment
cd /tmp/kabaadwala && ./vps-deploy.sh
```

## 🌍 **Access Your App**

- **Local**: http://localhost:8000
- **VPS**: http://your-vps-ip:8000
- **Admin**: /admin/

## 📁 **File Structure**
```
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Service orchestration
├── settings_docker.py      # Docker-specific settings
├── deploy.sh              # Local deployment script
├── vps-deploy.sh          # VPS deployment script
├── .dockerignore          # Docker build exclusions
└── db.sqlite3            # Persistent database
```

## 🔒 **Security Notes**

- Change default admin password after first login
- Configure firewall on VPS (allow port 8000)
- Use reverse proxy (nginx) for production
- Enable HTTPS with SSL certificate

## 🛠 **Troubleshooting**

### **Container won't start**
```bash
docker-compose logs web
```

### **Database issues**
```bash
docker-compose exec web python manage.py migrate
```

### **Reset everything**
```bash
docker-compose down -v
docker-compose up -d
```

## 📊 **Resource Requirements**

- **RAM**: 512MB minimum
- **Storage**: 2GB minimum  
- **CPU**: 1 core minimum
- **Network**: Port 8000 open
