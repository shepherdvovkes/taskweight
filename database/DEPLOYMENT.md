# TaskWeight Database Deployment Guide

## Prerequisites

### System Requirements
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB free disk space
- Linux/macOS/Windows with Docker support

### Network Requirements
- Ports 5432, 6379, 8080 available
- Internet access for Docker images
- Firewall configured for database access

## Deployment Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd taskweight/database
```

### 2. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

**Required Variables:**
```bash
POSTGRES_DB=taskweight
POSTGRES_USER=taskweight_user
POSTGRES_PASSWORD=<strong_password>
POSTGRES_PORT=5432

PGADMIN_EMAIL=admin@yourdomain.com
PGADMIN_PASSWORD=<strong_password>

REDIS_PASSWORD=<strong_password>
```

### 3. Start Database Services
```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 4. Run Database Initialization
```bash
# Wait for PostgreSQL to be ready (check health check)
docker-compose logs postgres

# Run migrations
./scripts/migrate.sh

# Or with sample data for development
LOAD_SAMPLE_DATA=true ./scripts/migrate.sh
```

### 5. Verify Deployment
```bash
# Check database connection
./scripts/health-check.sh

# Access PgAdmin
# Open http://localhost:8080 in browser
# Login with credentials from .env
```

## Production Deployment

### 1. Security Hardening
```bash
# Generate strong passwords
openssl rand -base64 32

# Use environment-specific .env files
cp .env .env.production
nano .env.production
```

### 2. SSL Configuration
```bash
# Add SSL certificates to postgres/conf/
# Update postgresql.conf for SSL
# Update docker-compose.yml for SSL volumes
```

### 3. Backup Configuration
```bash
# Configure automatic backups
crontab -e

# Add backup schedule
0 2 * * * /path/to/taskweight/database/scripts/backup.sh
```

### 4. Monitoring Setup
```bash
# Start monitoring stack
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Configure alerts in Prometheus
# Setup Grafana dashboards
```

## Scaling

### 1. Database Replication
```bash
# Add read replicas
# Update docker-compose.yml
# Configure connection pooling
```

### 2. Redis Cluster
```bash
# Setup Redis Sentinel
# Configure Redis Cluster
# Update application configuration
```

## Maintenance

### 1. Regular Tasks
```bash
# Daily health checks
./scripts/health-check.sh

# Weekly backups
./scripts/backup.sh

# Monthly log rotation
docker system prune -f
```

### 2. Updates
```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Run migrations if needed
./scripts/migrate.sh
```

### 3. Troubleshooting
```bash
# Check logs
docker-compose logs -f postgres

# Restart services
docker-compose restart postgres

# Access database directly
docker exec -it taskweight_postgres psql -U taskweight_user -d taskweight
```

## Backup & Recovery

### 1. Backup Strategy
- **Full backup**: Daily at 2:00 AM
- **Incremental**: Every 4 hours
- **Retention**: 30 days
- **Storage**: Local + remote (S3/Backblaze)

### 2. Recovery Procedures
```bash
# Stop application
docker-compose down

# Restore from backup
./scripts/restore.sh backup_20240101_120000.sql

# Start services
docker-compose up -d

# Verify data integrity
./scripts/health-check.sh
```

## Monitoring & Alerting

### 1. Key Metrics
- Database connections
- Query performance
- Disk usage
- Memory usage
- Backup status

### 2. Alert Rules
```yaml
# Prometheus alert rules
groups:
  - name: database_alerts
    rules:
      - alert: HighConnectionCount
        expr: pg_stat_database_numbackends > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connection count"
```

## Security Checklist

- [ ] Strong passwords for all services
- [ ] Network isolation with Docker networks
- [ ] SSL/TLS encryption enabled
- [ ] Regular security updates
- [ ] Access logging enabled
- [ ] Backup encryption
- [ ] Firewall rules configured
- [ ] User access limited to necessary accounts

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :5432

# Change port in .env
POSTGRES_PORT=5433
```

#### 2. Permission Denied
```bash
# Fix script permissions
chmod +x scripts/*.sh

# Check Docker user permissions
sudo usermod -aG docker $USER
```

#### 3. Database Connection Failed
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs postgres

# Verify environment variables
docker-compose config
```

#### 4. Migration Errors
```bash
# Check database connection
./scripts/health-check.sh

# Verify SQL syntax
docker exec -it taskweight_postgres psql -U taskweight_user -d taskweight -f /docker-entrypoint-initdb.d/01-init-database.sql
```

## Support

### Documentation
- [Database Schema](DATABASE_SCHEMA.md)
- [README](README.md)
- [Docker Compose Reference](https://docs.docker.com/compose/)

### Logs Location
- PostgreSQL: `docker-compose logs postgres`
- Redis: `docker-compose logs redis`
- PgAdmin: `docker-compose logs pgadmin`

### Contact
For database issues, check logs first and refer to troubleshooting section above.
