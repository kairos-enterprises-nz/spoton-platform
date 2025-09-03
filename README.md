# 🚀 SpotOn Platform

**Power • Broadband • Mobile Services**

A comprehensive platform for managing electricity, broadband, and mobile services in New Zealand.

---

## 🏗️ Architecture

### Applications
- **🔧 API** - Django REST API backend
- **🌐 Web** - Marketing website (React)
- **👥 Portal-Web** - Customer portal (React)
- **👨‍💼 Staff-Web** - Staff management portal (React)

### Environments
- **Development** - Local development environment
- **UAT** - User Acceptance Testing (`uat.spoton.co.nz`)
- **Live** - Production environment (`spoton.co.nz`)

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Development Setup
```bash
# Clone repository
git clone https://git.spoton.co.nz/arun-kumar/spoton-platform.git
cd spoton-platform

# Start development environment
docker-compose up -d

# Run migrations
./scripts/migrate_environment.sh uat --backup
```

### Production Deployment
```bash
# Deploy to UAT
git checkout uat
git merge feature/your-feature
git push origin uat
# → Automatic UAT deployment

# Deploy to Live
git checkout main
git merge uat
git push origin main
# → Automatic Live deployment
```

---

## 🔄 CI/CD Workflow

### Branch Strategy
```
main (production) ← uat (staging) ← feature/your-feature
```

### Development Process
1. Create feature branch from `uat`
2. Develop and test locally
3. Push and create pull request
4. Merge to `uat` for testing
5. After approval, merge to `main` for production

### Automated Pipeline
- **Tests** run on all branches
- **UAT deployment** on push to `uat` branch
- **Live deployment** on push to `main` branch

---

## 📁 Project Structure

```
spoton-platform/
├── apps/
│   ├── api/           # Django REST API
│   ├── web/           # Marketing website
│   ├── portal-web/    # Customer portal
│   └── staff-web/     # Staff portal
├── scripts/           # Deployment & management scripts
├── docs/             # Documentation
├── .gitea/           # CI/CD workflows
├── docker-compose.uat.yml    # UAT environment
├── docker-compose.live.yml   # Live environment
└── README.md
```

---

## 🛠️ Development

### API (Django)
```bash
cd apps/api
python manage.py runserver
```

### Frontend Applications
```bash
cd apps/web          # or portal-web, staff-web
npm install
npm run dev
```

### Database Management
```bash
# Run migrations
./scripts/migrate_environment.sh uat

# Backup database
./scripts/backup_database.sh live

# Health check
./scripts/health_check.sh uat --detailed
```

---

## 🔧 Scripts Reference

| Script | Purpose |
|--------|---------|
| `migrate_environment.sh` | Run database migrations safely |
| `deploy_environment.sh` | Deploy to UAT or Live |
| `backup_database.sh` | Create database backups |
| `restore_database.sh` | Restore from backup |
| `health_check.sh` | System health monitoring |
| `rollback.sh` | Emergency rollback procedures |

---

## 🌐 Environments

### UAT (Testing)
- **Web**: https://uat.spoton.co.nz
- **API**: https://uat.api.spoton.co.nz
- **Portal**: https://uat.portal.spoton.co.nz
- **Staff**: https://uat.staff.spoton.co.nz

### Live (Production)
- **Web**: https://spoton.co.nz
- **API**: https://api.spoton.co.nz
- **Portal**: https://portal.spoton.co.nz
- **Staff**: https://staff.spoton.co.nz

---

## 📚 Documentation

- [CI/CD Framework Plan](./docs/CICD_FRAMEWORK_PLAN.md)
- [Developer Guide](./docs/DEVELOPER_GUIDE.md)
- [Branching Strategy](./docs/BRANCHING_STRATEGY.md)
- [Architecture Documentation](./docs/ARCHITECTURE_MIGRATION_PLAN.md)

---

## 🔒 Security

- HTTPS everywhere via Caddy
- Keycloak OIDC authentication
- Environment-specific secrets
- Database encryption at rest
- Regular security updates

---

## 📊 Monitoring

- **Grafana**: https://grafana.spoton.co.nz
- **Health Checks**: Automated monitoring
- **Alerts**: Email/Slack notifications
- **Logs**: Centralized logging system

---

## 🤝 Contributing

1. Create feature branch from `uat`
2. Follow [Conventional Commits](https://www.conventionalcommits.org/)
3. Test locally and in UAT
4. Create pull request with clear description
5. Ensure all CI checks pass

---

## 📄 License

Proprietary - SpotOn Platform © 2025

---

**Built with ❤️ for New Zealand's energy future**