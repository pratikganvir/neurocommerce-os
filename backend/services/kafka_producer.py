"""Kafka producer for publishing events"""
import os
import json
from kafka import KafkaProducer
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Initialize Kafka producer
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")

kafka_producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',
    retries=3
)


def produce_event(event: Dict[str, Any], topic: str = "user_behavior_events"):
    """
    Publish event to Kafka
    
    Args:
        event: Event data dictionary
        topic: Kafka topic name
    """
    try:
        future = kafka_producer.send(topic, value=event)
        record_metadata = future.get(timeout=10)
        logger.debug(f"Event published to {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
    except Exception as e:
        logger.error(f"Failed to produce event: {e}")


def produce_shopify_event(event: Dict[str, Any]):
    """Publish Shopify webhook event"""
    produce_event(event, topic="shopify_events")


def produce_agent_action(action: Dict[str, Any]):
    """Publish agent action decision"""
    produce_event(action, topic="agent_actions")


def produce_conversion_event(event: Dict[str, Any]):
    """Publish conversion event"""
    produce_event(event, topic="conversion_events")
