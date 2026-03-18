"""Billing and subscription routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ...models.models import Store, BillingEvent

router = APIRouter()


class BillingResponse(BaseModel):
    current_plan: str
    subscription_status: str
    stripe_customer_id: str
    usage: dict


@router.get("/{store_id}", response_model=BillingResponse)
async def get_billing_info(
    store_id: str,
    db: Session = Depends(get_db)
):
    """Get billing information for a store"""
    store = db.query(Store).filter(Store.id == store_id).first()
    
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    # Get usage metrics for current month
    from datetime import date
    first_day_of_month = date.today().replace(day=1)
    
    usage_events = db.query(BillingEvent).filter(
        BillingEvent.store_id == store_id,
        BillingEvent.created_at >= first_day_of_month
    ).all()
    
    usage = {}
    for event in usage_events:
        usage[event.event_type] = usage.get(event.event_type, 0) + event.metric_value
    
    return BillingResponse(
        current_plan=store.plan,
        subscription_status=store.subscription_status,
        stripe_customer_id=store.stripe_customer_id or "",
        usage=usage
    )
