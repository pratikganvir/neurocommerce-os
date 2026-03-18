"""Integration tests"""
import pytest
import asyncio
from datetime import datetime


@pytest.mark.integration
class TestEndToEndFlow:
    """Test complete user journey"""
    
    @pytest.mark.asyncio
    async def test_full_checkout_flow(self, client, api_key, kafka_producer, db):
        """Test: SDK track → API ingestion → Agent decision → Action"""
        
        # 1. Initialize SDK session
        session_id = "sess_e2e_123"
        
        # 2. Ingest tracking events
        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": session_id,
                "customer_id": "cust_e2e_123",
                "events": [
                    {"event_type": "page_view", "event_data": {"path": "/products"}},
                    {"event_type": "product_view", "event_data": {"product_id": "prod_1"}},
                    {"event_type": "product_view", "event_data": {"product_id": "prod_2"}},
                    {"event_type": "add_to_cart", "event_data": {"product_id": "prod_1"}},
                    {"event_type": "checkout_start", "event_data": {"cart_value": 99.99}}
                ]
            },
            headers={"api-key": api_key}
        )
        
        assert response.status_code == 200
        
        # 3. Verify events were queued
        await asyncio.sleep(0.5)  # Let async processing happen
        
        # 4. Simulate agent decision
        from backend.orchestration.orchestrator import AgentOrchestrator
        from ml.inference.mock import MockInferenceClient
        from backend.services.mock import MockMessagingService, MockShopifyService
        
        orchestrator = AgentOrchestrator(
            db,
            MockInferenceClient(),
            MockMessagingService(),
            MockShopifyService()
        )
        
        # 5. Process event through orchestrator
        decision = await orchestrator.process_event({
            "event_type": "checkout_start",
            "session_id": session_id,
            "store_id": "store_123",
            "customer_id": "cust_123"
        })
        
        # 6. Verify decision was made
        assert decision is not None
        assert decision["agent_type"] in [
            "checkout_persuasion",
            "recommendation"
        ]


@pytest.mark.integration
class TestKafkaEventProcessing:
    """Test Kafka event streaming"""
    
    @pytest.mark.asyncio
    async def test_event_to_kafka(self, kafka_producer, kafka_consumer):
        """Test events published to Kafka are consumed"""
        
        # Publish event
        event = {
            "event_type": "page_view",
            "session_id": "sess_kafka_123",
            "store_id": "store_123"
        }
        
        kafka_producer.send("user_behavior_events", value=event)
        
        # Consume event
        consumer_records = kafka_consumer.poll(timeout_ms=1000)
        
        # Verify event received
        assert len(consumer_records) > 0


@pytest.mark.integration
class TestShopifyIntegration:
    """Test Shopify integration"""
    
    @pytest.mark.asyncio
    async def test_shopify_order_webhook(self, client, db):
        """Test Shopify order.created webhook"""
        import hmac
        import hashlib
        import base64
        
        webhook_data = {
            "id": "order_123",
            "email": "customer@example.com",
            "total_price": "99.99",
            "line_items": [],
            "customer": {
                "id": "cust_456",
                "email": "customer@example.com",
                "first_name": "John",
                "last_name": "Doe"
            },
            "shop": {"myshopify_domain": "testshop.myshopify.com"}
        }
        
        # Create HMAC signature
        import json
        import os
        secret = os.getenv("SHOPIFY_API_SECRET", "test").encode()
        payload = json.dumps(webhook_data).encode()
        
        signature = base64.b64encode(
            hmac.new(secret, payload, hashlib.sha256).digest()
        )
        
        # Send webhook
        response = client.post(
            "/api/v1/shopify/webhooks/orders/create",
            json=webhook_data,
            headers={"X-Shopify-Hmac-SHA256": signature.decode()}
        )
        
        # Verify order was processed
        assert response.status_code == 200


@pytest.mark.integration
class TestDashboardMetrics:
    """Test dashboard metrics generation"""
    
    @pytest.mark.asyncio
    async def test_revenue_metrics(self, client, db, auth_token):
        """Test revenue metrics endpoint"""
        response = client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "revenue" in data["stats"]
        assert "conversions" in data["stats"]


@pytest.mark.integration
class TestMultiTenant:
    """Test multi-tenant isolation"""
    
    @pytest.mark.asyncio
    async def test_store_isolation(self, client, db):
        """Test that stores can't access each other's data"""
        
        # Create two stores
        store1 = create_store(db, "store1.com")
        store2 = create_store(db, "store2.com")
        
        # Get API keys
        api_key1 = create_api_key(db, store1.id)
        api_key2 = create_api_key(db, store2.id)
        
        # Store1 ingests events
        client.post(
            "/api/v1/events/batch",
            json={
                "session_id": "sess_store1",
                "events": [{"event_type": "page_view", "event_data": {}}]
            },
            headers={"api-key": api_key1.key}
        )
        
        # Store2 ingests events
        client.post(
            "/api/v1/events/batch",
            json={
                "session_id": "sess_store2",
                "events": [{"event_type": "page_view", "event_data": {}}]
            },
            headers={"api-key": api_key2.key}
        )
        
        # Store1 should only see its own events
        store1_events = db.query(Event).filter_by(session_id="sess_store1").count()
        store2_events = db.query(Event).filter_by(session_id="sess_store2").count()
        
        assert store1_events == 1
        assert store2_events == 1


def create_store(db, domain):
    """Helper to create store"""
    from backend.models.models import Store
    store = Store(
        id=f"store_{domain}",
        domain=domain,
        name=domain,
        shopify_store_id=domain,
        shopify_access_token="token"
    )
    db.add(store)
    db.commit()
    return store


def create_api_key(db, store_id):
    """Helper to create API key"""
    from backend.models.models import ApiKey
    import secrets
    
    key = ApiKey(
        id=f"key_{secrets.token_urlsafe(8)}",
        store_id=store_id,
        key=f"sk_live_{secrets.token_urlsafe(32)}",
        name="Test Key"
    )
    db.add(key)
    db.commit()
    return key
