"""ClickHouse Client Service

Provides interface for storing analytics and ML training data in ClickHouse.
ClickHouse is optimized for analytics queries and time-series data.

Tables:
- events: Raw behavioral events
- sessions: Session-level aggregations
- customers: Customer features and metrics
- stores: Store configuration and metrics
- agent_actions: Agent decisions and outcomes
- conversions: Purchase conversion events
- store_metrics: Aggregated store performance metrics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """
    Client for ClickHouse analytics database
    
    Handles:
    - Connection management
    - Event insertion
    - Batch operations
    - Query execution
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        database: str = "neurocommerce",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """Initialize ClickHouse client"""
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.client = None
        
        try:
            import clickhouse_driver
            self.client = clickhouse_driver.Client(
                host=host,
                port=port,
                database=database,
                user=username or "default",
                password=password or "",
            )
            # Verify connection
            self.client.execute("SELECT 1")
            logger.info(f"Connected to ClickHouse at {host}:{port}")
        except Exception as e:
            logger.warning(f"ClickHouse connection failed: {e}. Analytics disabled.")
            self.client = None
    
    async def insert_event(self, enriched_event: Dict[str, Any]) -> None:
        """Insert enriched event into events table"""
        if not self.client:
            return
        
        try:
            query = """
            INSERT INTO events (
                event_id, session_id, store_id, event_type,
                event_data, customer_id, customer_ltv, customer_segment,
                page_views, product_views, scroll_depth, time_on_site,
                device, traffic_source, created_at
            ) VALUES
            """
            
            values = (
                enriched_event.get("event_id"),
                enriched_event.get("session_id"),
                enriched_event.get("store_id"),
                enriched_event.get("event_type"),
                json.dumps(enriched_event.get("event_data", {})),
                enriched_event.get("customer_data", {}).get("customer_id"),
                enriched_event.get("customer_data", {}).get("customer_ltv", 0),
                enriched_event.get("customer_data", {}).get("customer_segment"),
                enriched_event.get("session_data", {}).get("page_views", 0),
                enriched_event.get("session_data", {}).get("product_views", 0),
                enriched_event.get("session_data", {}).get("scroll_depth", 0),
                enriched_event.get("session_data", {}).get("time_on_site", 0),
                enriched_event.get("session_data", {}).get("device"),
                enriched_event.get("session_data", {}).get("traffic_source"),
                enriched_event.get("timestamp"),
            )
            
            self.client.execute(query, [values])
            logger.debug(f"Event {enriched_event.get('event_id')} inserted")
            
        except Exception as e:
            logger.error(f"Error inserting event: {e}")
    
    async def insert_agent_action(self, action: Dict[str, Any]) -> None:
        """Insert agent action and decision for training"""
        if not self.client:
            return
        
        try:
            query = """
            INSERT INTO agent_actions (
                action_id, session_id, store_id, agent_type,
                action, action_details, confidence, created_at
            ) VALUES
            """
            
            values = (
                action.get("action_id"),
                action.get("session_id"),
                action.get("store_id"),
                action.get("agent_type"),
                action.get("action"),
                json.dumps(action.get("action_details", {})),
                action.get("confidence", 0),
                action.get("timestamp"),
            )
            
            self.client.execute(query, [values])
            logger.debug(f"Agent action {action.get('action_id')} inserted")
            
        except Exception as e:
            logger.error(f"Error inserting agent action: {e}")
    
    async def insert_conversion(self, conversion: Dict[str, Any]) -> None:
        """Insert conversion event for training labels"""
        if not self.client:
            return
        
        try:
            query = """
            INSERT INTO conversions (
                session_id, store_id, customer_id,
                conversion_value, conversion_time, created_at
            ) VALUES
            """
            
            values = (
                conversion.get("session_id"),
                conversion.get("store_id"),
                conversion.get("customer_id"),
                conversion.get("conversion_value", 0),
                conversion.get("conversion_time"),
                conversion.get("timestamp"),
            )
            
            self.client.execute(query, [values])
            logger.debug(f"Conversion for session {conversion.get('session_id')} inserted")
            
        except Exception as e:
            logger.error(f"Error inserting conversion: {e}")
    
    async def insert_store_metrics(self, metrics: Dict[str, Any]) -> None:
        """Insert aggregated store metrics"""
        if not self.client:
            return
        
        try:
            query = """
            INSERT INTO store_metrics (
                store_id, store_plan,
                total_customers, avg_ltv, total_revenue,
                total_campaigns, total_conversions, conversion_rate,
                total_agent_actions, agent_conversion_rate, avg_agent_confidence,
                created_at
            ) VALUES
            """
            
            customer_metrics = metrics.get("customer_metrics", {})
            campaign_metrics = metrics.get("campaign_metrics", {})
            agent_metrics = metrics.get("agent_metrics", {})
            
            values = (
                metrics.get("store_id"),
                metrics.get("store_plan"),
                customer_metrics.get("total_customers", 0),
                customer_metrics.get("avg_ltv", 0),
                customer_metrics.get("total_revenue", 0),
                campaign_metrics.get("total_campaigns", 0),
                agent_metrics.get("total_conversions", 0),
                agent_metrics.get("conversion_rate", 0),
                agent_metrics.get("total_actions", 0),
                agent_metrics.get("conversion_rate", 0),
                agent_metrics.get("avg_confidence", 0),
                metrics.get("timestamp"),
            )
            
            self.client.execute(query, [values])
            logger.debug(f"Metrics for store {metrics.get('store_id')} inserted")
            
        except Exception as e:
            logger.error(f"Error inserting store metrics: {e}")
    
    async def create_tables(self) -> None:
        """Create all required ClickHouse tables"""
        if not self.client:
            return
        
        try:
            # Events table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id String,
                    session_id String,
                    store_id String,
                    event_type String,
                    event_data String,
                    customer_id Nullable(String),
                    customer_ltv Nullable(Float64),
                    customer_segment Nullable(String),
                    page_views UInt32,
                    product_views UInt32,
                    scroll_depth Float64,
                    time_on_site UInt32,
                    device Nullable(String),
                    traffic_source Nullable(String),
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (store_id, session_id, created_at)
                PARTITION BY toYYYYMM(created_at)
            """)
            
            # Agent actions table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS agent_actions (
                    action_id String,
                    session_id String,
                    store_id String,
                    agent_type String,
                    action String,
                    action_details String,
                    confidence Float64,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (store_id, session_id, created_at)
                PARTITION BY toYYYYMM(created_at)
            """)
            
            # Conversions table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS conversions (
                    session_id String,
                    store_id String,
                    customer_id String,
                    conversion_value Float64,
                    conversion_time DateTime,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (store_id, created_at)
                PARTITION BY toYYYYMM(created_at)
            """)
            
            # Store metrics table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS store_metrics (
                    store_id String,
                    store_plan String,
                    total_customers UInt32,
                    avg_ltv Float64,
                    total_revenue Float64,
                    total_campaigns UInt32,
                    total_conversions UInt32,
                    conversion_rate Float64,
                    total_agent_actions UInt32,
                    agent_conversion_rate Float64,
                    avg_agent_confidence Float64,
                    created_at DateTime
                ) ENGINE = MergeTree()
                ORDER BY (store_id, created_at)
                PARTITION BY toYYYYMM(created_at)
            """)
            
            logger.info("ClickHouse tables created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating ClickHouse tables: {e}")
    
    async def query_events(
        self,
        store_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Query events from ClickHouse"""
        if not self.client:
            return []
        
        try:
            conditions = []
            if store_id:
                conditions.append(f"store_id = '{store_id}'")
            if start_date:
                conditions.append(f"created_at >= '{start_date.isoformat()}'")
            if end_date:
                conditions.append(f"created_at <= '{end_date.isoformat()}'")
            if event_types:
                event_list = "', '".join(event_types)
                conditions.append(f"event_type IN ('{event_list}')")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
                SELECT * FROM events
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT {limit}
            """
            
            results = self.client.execute(query)
            return results
            
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []
    
    async def get_store_conversion_metrics(
        self,
        store_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get conversion metrics for a store"""
        if not self.client:
            return {}
        
        try:
            query = f"""
                SELECT
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN conversion_value > 0 THEN 1 ELSE 0 END) as conversions,
                    AVG(conversion_value) as avg_order_value,
                    SUM(conversion_value) as total_revenue
                FROM conversions
                WHERE store_id = '{store_id}'
                AND created_at >= subtractDays(now(), {days})
            """
            
            result = self.client.execute(query)
            if result:
                return {
                    "total_sessions": result[0][0],
                    "conversions": result[0][1],
                    "conversion_rate": result[0][1] / result[0][0] if result[0][0] > 0 else 0,
                    "avg_order_value": result[0][2],
                    "total_revenue": result[0][3],
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error getting store conversion metrics: {e}")
            return {}
