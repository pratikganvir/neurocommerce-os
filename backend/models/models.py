"""SQLAlchemy ORM Models for NeuroCommerce OS"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text, JSON, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

# Note: For circular import avoidance, defaults are kept as literals in models
# but documented here. Use config module when instantiating models.
# DEFAULT_STORE_PLAN = "starter"
# DEFAULT_SUBSCRIPTION_STATUS = "active"
# DEFAULT_USER_ROLE = "viewer"
# DEFAULT_CART_STATUS = "active"
# DEFAULT_EXPERIMENT_STATUS = "draft"
# DEFAULT_CAMPAIGN_STATUS = "draft"
# DEFAULT_API_KEY_ACTIVE = True

Base = declarative_base()


class Store(Base):
    """Merchant store"""
    __tablename__ = "stores"

    id = Column(String, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    shopify_access_token = Column(String, nullable=False)
    shopify_store_id = Column(String, unique=True, nullable=False)
    
    # Subscription
    plan = Column(String, default="starter")  # Configuration: DEFAULT_STORE_PLAN
    subscription_status = Column(String, default="active")  # Configuration: DEFAULT_SUBSCRIPTION_STATUS
    stripe_customer_id = Column(String, unique=True)
    stripe_subscription_id = Column(String)
    
    # Settings
    settings = Column(JSON, default={})
    enabled_agents = Column(JSON, default=[])  # List of enabled agent types
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="store")
    customers = relationship("Customer", back_populates="store")
    sessions = relationship("Session", back_populates="store")
    carts = relationship("Cart", back_populates="store")
    agent_actions = relationship("AgentAction", back_populates="store")


class User(Base):
    """Store users/team members"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer")  # Configuration: DEFAULT_USER_ROLE
    oauth_provider = Column(String)  # google, github, etc
    oauth_id = Column(String)
    
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    store = relationship("Store", back_populates="users")


class Customer(Base):
    """Store customers"""
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), nullable=False)
    shopify_customer_id = Column(String)
    email = Column(String, index=True)
    phone = Column(String)
    
    first_name = Column(String)
    last_name = Column(String)
    
    # Metrics
    lifetime_value = Column(Float, default=0)
    total_orders = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0)
    last_order_date = Column(DateTime)
    
    # Segmentation
    segment = Column(String)  # VIP, high-value, at-risk, etc
    churn_risk = Column(Float, default=0)  # 0-1 probability: Configuration: CHURN_RISK_THRESHOLD
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (Index("idx_store_email", "store_id", "email"),)
    
    store = relationship("Store", back_populates="customers")
    sessions = relationship("Session", back_populates="customer")
    carts = relationship("Cart", back_populates="customer")


class Session(Base):
    """Customer browser sessions"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"))
    
    # Traffic
    traffic_source = Column(String)  # organic, paid, direct, referral
    device = Column(String)  # mobile, desktop, tablet
    browser = Column(String)
    os = Column(String)
    
    # Behavior
    page_views = Column(Integer, default=0)
    product_views = Column(Integer, default=0)
    scroll_depth = Column(Float, default=0)  # 0-1
    time_on_site = Column(Integer, default=0)  # seconds
    
    # Prediction
    purchase_probability = Column(Float, default=0)  # Configuration: PURCHASE_PROBABILITY_THRESHOLD
    abandonment_probability = Column(Float, default=0)  # Configuration: ABANDONMENT_PROBABILITY_THRESHOLD
    intent_class = Column(String)  # high, medium, low
    
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    
    store = relationship("Store", back_populates="sessions")
    customer = relationship("Customer", back_populates="sessions")
    carts = relationship("Cart", back_populates="session")
    events = relationship("Event", back_populates="session")


class Cart(Base):
    """Shopping carts"""
    __tablename__ = "carts"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id"))
    customer_id = Column(String, ForeignKey("customers.id"))
    shopify_cart_token = Column(String, unique=True)
    
    cart_value = Column(Float, default=0)
    item_count = Column(Integer, default=0)
    items = Column(JSON, default=[])  # Product details
    
    status = Column(String, default="active")  # Configuration: DEFAULT_CART_STATUS
    abandonment_reason = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (Index("idx_store_status", "store_id", "status"),)
    
    store = relationship("Store", back_populates="carts")
    session = relationship("Session", back_populates="carts")
    customer = relationship("Customer", back_populates="carts")


class Event(Base):
    """Raw behavior events"""
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    event_type = Column(String, index=True)  # page_view, product_view, click, scroll, etc
    event_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (Index("idx_session_type_time", "session_id", "event_type", "created_at"),)
    
    session = relationship("Session", back_populates="events")


class AgentAction(Base):
    """Agent decisions and actions"""
    __tablename__ = "agent_actions"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), index=True)
    session_id = Column(String, index=True)
    
    agent_type = Column(String)  # behavior, checkout_persuasion, cart_recovery, etc
    action = Column(String)  # coupon, banner, email, sms, etc
    action_details = Column(JSON)  # Specific action parameters
    
    # Execution
    executed = Column(Boolean, default=False)
    execution_channel = Column(String)  # email, sms, whatsapp, banner, etc
    
    # Results
    delivered = Column(Boolean, default=False)
    engaged = Column(Boolean)
    converted = Column(Boolean)
    
    confidence = Column(Float, default=0)  # Configuration: MIN_AGENT_CONFIDENCE, OPTIMAL_AGENT_CONFIDENCE
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    executed_at = Column(DateTime)
    
    __table_args__ = (Index("idx_store_type_time", "store_id", "agent_type", "created_at"),)
    
    store = relationship("Store", back_populates="agent_actions")


class ExperimentClass(str, enum.Enum):
    """Experiment types"""
    DISCOUNT = "discount"
    COPY = "copy"
    TIMING = "timing"
    OFFER = "offer"


class Experiment(Base):
    """A/B experiments"""
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), index=True)
    
    name = Column(String, nullable=False)
    experiment_type = Column(String)  # discount, copy, timing, offer
    
    # Variants
    control_variant = Column(JSON)  # Original / control variant
    test_variants = Column(JSON)  # List of test variants
    
    # Configuration
    allocation = Column(JSON)  # Allocation percentages per variant
    duration_days = Column(Integer)
    
    # Results
    status = Column(String, default="draft")  # Configuration: DEFAULT_EXPERIMENT_STATUS
    winner = Column(String)  # Best performing variant
    statistical_significance = Column(Float)
    
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CampaignStatus(str, enum.Enum):
    """Campaign statuses"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"


class Campaign(Base):
    """Marketing campaigns (email, SMS, push, etc)"""
    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), index=True)
    
    name = Column(String, nullable=False)
    campaign_type = Column(String)  # cart_recovery, replenishment, cross_sell, etc
    
    # Configuration
    target_segment = Column(String)  # Customer segment targeting
    channels = Column(JSON)  # email, sms, whatsapp, push
    message_template = Column(Text)  # Template for personalization
    
    # Scheduling
    status = Column(String, default="draft")
    schedule = Column(JSON)  # Cron or one-time scheduling
    
    # Results
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    converted_count = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApiKey(Base):
    """API keys for store authentication"""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), index=True)
    
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)


class BillingEvent(Base):
    """Billing and usage tracking"""
    __tablename__ = "billing_events"

    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"), index=True)
    
    event_type = Column(String)  # api_call, email_sent, sms_sent, agent_decision, etc
    metric_value = Column(Float, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (Index("idx_store_type_date", "store_id", "event_type", "created_at"),)
