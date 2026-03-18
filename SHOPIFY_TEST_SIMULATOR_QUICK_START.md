# 🎭 Shopify Test Simulator - Quick Start

**All 5 test scripts are now ready to use!**

## 📍 Scripts Created

```
scripts/
├── shopify_mock_server.py          # Mock Shopify server (port 8001)
├── test_oauth_flow.py               # Test complete OAuth flow
├── test_webhooks.py                 # Test webhook delivery
├── test_shopify_simulator.py         # Run all tests end-to-end
└── generate_test_data.py             # Generate random test data
```

## 🚀 Usage

### 1. Start Everything

```bash
# Start all services (API, Frontend, Database)
make start

# In another terminal: Start mock Shopify server
python3 scripts/shopify_mock_server.py
```

### 2. Run Tests

```bash
# Option A: Run complete test suite
python3 scripts/test_shopify_simulator.py

# Option B: Test individual components
python3 scripts/test_oauth_flow.py
python3 scripts/test_webhooks.py
python3 scripts/generate_test_data.py
```

## 🎯 What Each Script Does

### `shopify_mock_server.py` (Port 8001)
Simulates Shopify with:
- ✅ OAuth authorization & token exchange
- ✅ Admin API endpoints (shop, products, customers, orders)
- ✅ Webhook subscription management
- **No real Shopify credentials needed!**

**Start it:**
```bash
python3 scripts/shopify_mock_server.py
```

### `test_oauth_flow.py`
Tests complete OAuth installation flow:
1. Request authorization
2. Exchange code for token
3. Create store in our backend
4. Redirect to setup wizard

**Run it:**
```bash
python3 scripts/test_oauth_flow.py
```

### `test_webhooks.py`
Tests webhook delivery:
- orders/created
- checkouts/create
- customers/create

**Run it:**
```bash
python3 scripts/test_webhooks.py
```

### `test_shopify_simulator.py`
End-to-end test suite:
- ✅ Service health checks
- ✅ Database connectivity
- ✅ OAuth flow
- ✅ Setup wizard API
- ✅ Color-coded output

**Run it:**
```bash
python3 scripts/test_shopify_simulator.py
```

### `generate_test_data.py`
Generate random test data:
- Random emails
- Secure passwords
- Store names
- Agent configurations

**Run it:**
```bash
python3 scripts/generate_test_data.py
```

## 📋 Complete Testing Workflow

```bash
# Terminal 1: Start all services
make start

# Terminal 2: Start mock Shopify server
python3 scripts/shopify_mock_server.py

# Terminal 3: Run complete test suite
python3 scripts/test_shopify_simulator.py

# If all pass, test individual flows:
python3 scripts/test_oauth_flow.py
python3 scripts/test_webhooks.py

# Generate test data for manual testing:
python3 scripts/generate_test_data.py
```

## ✅ Success Indicators

### Mock Server Starting
```
🎭 Mock Shopify Server Starting

This server simulates Shopify for local testing.
No real Shopify credentials needed!

Test credentials:
- API Key: test_api_key_12345
- API Secret: test_api_secret_67890
```

### OAuth Flow Success
```
✅ OAUTH FLOW SIMULATION COMPLETE!

Next steps:
1. Open setup wizard: http://localhost:3000/setup?store_id=...
2. Fill out account and store info
3. Enable AI agents
4. Click 'Activate'

The app will be live on the store! 🚀
```

### Test Suite Success
```
✅ All tests passed! ✨

PASS: Services
PASS: Database
PASS: OAuth Flow
PASS: Setup Wizard
```

## 🔧 Troubleshooting

### "Connection refused" on 8001
Mock server not running. Start it in another terminal:
```bash
python3 scripts/shopify_mock_server.py
```

### "Backend not responding"
Make sure API is running:
```bash
make start
# Wait 30 seconds for startup
```

### "Database test fails"
Check PostgreSQL is running:
```bash
make db-status
# Or restart:
make db-restart
```

### "OAuth test fails"
Check all services are healthy:
```bash
curl http://localhost:8000/health    # API
curl http://localhost:3000/          # Frontend
curl http://localhost:8001/health    # Mock Shopify
```

## 📊 Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| Mock OAuth | Request → Token → Code Exchange | ✅ |
| Setup Wizard API | Account → Store → Agents → Complete | ✅ |
| Webhooks | orders/created, checkouts/create, customers/create | ✅ |
| Database | Connectivity & basic queries | ✅ |
| Services | API, Frontend, Database health checks | ✅ |

## 🎓 Learning from Tests

Each script includes:
- **Detailed comments** explaining each step
- **Example payloads** showing what Shopify sends
- **Error handling** for common issues
- **Colored output** for easy reading

Perfect for understanding:
1. How OAuth works
2. What webhook payloads look like
3. How to structure test data
4. Integration points between services

## 🚀 Next Steps

1. **Run the tests locally** to verify everything works
2. **Review the LOCAL_TESTING_GUIDE.md** for comprehensive testing
3. **Check SHOPIFY_TEST_SIMULATOR.md** for detailed documentation
4. **Integrate into CI/CD** for automated testing
5. **Deploy to production** with confidence!

---

**All test scripts ready! Start testing now.** ✨
