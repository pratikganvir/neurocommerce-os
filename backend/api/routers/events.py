"""Event ingestion routes"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import secrets

from ..database import get_db
from ..cache import set_cache, get_cache
from ..config import EVENT_ID_PREFIX, MAX_BATCH_SIZE
from ...models.models import Event, Session as SessionModel, Customer, Cart
from ...services.event_processor import process_event
from ...services.kafka_producer import produce_event

router = APIRouter()


class EventData(BaseModel):
    event_type: str
    event_data: dict
    timestamp: Optional[datetime] = None


class BatchEventRequest(BaseModel):
    session_id: str
    customer_id: Optional[str] = None
    events: List[EventData]
    metadata: Optional[dict] = None


class EventResponse(BaseModel):
    event_id: str
    status: str


@router.post("/batch", response_model=List[EventResponse])
async def ingest_events(
    request: BatchEventRequest,
    api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Ingest batch of events from tracking SDK
    
    This endpoint receives events from the JavaScript SDK and:
    1. Validates API key
    2. Creates event records
    3. Publishes to Kafka for async processing
    4. Triggers real-time agents if needed
    """
    
    # Verify API key
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    from ..security import verify_api_key
    store_id = verify_api_key(api_key, db)
    if not store_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get or create session
    session = db.query(SessionModel).filter(
        SessionModel.id == request.session_id,
        SessionModel.store_id == store_id
    ).first()
    
    if not session:
        session = SessionModel(
            id=request.session_id,
            store_id=store_id,
            customer_id=request.customer_id,
            start_time=datetime.utcnow()
        )
        db.add(session)
        db.commit()
    
    # Update customer ID if provided
    if request.customer_id and not session.customer_id:
        session.customer_id = request.customer_id
        db.commit()
    
    # Process events
    results = []
    for event_data in request.events:
        event_id = f"{EVENT_ID_PREFIX}{secrets.token_urlsafe(12)}"
        
        # Create event record
        event = Event(
            id=event_id,
            session_id=request.session_id,
            event_type=event_data.event_type,
            event_data=event_data.event_data,
            created_at=event_data.timestamp or datetime.utcnow()
        )
        
        db.add(event)
        
        # Publish to Kafka for async processing
        produce_event({
            "event_id": event_id,
            "session_id": request.session_id,
            "store_id": store_id,
            "customer_id": request.customer_id,
            "event_type": event_data.event_type,
            "event_data": event_data.event_data,
            "timestamp": (event_data.timestamp or datetime.utcnow()).isoformat()
        })
        
        results.append(EventResponse(event_id=event_id, status="queued"))
    
    db.commit()
    
    return results


@router.post("/track", response_model=EventResponse)
async def track_event(
    event: EventData,
    session_id: str,
    api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Track a single event
    """
    
    # Verify API key
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    from ..security import verify_api_key
    store_id = verify_api_key(api_key, db)
    if not store_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    event_id = f"{EVENT_ID_PREFIX}{secrets.token_urlsafe(12)}"
    
    # Create event
    db_event = Event(
        id=event_id,
        session_id=session_id,
        event_type=event.event_type,
        event_data=event.event_data,
        created_at=event.timestamp or datetime.utcnow()
    )
    
    db.add(db_event)
    db.commit()
    
    # Publish to Kafka
    produce_event({
        "event_id": event_id,
        "session_id": session_id,
        "store_id": store_id,
        "event_type": event.event_type,
        "event_data": event.event_data,
        "timestamp": (event.timestamp or datetime.utcnow()).isoformat()
    })
    
    return EventResponse(event_id=event_id, status="queued")
