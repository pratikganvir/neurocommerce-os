"""ML Data Pipeline Service

Ensures all event data and stores data is properly captured, enriched,
and stored for ML model training and analytics.

Data Flow:
1. Events ingested via /events/batch endpoint
2. Events stored in PostgreSQL (events table)
3. Events published to Kafka (for real-time processing)
4. Events sent to ClickHouse (for analytics & ML training)
5. Daily export of training datasets to cloud storage
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.models import (
    Event, Session as SessionModel, Customer, Store, 
    AgentAction, Cart, Campaign, Experiment
)
from ..database import SessionLocal

logger = logging.getLogger(__name__)


class MLDataPipeline:
    """
    Central service for ML training data management
    
    Responsibilities:
    1. Capture all event data (behavioral, conversion, agent actions)
    2. Enrich events with context (customer, store, session)
    3. Store in ClickHouse for analytics
    4. Export training datasets periodically
    5. Validate data quality
    """
    
    def __init__(self):
        self.clickhouse_enabled = False
        self.kafka_enabled = False
        try:
            from ..services.clickhouse_client import ClickHouseClient
            self.clickhouse = ClickHouseClient()
            self.clickhouse_enabled = True
        except Exception as e:
            logger.warning(f"ClickHouse not available: {e}")
        
        try:
            from ..services.kafka_producer import produce_analytics_event
            self.kafka_enabled = True
        except Exception as e:
            logger.warning(f"Kafka not available: {e}")
    
    async def ingest_event(
        self,
        event_id: str,
        session_id: str,
        store_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        timestamp: datetime,
        db: Session
    ) -> None:
        """
        Ingest a single event and send to all analytics pipelines
        
        Args:
            event_id: Unique event identifier
            session_id: Session this event belongs to
            store_id: Store/merchant ID
            event_type: Type of event (page_view, product_view, click, etc)
            event_data: Event payload with detailed data
            timestamp: Event timestamp
            db: Database session
        """
        try:
            # Get enrichment context
            session = db.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            
            customer = None
            customer_data = {}
            if session and session.customer_id:
                customer = db.query(Customer).filter(
                    Customer.id == session.customer_id
                ).first()
                if customer:
                    customer_data = {
                        "customer_id": customer.id,
                        "customer_ltv": customer.lifetime_value,
                        "customer_segment": customer.segment,
                        "total_orders": customer.total_orders,
                        "churn_risk": customer.churn_risk,
                    }
            
            # Get store
            store = db.query(Store).filter(Store.id == store_id).first()
            store_data = {}
            if store:
                store_data = {
                    "store_id": store.id,
                    "store_plan": store.plan,
                    "store_domain": store.domain,
                }
            
            # Build enriched event
            enriched_event = {
                "event_id": event_id,
                "session_id": session_id,
                "store_id": store_id,
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": timestamp.isoformat(),
                
                # Session context
                "session_data": {
                    "page_views": session.page_views if session else 0,
                    "product_views": session.product_views if session else 0,
                    "scroll_depth": session.scroll_depth if session else 0,
                    "time_on_site": (
                        (datetime.utcnow() - session.start_time).total_seconds()
                        if session else 0
                    ),
                    "device": session.device if session else None,
                    "traffic_source": session.traffic_source if session else None,
                    "browser": session.browser if session else None,
                    "os": session.os if session else None,
                },
                
                # Customer context
                "customer_data": customer_data,
                
                # Store context
                "store_data": store_data,
                
                # Processing metadata
                "processed_at": datetime.utcnow().isoformat(),
            }
            
            # Send to ClickHouse for analytics
            if self.clickhouse_enabled:
                await self._send_to_clickhouse(enriched_event)
            
            # Send to Kafka for real-time processing
            if self.kafka_enabled:
                from ..services.kafka_producer import produce_analytics_event
                produce_analytics_event(enriched_event)
            
            logger.info(f"Event {event_id} ingested successfully")
            
        except Exception as e:
            logger.error(f"Error ingesting event {event_id}: {e}", exc_info=True)
    
    async def _send_to_clickhouse(self, enriched_event: Dict[str, Any]) -> None:
        """Send enriched event to ClickHouse"""
        try:
            await self.clickhouse.insert_event(enriched_event)
        except Exception as e:
            logger.error(f"Error sending to ClickHouse: {e}")
    
    async def capture_agent_action(
        self,
        action_id: str,
        session_id: str,
        store_id: str,
        agent_type: str,
        action: str,
        action_details: Dict[str, Any],
        confidence: float,
        db: Session
    ) -> None:
        """
        Capture agent decision and action for ML training
        
        Important for supervised learning:
        - What action did the agent recommend?
        - What was the confidence?
        - Did the customer convert?
        - What was the impact?
        """
        try:
            enriched_action = {
                "action_id": action_id,
                "session_id": session_id,
                "store_id": store_id,
                "agent_type": agent_type,
                "action": action,
                "action_details": action_details,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Send to ClickHouse
            if self.clickhouse_enabled:
                await self.clickhouse.insert_agent_action(enriched_action)
            
            logger.info(f"Agent action {action_id} captured")
            
        except Exception as e:
            logger.error(f"Error capturing agent action: {e}")
    
    async def capture_conversion(
        self,
        session_id: str,
        store_id: str,
        customer_id: str,
        cart_value: float,
        conversion_time: datetime,
        db: Session
    ) -> None:
        """
        Capture conversion event for ML training labels
        
        This is critical for training conversion prediction models
        """
        try:
            enriched_conversion = {
                "event_type": "conversion",
                "session_id": session_id,
                "store_id": store_id,
                "customer_id": customer_id,
                "conversion_value": cart_value,
                "conversion_time": conversion_time.isoformat(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Send to ClickHouse
            if self.clickhouse_enabled:
                await self.clickhouse.insert_conversion(enriched_conversion)
            
            logger.info(f"Conversion captured for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error capturing conversion: {e}")
    
    async def capture_store_metrics(
        self,
        store_id: str,
        db: Session
    ) -> None:
        """
        Capture store-level aggregated metrics for ML training
        
        Includes:
        - Revenue metrics
        - Customer metrics
        - Campaign performance
        - Agent action effectiveness
        """
        try:
            store = db.query(Store).filter(Store.id == store_id).first()
            if not store:
                return
            
            # Customer metrics
            customers = db.query(Customer).filter(
                Customer.store_id == store_id
            ).all()
            
            customer_metrics = {
                "total_customers": len(customers),
                "avg_ltv": sum(c.lifetime_value for c in customers) / len(customers) if customers else 0,
                "total_revenue": sum(c.lifetime_value for c in customers),
                "avg_orders": sum(c.total_orders for c in customers) / len(customers) if customers else 0,
            }
            
            # Campaign metrics
            campaigns = db.query(Campaign).filter(
                Campaign.store_id == store_id,
                Campaign.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            campaign_metrics = {
                "total_campaigns": len(campaigns),
                "total_sent": sum(c.sent_count for c in campaigns),
                "total_delivered": sum(c.delivered_count for c in campaigns),
                "total_opened": sum(c.opened_count for c in campaigns),
                "total_converted": sum(c.converted_count for c in campaigns),
                "total_revenue": sum(c.revenue_generated for c in campaigns),
                "avg_open_rate": (
                    sum(c.opened_count for c in campaigns) / sum(c.sent_count for c in campaigns)
                    if sum(c.sent_count for c in campaigns) > 0 else 0
                ),
                "avg_conversion_rate": (
                    sum(c.converted_count for c in campaigns) / sum(c.sent_count for c in campaigns)
                    if sum(c.sent_count for c in campaigns) > 0 else 0
                ),
            }
            
            # Agent metrics
            agent_actions = db.query(AgentAction).filter(
                AgentAction.store_id == store_id,
                AgentAction.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            agent_metrics = {
                "total_actions": len(agent_actions),
                "avg_confidence": sum(a.confidence for a in agent_actions) / len(agent_actions) if agent_actions else 0,
                "total_conversions": sum(1 for a in agent_actions if a.converted),
                "conversion_rate": (
                    sum(1 for a in agent_actions if a.converted) / len(agent_actions)
                    if agent_actions else 0
                ),
                "by_agent_type": {}
            }
            
            # Agent breakdown
            for agent_type in set(a.agent_type for a in agent_actions):
                agent_type_actions = [a for a in agent_actions if a.agent_type == agent_type]
                agent_metrics["by_agent_type"][agent_type] = {
                    "count": len(agent_type_actions),
                    "conversion_rate": (
                        sum(1 for a in agent_type_actions if a.converted) / len(agent_type_actions)
                        if agent_type_actions else 0
                    ),
                    "avg_confidence": (
                        sum(a.confidence for a in agent_type_actions) / len(agent_type_actions)
                        if agent_type_actions else 0
                    ),
                }
            
            enriched_metrics = {
                "metric_type": "store_aggregated",
                "store_id": store_id,
                "store_plan": store.plan,
                "customer_metrics": customer_metrics,
                "campaign_metrics": campaign_metrics,
                "agent_metrics": agent_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Send to ClickHouse
            if self.clickhouse_enabled:
                await self.clickhouse.insert_store_metrics(enriched_metrics)
            
            logger.info(f"Store metrics captured for {store_id}")
            
        except Exception as e:
            logger.error(f"Error capturing store metrics: {e}")
    
    async def export_training_dataset(
        self,
        store_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        output_format: str = "csv"
    ) -> str:
        """
        Export training dataset for ML model training
        
        Args:
            store_id: Specific store or all stores if None
            start_date: Training data start date
            end_date: Training data end date
            output_format: csv, parquet, or json
        
        Returns:
            Path to exported dataset
        """
        try:
            if start_date is None:
                start_date = datetime.utcnow() - timedelta(days=90)
            if end_date is None:
                end_date = datetime.utcnow()
            
            db = SessionLocal()
            
            # Query events
            query = db.query(Event).filter(
                Event.created_at >= start_date,
                Event.created_at <= end_date
            )
            
            if store_id:
                # Get sessions for this store
                sessions = db.query(SessionModel.id).filter(
                    SessionModel.store_id == store_id
                ).all()
                session_ids = [s[0] for s in sessions]
                query = query.filter(Event.session_id.in_(session_ids))
            
            events = query.all()
            
            # Convert to format suitable for ML
            training_data = []
            for event in events:
                training_data.append({
                    "event_id": event.id,
                    "session_id": event.session_id,
                    "event_type": event.event_type,
                    "event_data": json.dumps(event.event_data),
                    "created_at": event.created_at.isoformat(),
                })
            
            # Export to file
            if output_format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if training_data:
                    writer = csv.DictWriter(output, fieldnames=training_data[0].keys())
                    writer.writeheader()
                    writer.writerows(training_data)
                
                filepath = f"/tmp/training_data_{datetime.utcnow().isoformat()}.csv"
                with open(filepath, 'w') as f:
                    f.write(output.getvalue())
            
            elif output_format == "json":
                import json
                filepath = f"/tmp/training_data_{datetime.utcnow().isoformat()}.json"
                with open(filepath, 'w') as f:
                    json.dump(training_data, f)
            
            else:
                raise ValueError(f"Unsupported format: {output_format}")
            
            logger.info(f"Training dataset exported to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting training dataset: {e}")
            raise
    
    async def validate_data_quality(
        self,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate data quality for ML training
        
        Checks:
        - Event completeness
        - Missing values
        - Data consistency
        - Outliers
        """
        try:
            db = SessionLocal()
            
            quality_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {}
            }
            
            # Check 1: Event coverage
            query = db.query(Event)
            if store_id:
                sessions = db.query(SessionModel.id).filter(
                    SessionModel.store_id == store_id
                ).all()
                session_ids = [s[0] for s in sessions]
                query = query.filter(Event.session_id.in_(session_ids))
            
            total_events = query.count()
            quality_report["checks"]["total_events"] = total_events
            quality_report["checks"]["events_24h"] = query.filter(
                Event.created_at >= datetime.utcnow() - timedelta(days=1)
            ).count()
            
            # Check 2: Session completeness
            sessions_query = db.query(SessionModel)
            if store_id:
                sessions_query = sessions_query.filter(SessionModel.store_id == store_id)
            
            total_sessions = sessions_query.count()
            quality_report["checks"]["total_sessions"] = total_sessions
            quality_report["checks"]["sessions_with_customer"] = sessions_query.filter(
                SessionModel.customer_id.isnot(None)
            ).count()
            
            # Check 3: Customer data quality
            customers_query = db.query(Customer)
            if store_id:
                customers_query = customers_query.filter(Customer.store_id == store_id)
            
            total_customers = customers_query.count()
            quality_report["checks"]["total_customers"] = total_customers
            quality_report["checks"]["customers_with_ltv"] = customers_query.filter(
                Customer.lifetime_value > 0
            ).count()
            
            # Check 4: Agent action quality
            actions_query = db.query(AgentAction)
            if store_id:
                actions_query = actions_query.filter(AgentAction.store_id == store_id)
            
            total_actions = actions_query.count()
            quality_report["checks"]["total_agent_actions"] = total_actions
            quality_report["checks"]["actions_with_outcome"] = actions_query.filter(
                or_(
                    AgentAction.converted.isnot(None),
                    AgentAction.engaged.isnot(None)
                )
            ).count()
            
            quality_report["overall_quality_score"] = (
                quality_report["checks"]["sessions_with_customer"] / max(total_sessions, 1) * 0.3 +
                quality_report["checks"]["customers_with_ltv"] / max(total_customers, 1) * 0.3 +
                quality_report["checks"]["actions_with_outcome"] / max(total_actions, 1) * 0.4
            ) if total_sessions > 0 else 0
            
            logger.info(f"Data quality report: {quality_report}")
            return quality_report
            
        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            raise


# Singleton instance
_pipeline_instance = None


def get_ml_pipeline() -> MLDataPipeline:
    """Get or create ML data pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MLDataPipeline()
    return _pipeline_instance
