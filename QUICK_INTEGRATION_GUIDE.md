# Quick Integration Guide - SaaS One-Click Setup

**⏱️ Time to integrate: 15-30 minutes**

---

## Step 1: Add Setup Router to Backend (2 min)

Edit `backend/api/main.py`:

```python
# Add this import at the top with other routers
from .routers import auth, events, agents, shopify, campaigns, experiments, billing, setup

# Find this section where routers are included:
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(agents.router)
app.include_router(shopify.router)
app.include_router(campaigns.router)
app.include_router(experiments.router)
app.include_router(billing.router)

# Add this line:
app.include_router(setup.router)
```

**Save and restart API**

---

## Step 2: Create Frontend Setup Route (3 min)

Create `frontend/dashboard/src/pages/Setup.tsx`:

```typescript
import React from 'react';
import SetupWizard from '../components/SetupWizard';

export default function SetupPage() {
  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <SetupWizard />
    </div>
  );
}
```

Add route in your routing config (e.g., `src/App.tsx` or router setup):

```typescript
import Setup from './pages/Setup';

// Add to routes:
{ path: '/setup', component: Setup }
// or with React Router v6:
<Route path="/setup" element={<Setup />} />
```

**Test:** Open `http://localhost:3000/setup?store_id=test_store`

---

## Step 3: Configure Environment Variables (2 min)

Update `.env` file:

```bash
# Shopify OAuth
SHOPIFY_API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
SHOPIFY_API_VERSION=2024-01

# JWT for setup tokens
JWT_SECRET=your_jwt_secret_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/neurocommerce

# API Configuration
API_HOST=https://neurocommerce.example.com
OAUTH_REDIRECT_URI=https://neurocommerce.example.com/api/setup/oauth/callback
```

---

## Step 4: Update Shopify App Config (2 min)

The `shopify.app.toml` is already created. Update it with your domain:

```toml
redirect_uris = [
  "https://YOUR_DOMAIN.com/api/setup/oauth/callback"
]

# Update these URLs:
privacy_url = "https://YOUR_DOMAIN.com/privacy"
support_url = "https://YOUR_DOMAIN.com/support"
homepage_url = "https://YOUR_DOMAIN.com"
```

---

## Step 5: Database Setup (2 min)

Ensure Store model has these fields (should already exist):

```python
# In backend/models/models.py
class Store(Base):
    __tablename__ = "stores"
    
    id = Column(String, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    shopify_access_token = Column(String, nullable=False)
    shopify_store_id = Column(String, unique=True, nullable=False)
    
    # These should be added if not present:
    enabled_agents = Column(JSON, default=[])  # NEW
    settings = Column(JSON, default={})  # NEW
    subscription_status = Column(String, default="active")  # NEW
```

If you need to add columns, create a migration:

```bash
# Using Alembic
alembic revision --autogenerate -m "Add setup fields to Store"
alembic upgrade head

# Or manually:
# ALTER TABLE stores ADD COLUMN enabled_agents JSONB DEFAULT '[]';
# ALTER TABLE stores ADD COLUMN settings JSONB DEFAULT '{}';
# ALTER TABLE stores ADD COLUMN subscription_status VARCHAR DEFAULT 'active';
```

---

## Step 6: Test the Setup Flow (5-10 min)

### Test 1: Start Backend
```bash
# In project root
make start
# or
docker-compose up -d

# Wait for services to be ready
sleep 10

# Check API is running
curl http://localhost:8000/health
```

### Test 2: Start Frontend
```bash
cd frontend/dashboard
npm start  # Opens http://localhost:3000
```

### Test 3: Simulate OAuth Callback
```bash
# Manually create a test store entry first (in database)
# or just visit the setup page with a test store_id

open http://localhost:3000/setup?store_id=test_123&shop=teststore.myshopify.com
```

### Test 4: Fill Out Wizard
- Step 1: Enter account info (email, password, name)
- Step 2: Enter store config (industry, audience, etc.)
- Step 3: Select agents
- Step 4: Click "Activate"

### Test 5: Verify Database
```bash
make db-shell
# Run these SQL commands:
SELECT * FROM users;
SELECT * FROM stores;
SELECT * FROM api_keys;
```

---

## Step 7: Deploy to Production (5 min)

### Build Frontend
```bash
cd frontend/dashboard
npm run build
# Creates build/ folder
```

### Deploy Anywhere

**Option A: Docker**
```bash
docker-compose -f docker-compose.yml up -d
```

**Option B: Heroku**
```bash
heroku create neurocommerce-prod
git push heroku main
heroku config:set SHOPIFY_API_KEY=...
heroku config:set SHOPIFY_API_SECRET=...
```

**Option C: AWS/GCP/Azure**
Follow your cloud provider's deployment guide with the `.env` variables

---

## Step 8: Enable HTTPS (Required for Production)

### Local Testing with HTTPS
```bash
# Create self-signed cert
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update docker-compose or Nginx config to use HTTPS
```

### Production
- Use Let's Encrypt (free)
- Or AWS Certificate Manager
- Or Cloudflare (easiest)

---

## Step 9: Test Full OAuth Flow

### In Shopify Partner Dashboard

1. Go to your app settings
2. Set OAuth redirect URI: `https://YOUR_DOMAIN.com/api/setup/oauth/callback`
3. Copy API Key and API Secret
4. Add to `.env` as `SHOPIFY_API_KEY` and `SHOPIFY_API_SECRET`

### Test OAuth
```bash
# Build OAuth URL (in Shopify Partner Dashboard)
https://YOUR_STORE.myshopify.com/admin/oauth/authorize?client_id=YOUR_API_KEY&scope=write_products,read_products,...&redirect_uri=https://YOUR_DOMAIN.com/api/setup/oauth/callback&state=random_state

# Then your backend receives the callback
# And redirects customer to setup wizard
```

---

## Troubleshooting

### "TypeError: Cannot read property 'storeId' of null"
- SetupWizard not getting store_id from URL
- Fix: Make sure URL has `?store_id=...` parameter

### "Failed to get access token from Shopify"
- SHOPIFY_API_KEY or SHOPIFY_API_SECRET not set
- Fix: Update `.env` with correct credentials

### "404 Not Found" on `/api/setup/account`
- Setup router not included in main.py
- Fix: Add `app.include_router(setup.router)` to main.py and restart

### "CORS Error"
- Frontend making requests to wrong domain
- Fix: Check CORS configuration in main.py matches your domain

### "Database connection failed"
- DATABASE_URL not set or PostgreSQL not running
- Fix: `make start` to start all services, or set DATABASE_URL in .env

---

## Files Checklist

- [x] `shopify.app.toml` - Created ✅
- [x] `backend/api/routers/setup.py` - Created ✅  
- [x] `frontend/dashboard/src/components/SetupWizard.tsx` - Created ✅
- [x] `frontend/dashboard/src/components/SetupWizard.css` - Created ✅
- [ ] `backend/api/main.py` - NEED TO INTEGRATE (add import + router)
- [ ] `frontend/dashboard/src/pages/Setup.tsx` - NEED TO CREATE
- [ ] `.env` - NEED TO UPDATE with credentials
- [ ] Database migrations - NEED TO RUN (if adding new columns)

---

## Verification Checklist

- [ ] Backend running: `http://localhost:8000/health` returns 200
- [ ] Frontend running: `http://localhost:3000` loads
- [ ] Setup page loads: `http://localhost:3000/setup?store_id=test`
- [ ] Can fill out wizard (all 4 steps)
- [ ] Database created user/store/api_key
- [ ] GET `/api/setup/status/store_id` returns correct step
- [ ] .env has all required variables
- [ ] HTTPS enabled (for production)

---

## Next Steps

1. **Complete the 9 steps above** (should take 15-30 min)
2. **Test the full setup flow locally**
3. **Deploy to production**
4. **Submit to Shopify App Store** when ready
5. **Monitor setup completion rates** and fix any issues

---

## Command Reference

```bash
# Start everything
make start

# Check services
docker-compose ps

# View logs
make logs

# Connect to database
make db-shell

# Rebuild frontend
cd frontend/dashboard && npm run build

# Run tests (once created)
make test

# Deploy to Heroku
git push heroku main

# View production logs
heroku logs --tail
```

---

## Support

If you hit issues:

1. Check logs: `docker logs neurocommerce_api`
2. Check frontend console: Open DevTools (F12) → Console tab
3. Review guide: Read `SAAS_ONECLICK_SETUP.md` for more details
4. Check env vars: `cat .env | grep SHOPIFY`

---

## Success!

Once integrated and deployed, you'll have:

✅ Customers can install from Shopify App Store  
✅ One-click setup in 5 minutes  
✅ AI agents live on their store  
✅ Zero manual configuration  

Ready to launch! 🚀
