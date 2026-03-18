# ✅ Fixed API Connection Error - ERR_NAME_NOT_RESOLVED

## Problem
Frontend was trying to reach `http://api:8000` but got error:
```
GET http://api:8000/api/v1/dashboard/overview net::ERR_NAME_NOT_RESOLVED
```

## Root Cause
The hostname `api` only exists inside Docker's internal network. When running locally without Docker, there's no such hostname.

## Solution

### 1. Updated API URL Detection in Frontend
**File:** `frontend/dashboard/app/page.tsx`

```typescript
let apiUrl = process.env.NEXT_PUBLIC_API_URL;

if (!apiUrl) {
  // Default to localhost for local development
  apiUrl = 'http://localhost:8000';
}
```

### 2. Updated docker-compose.yml
**File:** `docker-compose.yml`

```yaml
environment:
  NEXT_PUBLIC_API_URL: http://localhost:8000
  REACT_APP_API_URL: http://localhost:8000
```

## How to Start Services

### Option 1: Local Development (WITHOUT Docker)

```bash
# Terminal 1: Start backend API
cd /Users/ruchi/Projects/neurocommerce-os/backend/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start frontend
cd /Users/ruchi/Projects/neurocommerce-os/frontend/dashboard
npm run dev

# Open browser
open http://localhost:3000
```

### Option 2: Docker Compose (WITH Docker)

```bash
cd /Users/ruchi/Projects/neurocommerce-os

# Start all services
docker-compose up -d

# Or use the make command
make start

# Open browser
open http://localhost:3000
```

## API URL Configuration

| Environment | NEXT_PUBLIC_API_URL | Notes |
|-------------|-------------------|-------|
| **Local Dev** | `http://localhost:8000` | Running services manually |
| **Docker** | `http://localhost:8000` | Containers on same machine |
| **Docker (Internal)** | `http://api:8000` | (Alternative for container-to-container) |
| **Production** | `https://api.yourdomain.com` | Remote API endpoint |

## Current Setup

✅ Frontend: `http://localhost:3000`  
✅ API: `http://localhost:8000`  
✅ Database: `postgresql://localhost:5432`  
✅ Redis: `http://localhost:6379`  
✅ Kafka: `localhost:9092`  

## Checklist Before Starting

- [ ] Python installed (for API)
- [ ] Node.js installed (for frontend)
- [ ] PostgreSQL running (or Docker)
- [ ] Backend requirements installed: `pip install -r backend/api/requirements.txt`
- [ ] Frontend dependencies installed: `npm install`

## Start Backend

```bash
cd backend/api

# Install dependencies (first time)
pip install -r requirements.txt

# Start API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
Uvicorn running on http://0.0.0.0:8000
Press CTRL+C to quit
```

## Start Frontend

```bash
cd frontend/dashboard

# Install dependencies (first time)
npm install

# Start dev server
npm run dev
```

**Expected Output:**
```
▲ Next.js 14.2.35

  ▲ Local:        http://localhost:3000
  ▲ Environments: .env.local
```

## Verify Services

```bash
# Check API is running
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# Check frontend is running
curl http://localhost:3000
# Should return HTML

# Check database
psql -U neurocommerce -d neurocommerce -h localhost
```

## If Still Getting Errors

### Error: `ERR_NAME_NOT_RESOLVED`
- Make sure API is running on port 8000
- Check `NEXT_PUBLIC_API_URL` env variable
- Verify no firewall blocking localhost:8000

### Error: `Connection refused`
- API service not running
- Check port 8000 is not in use: `lsof -i :8000`
- Start API manually in another terminal

### Error: `CORS errors`
- Backend needs to allow frontend origin
- Check API CORS configuration
- Should include `http://localhost:3000`

## Demo Mode Still Works

If backend isn't available, the dashboard shows demo data:
```
Demo mode: Showing sample data. Backend API not yet available.
```

This allows you to see the UI while developing the backend!

## Production Deployment

For production, update the API URL:

```bash
# Set environment variable
export NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# Or in .env.local
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

**API connection fixed! Start both services and open localhost:3000** 🚀
