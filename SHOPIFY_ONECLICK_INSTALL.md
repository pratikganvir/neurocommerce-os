# NeuroCommerce Shopify App - ONE-CLICK SETUP GUIDE

**Installation Time: 5 minutes | No manual configuration needed**

This guide walks you through the complete one-click installation and setup of NeuroCommerce with Shopify integration.

---

## 🚀 Quick Start (TL;DR)

### Option 1: Python Setup (Recommended)
```bash
python3 setup_shopify.py
```

### Option 2: Bash Setup
```bash
bash install.sh
```

### Option 3: Make (Simplest)
```bash
make install
```

Then follow the on-screen prompts. That's it! ✨

---

## 📋 Prerequisites

- **Docker Desktop** (includes Docker + Docker Compose)
  - Download: https://www.docker.com/products/docker-desktop
  - Windows: Requires WSL 2
  - Mac: Apple Silicon or Intel
  - Linux: Docker Engine + Docker Compose
  
- **Shopify Account** (Free!)
  - Go to: https://partners.shopify.com
  - Create account or sign in
  - No credit card needed for dev store

- **5 minutes** of your time

---

## 🎯 Installation Steps

### Step 1: Start Installation

Choose one method:

**Method A: Python (Recommended - Most user-friendly)**
```bash
cd /path/to/neurocommerce-os
python3 setup_shopify.py
```

**Method B: Bash (Simple shell script)**
```bash
cd /path/to/neurocommerce-os
bash install.sh
```

**Method C: Make (Quickest)**
```bash
cd /path/to/neurocommerce-os
make install
```

**Method D: Non-interactive (For CI/CD)**
```bash
python3 setup_shopify.py --non-interactive
```

### Step 2: Answer Setup Questions

The installer will ask for:

1. **Shopify API Key**
   - Get from: Partners Dashboard → Your App → Configuration → API credentials
   - Copy the "Admin API access token" value

2. **Shopify API Secret**
   - Get from: Same place as API Key
   - Copy the "API secret key" value

3. **App Name** (optional, defaults to "NeuroCommerce")
   - Name for your app in Shopify

4. **App URL** (optional, defaults to http://localhost:8000)
   - Where your app is hosted
   - Use http://localhost:8000 for local development
   - Use https://yourdomain.com for production

5. **Database Password** (optional, defaults to "password")
   - For local development, the default is fine
   - Change for production

### Step 3: Automatic Setup

The installer will automatically:

✅ Verify Docker installation  
✅ Create `.env` configuration file  
✅ Generate security keys (JWT secret)  
✅ Start Docker containers (PostgreSQL, Redis, Kafka, ClickHouse)  
✅ Wait for services to be ready  
✅ Initialize database  
✅ Display completion summary  

### Step 4: Configure Shopify (5 minutes)

After installation completes, you need to:

**A. Add OAuth Redirect URI**
1. Go to: https://partners.shopify.com
2. Select your app
3. Go to "Configuration" tab
4. Find "Redirect URIs" section
5. Add: `http://localhost:8000/shopify/oauth/callback`
6. Save

**B. Add Webhooks**
1. In same app, go to "Webhooks" tab
2. Click "Add webhook"
3. Create three webhooks:

| Event | URL |
|-------|-----|
| checkout/create | `http://localhost:8000/shopify/webhooks/checkout/create` |
| checkout/update | `http://localhost:8000/shopify/webhooks/checkout/update` |
| orders/create | `http://localhost:8000/shopify/webhooks/orders/create` |

---

## ✅ Verify Installation

After setup completes, verify everything is working:

### Check Services
```bash
# View service status
docker-compose ps

# Should show: postgres, redis, kafka, clickhouse, api - all "Up"
```

### Check API Health
```bash
# Quick health check
curl http://localhost:8000/health

# Should return: {"status": "ok"}
```

### View API Documentation
```bash
# Open browser to:
http://localhost:8000/docs

# You'll see full API documentation and can test endpoints
```

### View Logs
```bash
# Real-time API logs
make logs

# All service logs
docker-compose logs -f

# Exit logs: Ctrl+C
```

---

## 🛠️ Common Issues & Solutions

### Issue: "Docker is not installed"
**Solution:**
```bash
# Download from https://www.docker.com/products/docker-desktop
# Then run:
docker --version  # Should print version
```

### Issue: "Docker daemon is not running"
**Solution:**
- Open Docker Desktop application
- Wait for it to fully start
- Try again

### Issue: Port 8000 already in use
**Solution:**
```bash
# Find and stop the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change the port in docker-compose.yml
# Find: ports: - "8000:8000"
# Change to: ports: - "8001:8000"
```

### Issue: Database connection failed
**Solution:**
```bash
# Wait for PostgreSQL to be ready
docker-compose logs postgres

# Or restart PostgreSQL
docker-compose restart postgres
```

### Issue: Permission denied on install.sh
**Solution:**
```bash
chmod +x install.sh
bash install.sh
```

### Issue: Shopify webhooks not triggering
**Solution:**
1. Verify webhook URLs are correct (check Shopify app settings)
2. Check API is running: `curl http://localhost:8000/health`
3. View logs: `make logs`
4. Verify `.env` has correct API keys

---

## 📁 What Gets Installed

```
neurocommerce-os/
├── .env                    # ✅ Configuration (auto-created)
├── docker-compose.yml      # Services definition
├── setup_shopify.py        # Interactive setup script
├── install.sh              # Bash setup script
├── Makefile                # Make shortcuts
│
├── backend/
│   ├── api/
│   │   └── routers/
│   │       └── shopify.py  # ✅ Shopify webhooks & OAuth
│   │
│   ├── services/
│   │   └── shopify_service.py  # ✅ Shopify API client
│   │
│   ├── models/
│   │   └── models.py       # ✅ Store, Customer, Order models
│   │
│   ├── database.py         # ✅ Database connection
│   └── main.py             # ✅ API server
│
├── docker/
│   └── docker-compose.yml  # All services definition
│
└── docker-compose.yml      # Root compose file

🐳 Docker Containers Started:
  • postgres:15        → PostgreSQL database
  • redis:7            → Cache & sessions
  • kafka:latest       → Event streaming
  • clickhouse:latest  → Analytics database
  • api:latest         → Python FastAPI server
```

---

## 🔧 Managing Services

### Start Services
```bash
make start
# or
docker-compose up -d
```

### Stop Services
```bash
make stop
# or
docker-compose down
```

### Restart Services
```bash
make restart
# or
docker-compose restart
```

### View Logs
```bash
make logs         # API logs only
make logs-all     # All services
```

### Connect to Database
```bash
make db-shell
# or
docker-compose exec postgres psql -U neurocommerce neurocommerce
```

### Reset Everything
```bash
make clean-hard   # Remove all containers and data
```

---

## 🌐 Production Deployment

### For Production Setup:
```bash
python3 setup_shopify.py --env-file .env.production
```

### Production Checklist:
- [ ] Change `ENVIRONMENT=production` in `.env`
- [ ] Change `APP_URL` from localhost to your domain
- [ ] Generate new `JWT_SECRET_KEY`: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Update database URL with production credentials
- [ ] Use HTTPS for all URLs (not http://)
- [ ] Add domain to Shopify app settings
- [ ] Update webhook URLs to use production domain
- [ ] Set `SHOPIFY_SCOPES` based on what you need
- [ ] Never commit `.env` file to git (it's in `.gitignore`)
- [ ] Store secrets in environment variables or secure vault

### Deploy to Production:
```bash
# On your production server:
git clone https://github.com/your-org/neurocommerce-os.git
cd neurocommerce-os
python3 setup_shopify.py --env-file .env.production
# Follow production checklist above
docker-compose -f docker-compose.yml up -d
```

---

## 📚 Next Steps

### 1. Test the API
```bash
# View interactive documentation
open http://localhost:8000/docs

# Or test with curl
curl -X GET http://localhost:8000/health
```

### 2. Create Test Store
```bash
curl -X POST http://localhost:8000/api/stores \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Test Store",
    "domain": "test-store.myshopify.com",
    "plan": "starter"
  }'
```

### 3. Explore Endpoints

Available endpoints (after installation):
- `POST /shopify/oauth/callback` - OAuth callback
- `POST /shopify/webhooks/checkout/create` - Checkout created
- `POST /shopify/webhooks/checkout/update` - Checkout updated
- `POST /shopify/webhooks/orders/create` - Order created
- `GET /api/stores` - List stores
- `GET /api/customers` - List customers
- `GET /api/orders` - List orders
- And many more...

### 4. Read Documentation
- API Docs: http://localhost:8000/docs
- Project README: `README.md`
- Shopify Integration: `docs/SHOPIFY_INTEGRATION.md`

---

## 🆘 Get Help

### View Help
```bash
# Show all available commands
make help

# Shopify-specific help
make shopify-help
```

### Check Status
```bash
# Validate entire setup
make validate
```

### View Logs
```bash
# Real-time logs
make logs

# All services
make logs-all
```

### Documentation
- Full documentation: See `docs/` folder
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- API Reference: http://localhost:8000/docs (when running)

---

## 🎉 You're Done!

Your NeuroCommerce Shopify app is now:

✅ Installed  
✅ Configured  
✅ Running  
✅ Connected to Shopify  

### What's Next?
1. Build your business logic using the agents
2. Configure customer segments
3. Set up campaigns and experiments
4. Monitor analytics and conversions
5. Optimize with machine learning

---

## 📝 Files Modified by Installer

```
.env                    - CREATED (auto-generated)
docker-compose.yml      - UNCHANGED
setup_shopify.py        - UNCHANGED
install.sh              - UNCHANGED
Makefile                - UNCHANGED

All your code stays safe!
```

---

## 🔐 Security Notes

- `.env` is in `.gitignore` - never committed to git
- API keys are stored only in `.env` on your machine
- JWT secret is auto-generated and unique
- All passwords should be changed in production
- Use HTTPS for production (not http://)
- Keep Docker images updated: `docker-compose pull`

---

## 📞 Support

- **Issues?** Check `make validate`
- **Logs?** Run `make logs`
- **Documentation?** See `README.md` and `docs/`
- **Questions?** Check the troubleshooting guide

---

**Happy selling! 🚀**

*Last Updated: 2024-01*
