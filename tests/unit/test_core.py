"""Unit tests for core components"""
import pytest
from datetime import datetime
from backend.models.models import Store, Customer, Session, Cart, Event


@pytest.fixture
def db():
    """Database fixture"""
    from backend.api.database import SessionLocal
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_store(db):
    """Create sample store"""
    store = Store(
        id="store_test_123",
        domain="testshop.myshopify.com",
        name="Test Shop",
        shopify_store_id="123456789",
        shopify_access_token="test_token"
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@pytest.fixture
def sample_customer(db, sample_store):
    """Create sample customer"""
    customer = Customer(
        id="cust_test_123",
        store_id=sample_store.id,
        email="test@example.com",
        phone="+1234567890",
        first_name="Test",
        last_name="Customer",
        lifetime_value=500.0,
        total_orders=5
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


class TestStoreModel:
    """Test Store model"""
    
    def test_store_creation(self, sample_store):
        assert sample_store.id is not None
        assert sample_store.domain == "testshop.myshopify.com"
        assert sample_store.plan == "starter"
    
    def test_store_subscription(self, sample_store, db):
        sample_store.plan = "pro"
        sample_store.subscription_status = "active"
        db.commit()
        
        fetched = db.query(Store).filter(Store.id == sample_store.id).first()
        assert fetched.plan == "pro"


class TestCustomerModel:
    """Test Customer model"""
    
    def test_customer_creation(self, sample_customer):
        assert sample_customer.email == "test@example.com"
        assert sample_customer.lifetime_value == 500.0
    
    def test_customer_metrics(self, sample_customer, db):
        sample_customer.lifetime_value = 1000.0
        sample_customer.total_orders = 10
        db.commit()
        
        fetched = db.query(Customer).filter(Customer.id == sample_customer.id).first()
        assert fetched.lifetime_value == 1000.0
        assert fetched.total_orders == 10


class TestSessionModel:
    """Test Session model"""
    
    def test_session_creation(self, sample_store, sample_customer):
        session = Session(
            id="sess_test_123",
            store_id=sample_store.id,
            customer_id=sample_customer.id,
            device="mobile",
            traffic_source="organic",
            page_views=5,
            product_views=3
        )
        
        assert session.page_views == 5
        assert session.device == "mobile"


class TestAuthenticationRoutes:
    """Test authentication endpoints"""
    
    @pytest.mark.asyncio
    async def test_login(self, client, db):
        """Test user login"""
        # Create test user
        user = create_test_user(db)
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    @pytest.mark.asyncio
    async def test_register(self, client, db):
        """Test user registration"""
        response = client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "testpass123",
            "name": "New User",
            "store_name": "New Store"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # Verify store created
        store = db.query(Store).filter_by(domain="example.com").first()
        assert store is not None


class TestEventIngestion:
    """Test event tracking"""
    
    @pytest.mark.asyncio
    async def test_event_batch_ingestion(self, client, api_key, db):
        """Test batch event ingestion"""
        response = client.post(
            "/api/v1/events/batch",
            json={
                "session_id": "sess_123",
                "customer_id": "cust_123",
                "events": [
                    {
                        "event_type": "page_view",
                        "event_data": {"path": "/products"}
                    },
                    {
                        "event_type": "product_view",
                        "event_data": {"product_id": "prod_123"}
                    }
                ]
            },
            headers={"api-key": api_key}
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    @pytest.mark.asyncio
    async def test_event_persistence(self, client, api_key, db):
        """Test events are saved to database"""
        client.post(
            "/api/v1/events/batch",
            json={
                "session_id": "sess_123",
                "events": [{
                    "event_type": "page_view",
                    "event_data": {}
                }]
            },
            headers={"api-key": api_key}
        )
        
        # Verify event saved
        event = db.query(Event).filter_by(session_id="sess_123").first()
        assert event is not None
        assert event.event_type == "page_view"


class TestAgentDecisions:
    """Test agent decision making"""
    
    @pytest.mark.asyncio
    async def test_behavior_prediction(self):
        """Test behavior intelligence agent"""
        from backend.agents.behavior_intelligence import BehaviorIntelligenceAgent
        from ml.inference.mock import MockInferenceClient
        
        agent = BehaviorIntelligenceAgent(MockInferenceClient())
        
        result = await agent.predict({
            "page_views": 10,
            "product_views": 5,
            "scroll_depth": 0.8,
            "time_on_site": 300,
            "device": "desktop",
            "traffic_source": "paid"
        })
        
        assert "purchase_probability" in result
        assert "abandonment_probability" in result
        assert 0 <= result["purchase_probability"] <= 1
    
    @pytest.mark.asyncio
    async def test_pricing_optimization(self):
        """Test pricing optimization agent"""
        from backend.agents.pricing_optimization import PricingOptimizationAgent
        from ml.inference.mock import MockInferenceClient
        
        agent = PricingOptimizationAgent(MockInferenceClient())
        
        result = await agent.optimize_discount({
            "cart_value": 75,
            "margin": 0.3,
            "price_sensitivity": 0.7,
            "lifetime_value": 100,
            "abandonment_probability": 0.8
        })
        
        assert "discount_percentage" in result
        assert 0 <= result["discount_percentage"] <= 35
        assert "coupon_code" in result


def create_test_user(db):
    """Helper to create test user"""
    from backend.api.security import hash_password
    
    store = Store(
        id="store_test",
        domain="test.com",
        name="Test",
        shopify_store_id="123",
        shopify_access_token="token"
    )
    db.add(store)
    db.commit()
    
    from backend.models.models import User
    user = User(
        id="user_test",
        store_id=store.id,
        email="test@example.com",
        name="Test User",
        password_hash=hash_password("testpass123"),
        role="admin"
    )
    db.add(user)
    db.commit()
    return user
