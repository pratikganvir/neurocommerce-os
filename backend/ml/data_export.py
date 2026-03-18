"""ML Training Data Export Utilities

Provides functions to export data from ClickHouse/PostgreSQL
in formats suitable for ML model training.

Supports:
- Feature engineering from raw events
- Data validation and quality checks
- Multiple export formats (CSV, Parquet, JSON)
- Time-series data handling
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import json
from enum import Enum

logger = logging.getLogger(__name__)


class ExportFormat(str, Enum):
    """Supported export formats"""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class FeatureEngineer:
    """
    Feature engineering for ML training data
    
    Creates features from raw events and session data
    """
    
    @staticmethod
    def extract_session_features(
        events: List[Dict[str, Any]],
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract features from session events
        
        Creates:
        - Engagement features (page_views, product_views, scroll_depth)
        - Time features (session_duration, peak_time)
        - Behavioral features (scroll_rate, product_interest)
        - Purchase intent signals
        """
        features = {
            # Basic engagement metrics
            "page_views": session_data.get("page_views", 0),
            "product_views": session_data.get("product_views", 0),
            "scroll_depth": session_data.get("scroll_depth", 0),
            "time_on_site": session_data.get("time_on_site", 0),
            
            # Event-level features
            "total_events": len(events),
            "event_types": list(set(e.get("event_type") for e in events)),
        }
        
        # Engagement rate features
        if features["total_events"] > 0:
            features["page_view_ratio"] = features["page_views"] / features["total_events"]
            features["product_view_ratio"] = features["product_views"] / features["total_events"]
        else:
            features["page_view_ratio"] = 0
            features["product_view_ratio"] = 0
        
        # Scroll engagement
        features["scroll_engagement"] = min(features["scroll_depth"] / 100, 1.0)  # Normalize to 0-1
        
        # Time-based features
        if features["time_on_site"] > 0:
            features["avg_time_per_page"] = (
                features["time_on_site"] / max(features["page_views"], 1)
            )
        else:
            features["avg_time_per_page"] = 0
        
        # Purchase intent signals
        cart_events = [e for e in events if e.get("event_type") == "add_to_cart"]
        features["add_to_cart_count"] = len(cart_events)
        features["has_cart_action"] = 1 if cart_events else 0
        
        # Purchase view signals
        purchase_events = [e for e in events if e.get("event_type") == "purchase"]
        features["has_purchase"] = 1 if purchase_events else 0
        
        return features
    
    @staticmethod
    def extract_customer_features(
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract features from customer data
        
        Creates:
        - Lifetime value features
        - Purchase history features
        - Churn risk signals
        - Segment indicators
        """
        features = {
            "customer_ltv": customer_data.get("customer_ltv", 0),
            "total_orders": customer_data.get("total_orders", 0),
            "avg_order_value": (
                customer_data.get("customer_ltv", 0) / max(customer_data.get("total_orders", 1), 1)
            ),
            "churn_risk": customer_data.get("churn_risk", 0),
        }
        
        # Segment one-hot encoding
        segment = customer_data.get("customer_segment", "unknown")
        features["is_vip"] = 1 if segment == "vip" else 0
        features["is_active"] = 1 if segment == "active" else 0
        features["is_churned"] = 1 if segment == "churned" else 0
        features["is_new"] = 1 if segment == "new" else 0
        
        # LTV buckets
        ltv = features["customer_ltv"]
        features["ltv_high"] = 1 if ltv >= 1000 else 0
        features["ltv_medium"] = 1 if 100 <= ltv < 1000 else 0
        features["ltv_low"] = 1 if ltv > 0 and ltv < 100 else 0
        features["ltv_zero"] = 1 if ltv == 0 else 0
        
        return features
    
    @staticmethod
    def extract_store_features(
        store_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract features from store/merchant data
        
        Creates:
        - Store plan indicators
        - Merchant maturity signals
        """
        features = {
            "store_id": store_data.get("store_id"),
        }
        
        # Store plan one-hot encoding
        plan = store_data.get("store_plan", "free")
        features["plan_free"] = 1 if plan == "free" else 0
        features["plan_starter"] = 1 if plan == "starter" else 0
        features["plan_growth"] = 1 if plan == "growth" else 0
        features["plan_enterprise"] = 1 if plan == "enterprise" else 0
        
        return features


class DataValidator:
    """
    Validates training data quality
    """
    
    @staticmethod
    def validate_feature_set(features: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that all required features are present and valid
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for NaN or null values
        for key, value in features.items():
            if value is None:
                errors.append(f"Missing value for feature: {key}")
            elif isinstance(value, float) and not (-1e10 < value < 1e10):
                errors.append(f"Out of range value for {key}: {value}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_dataset(
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate entire dataset
        
        Returns quality metrics
        """
        report = {
            "total_records": len(data),
            "valid_records": 0,
            "invalid_records": 0,
            "issues": [],
        }
        
        for idx, record in enumerate(data):
            is_valid, errors = DataValidator.validate_feature_set(record)
            if is_valid:
                report["valid_records"] += 1
            else:
                report["invalid_records"] += 1
                report["issues"].append({
                    "record_idx": idx,
                    "errors": errors
                })
        
        report["quality_score"] = (
            report["valid_records"] / report["total_records"]
            if report["total_records"] > 0 else 0
        )
        
        return report


class TrainingDataExporter:
    """
    Export training data in various formats
    """
    
    @staticmethod
    def export_to_csv(
        data: List[Dict[str, Any]],
        filepath: str
    ) -> None:
        """Export data to CSV format"""
        try:
            import csv
            
            if not data:
                logger.warning("No data to export")
                return
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Exported {len(data)} records to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    @staticmethod
    def export_to_json(
        data: List[Dict[str, Any]],
        filepath: str
    ) -> None:
        """Export data to JSON format"""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Exported {len(data)} records to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            raise
    
    @staticmethod
    def export_to_parquet(
        data: List[Dict[str, Any]],
        filepath: str
    ) -> None:
        """Export data to Parquet format (requires pandas/pyarrow)"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            df.to_parquet(filepath, index=False)
            
            logger.info(f"Exported {len(data)} records to {filepath}")
            
        except ImportError:
            logger.error("Pandas/PyArrow not installed for Parquet export")
            raise
        except Exception as e:
            logger.error(f"Error exporting to Parquet: {e}")
            raise
    
    @staticmethod
    def export(
        data: List[Dict[str, Any]],
        filepath: str,
        format: ExportFormat = ExportFormat.CSV
    ) -> None:
        """
        Export training data
        
        Args:
            data: List of records to export
            filepath: Output file path
            format: Export format (csv, json, parquet)
        """
        if format == ExportFormat.CSV:
            TrainingDataExporter.export_to_csv(data, filepath)
        elif format == ExportFormat.JSON:
            TrainingDataExporter.export_to_json(data, filepath)
        elif format == ExportFormat.PARQUET:
            TrainingDataExporter.export_to_parquet(data, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")


class ConversionPredictionDataset:
    """
    Builds training dataset for conversion prediction models
    
    Features:
    - Session engagement features
    - Customer value features
    - Store characteristics
    - Target: conversion (0/1)
    """
    
    @staticmethod
    def build_dataset(
        sessions: List[Dict[str, Any]],
        events_map: Dict[str, List[Dict[str, Any]]],  # session_id -> events
        conversions: Dict[str, bool],  # session_id -> converted
    ) -> List[Dict[str, Any]]:
        """Build conversion prediction training dataset"""
        dataset = []
        
        for session in sessions:
            session_id = session.get("id")
            events = events_map.get(session_id, [])
            
            # Extract features
            session_features = FeatureEngineer.extract_session_features(
                events, session
            )
            customer_features = FeatureEngineer.extract_customer_features(
                session.get("customer_data", {})
            )
            store_features = FeatureEngineer.extract_store_features(
                session.get("store_data", {})
            )
            
            # Combine features
            record = {
                **session_features,
                **customer_features,
                **store_features,
                "target_conversion": conversions.get(session_id, 0),
            }
            
            # Validate
            is_valid, _ = DataValidator.validate_feature_set(record)
            if is_valid:
                dataset.append(record)
        
        return dataset


class CartAbandonmentDataset:
    """
    Builds training dataset for cart abandonment recovery models
    
    Features:
    - Cart value and items
    - Customer engagement
    - Customer value (LTV)
    - Target: recovered (0/1)
    """
    
    @staticmethod
    def build_dataset(
        abandoned_carts: List[Dict[str, Any]],
        recoveries: Dict[str, bool],  # cart_id -> recovered
    ) -> List[Dict[str, Any]]:
        """Build cart recovery prediction training dataset"""
        dataset = []
        
        for cart in abandoned_carts:
            cart_id = cart.get("id")
            
            record = {
                "cart_value": cart.get("cart_value", 0),
                "item_count": len(cart.get("items", [])),
                "price_bucket": TrainingDataExporter._get_price_bucket(
                    cart.get("cart_value", 0)
                ),
                "customer_ltv": cart.get("customer_ltv", 0),
                "customer_orders": cart.get("customer_orders", 0),
                "customer_segment": cart.get("customer_segment", "unknown"),
                "time_since_abandon": cart.get("time_since_abandon", 0),
                "target_recovery": recoveries.get(cart_id, 0),
            }
            
            dataset.append(record)
        
        return dataset
    
    @staticmethod
    def _get_price_bucket(value: float) -> str:
        """Categorize cart value"""
        if value < 50:
            return "low"
        elif value < 150:
            return "medium"
        else:
            return "high"


class AgentPerformanceDataset:
    """
    Builds training dataset for agent performance analysis
    
    Features:
    - Agent action details
    - Session and customer context
    - Target: outcome (converted, engaged)
    """
    
    @staticmethod
    def build_dataset(
        agent_actions: List[Dict[str, Any]],
        outcomes: Dict[str, Dict[str, bool]],  # action_id -> {converted, engaged}
    ) -> List[Dict[str, Any]]:
        """Build agent performance training dataset"""
        dataset = []
        
        for action in agent_actions:
            action_id = action.get("id")
            outcome = outcomes.get(action_id, {})
            
            record = {
                "agent_type": action.get("agent_type"),
                "action_type": action.get("action"),
                "confidence": action.get("confidence", 0),
                "customer_ltv": action.get("customer_ltv", 0),
                "session_engagement": action.get("session_page_views", 0),
                "store_plan": action.get("store_plan"),
                "target_conversion": outcome.get("converted", 0),
                "target_engagement": outcome.get("engaged", 0),
            }
            
            dataset.append(record)
        
        return dataset
