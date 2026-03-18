"""Configuration settings for NeuroCommerce OS API"""
import os
from typing import Optional, List

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

# API Configuration
API_VERSION = os.getenv("API_VERSION", "1.0.0")
API_TITLE = "NeuroCommerce OS API"
API_DESCRIPTION = "AI Revenue Operating System for ecommerce"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_LOG_LEVEL = os.getenv("API_LOG_LEVEL", "info").upper()

# ============================================================================
# SECURITY & AUTHENTICATION
# ============================================================================

# JWT Configuration
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-to-a-secure-random-key-in-production")

# Token Configuration
TOKEN_TYPE = os.getenv("TOKEN_TYPE", "bearer")

# Password Hashing
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))

# ============================================================================
# ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================================

# Available user roles
AVAILABLE_ROLES = ["admin", "editor", "viewer"]
DEFAULT_USER_ROLE = os.getenv("DEFAULT_USER_ROLE", "viewer")
DEFAULT_ADMIN_ROLE = os.getenv("DEFAULT_ADMIN_ROLE", "admin")

# ============================================================================
# STORE CONFIGURATION
# ============================================================================

# Default store settings
DEFAULT_STORE_PLAN = os.getenv("DEFAULT_STORE_PLAN", "starter")  # starter, pro, growth, enterprise
DEFAULT_SUBSCRIPTION_STATUS = os.getenv("DEFAULT_SUBSCRIPTION_STATUS", "active")  # active, paused, cancelled

# ID Prefix Configuration
STORE_ID_PREFIX = os.getenv("STORE_ID_PREFIX", "store_")
USER_ID_PREFIX = os.getenv("USER_ID_PREFIX", "user_")
SESSION_ID_PREFIX = os.getenv("SESSION_ID_PREFIX", "sess_")
CUSTOMER_ID_PREFIX = os.getenv("CUSTOMER_ID_PREFIX", "cust_")
CART_ID_PREFIX = os.getenv("CART_ID_PREFIX", "cart_")
EVENT_ID_PREFIX = os.getenv("EVENT_ID_PREFIX", "evt_")
ACTION_ID_PREFIX = os.getenv("ACTION_ID_PREFIX", "act_")
EXPERIMENT_ID_PREFIX = os.getenv("EXPERIMENT_ID_PREFIX", "exp_")
CAMPAIGN_ID_PREFIX = os.getenv("CAMPAIGN_ID_PREFIX", "camp_")
APIKEY_ID_PREFIX = os.getenv("APIKEY_ID_PREFIX", "key_")

# ============================================================================
# CROSS-ORIGIN RESOURCE SHARING (CORS)
# ============================================================================

CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3000,https://yourdomain.com")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]
DEFAULT_CORS_ORIGINS = CORS_ORIGINS

# Allowed hosts for TrustedHost middleware
ALLOWED_HOSTS_STR = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,neurocommerce.local")
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(",")]
DEFAULT_ALLOWED_HOSTS = ALLOWED_HOSTS

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL Connection (already in database.py, but included for reference)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neurocommerce:password@localhost:5432/neurocommerce"
)

# ============================================================================
# CACHE CONFIGURATION (Redis)
# ============================================================================

# Redis Connection (already in cache.py, but included for reference)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cache TTL (Time To Live) in seconds
CACHE_DEFAULT_EXPIRE = int(os.getenv("CACHE_DEFAULT_EXPIRE", "3600"))  # 1 hour
CACHE_SHORT_EXPIRE = int(os.getenv("CACHE_SHORT_EXPIRE", "300"))  # 5 minutes
CACHE_LONG_EXPIRE = int(os.getenv("CACHE_LONG_EXPIRE", "86400"))  # 1 day

# ============================================================================
# MESSAGE QUEUE CONFIGURATION (Kafka)
# ============================================================================

KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
KAFKA_CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "neurocommerce-group")

# Kafka Topics
KAFKA_TOPIC_EVENTS = "neurocommerce.events"
KAFKA_TOPIC_DECISIONS = "neurocommerce.decisions"
KAFKA_TOPIC_ACTIONS = "neurocommerce.actions"
KAFKA_TOPIC_BILLING = "neurocommerce.billing"

# ============================================================================
# CART & SHOPPING CONFIGURATION
# ============================================================================

# Default cart settings
DEFAULT_CART_STATUS = os.getenv("DEFAULT_CART_STATUS", "active")  # active, abandoned, converted

# ============================================================================
# EXPERIMENT CONFIGURATION
# ============================================================================

# Default experiment settings
DEFAULT_EXPERIMENT_STATUS = os.getenv("DEFAULT_EXPERIMENT_STATUS", "draft")  # draft, running, paused, complete

# Experiment types
EXPERIMENT_TYPES = ["discount", "copy", "timing", "offer"]

# ============================================================================
# CAMPAIGN CONFIGURATION
# ============================================================================

# Default campaign settings
DEFAULT_CAMPAIGN_STATUS = os.getenv("DEFAULT_CAMPAIGN_STATUS", "draft")  # draft, scheduled, running, paused, complete

# Campaign types
CAMPAIGN_TYPES = ["cart_recovery", "replenishment", "cross_sell", "retention"]

# Campaign channels
CAMPAIGN_CHANNELS = ["email", "sms", "whatsapp", "push"]

# ============================================================================
# API KEY CONFIGURATION
# ============================================================================

DEFAULT_API_KEY_ACTIVE = os.getenv("DEFAULT_API_KEY_ACTIVE", "true").lower() == "true"

# ============================================================================
# QUERY & PAGINATION CONFIGURATION
# ============================================================================

DEFAULT_QUERY_LIMIT = int(os.getenv("DEFAULT_QUERY_LIMIT", "100"))
MAX_QUERY_LIMIT = int(os.getenv("MAX_QUERY_LIMIT", "1000"))
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "500"))

# ============================================================================
# ML & AGENT CONFIGURATION
# ============================================================================

# ML Model Thresholds
PURCHASE_PROBABILITY_THRESHOLD = float(os.getenv("PURCHASE_PROBABILITY_THRESHOLD", "0.6"))
ABANDONMENT_PROBABILITY_THRESHOLD = float(os.getenv("ABANDONMENT_PROBABILITY_THRESHOLD", "0.7"))
CHURN_RISK_THRESHOLD = float(os.getenv("CHURN_RISK_THRESHOLD", "0.75"))

# Discount Configuration
MIN_DISCOUNT = float(os.getenv("MIN_DISCOUNT", "0.0"))
MAX_DISCOUNT = float(os.getenv("MAX_DISCOUNT", "35.0"))
DEFAULT_DISCOUNT = float(os.getenv("DEFAULT_DISCOUNT", "10.0"))

# Agent Confidence Thresholds
MIN_AGENT_CONFIDENCE = float(os.getenv("MIN_AGENT_CONFIDENCE", "0.5"))
OPTIMAL_AGENT_CONFIDENCE = float(os.getenv("OPTIMAL_AGENT_CONFIDENCE", "0.75"))

# Available agent types
AGENT_TYPES = [
    "behavior_intelligence",
    "cart_recovery",
    "checkout_persuasion",
    "experimentation",
    "pricing_optimization",
    "recommendation",
    "retention"
]

# ============================================================================
# SHOPIFY INTEGRATION
# ============================================================================

SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY", "")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET", "")
SHOPIFY_SCOPES = os.getenv(
    "SHOPIFY_SCOPES",
    "read_orders,read_products,read_customers,read_checkouts,write_discounts"
)
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")
SHOPIFY_WEBHOOK_TIMEOUT = int(os.getenv("SHOPIFY_WEBHOOK_TIMEOUT", "30"))

# ============================================================================
# PAYMENT PROCESSING (Stripe)
# ============================================================================

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# ============================================================================
# AI & LLM CONFIGURATION
# ============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))

# ============================================================================
# EMAIL & SMS CONFIGURATION
# ============================================================================

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@neurocommerce.io")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# ============================================================================
# ANALYTICS & OBSERVABILITY
# ============================================================================

PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))

OTEL_ENABLED = os.getenv("OTEL_ENABLED", "false").lower() == "true"
OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

# ============================================================================
# CLICKHOUSE ANALYTICS DATABASE
# ============================================================================

CLICKHOUSE_URL = os.getenv("CLICKHOUSE_URL", "http://clickhouse:8123/neurocommerce")
CLICKHOUSE_BATCH_SIZE = int(os.getenv("CLICKHOUSE_BATCH_SIZE", "100"))
CLICKHOUSE_BATCH_TIMEOUT = int(os.getenv("CLICKHOUSE_BATCH_TIMEOUT", "5"))

# ============================================================================
# REQUEST & RATE LIMITING
# ============================================================================

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "1000"))
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))

# ============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATION
# ============================================================================

IS_DEVELOPMENT = ENVIRONMENT.lower() in ["dev", "development", "local"]
IS_PRODUCTION = ENVIRONMENT.lower() in ["prod", "production"]
IS_STAGING = ENVIRONMENT.lower() in ["staging", "stage"]

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_config() -> bool:
    """Validate critical configuration values"""
    errors = []
    
    # Check JWT secret in production
    if IS_PRODUCTION and JWT_SECRET_KEY == "change-this-to-a-secure-random-key-in-production":
        errors.append("JWT_SECRET_KEY must be set in production")
    
    # Check API keys in production
    if IS_PRODUCTION:
        if not SHOPIFY_API_KEY or not SHOPIFY_API_SECRET:
            errors.append("Shopify credentials must be set in production")
        if not STRIPE_API_KEY:
            errors.append("STRIPE_API_KEY must be set in production")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


# Validate on import
if IS_PRODUCTION:
    validate_config()
