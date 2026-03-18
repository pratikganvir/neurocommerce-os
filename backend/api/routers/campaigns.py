"""Campaign management routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import secrets

from ..database import get_db
from ..config import CAMPAIGN_ID_PREFIX
from ...models.models import Campaign

router = APIRouter()


class CampaignCreate(BaseModel):
    name: str
    campaign_type: str  # cart_recovery, replenishment, cross_sell
    target_segment: Optional[str] = None
    channels: List[str]  # email, sms, whatsapp, push
    message_template: str


class CampaignResponse(BaseModel):
    id: str
    name: str
    campaign_type: str
    status: str
    sent_count: int
    converted_count: int
    revenue_generated: float
    created_at: str

    class Config:
        from_attributes = True


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    store_id: str,
    campaign: CampaignCreate,
    db: Session = Depends(get_db)
):
    """Create a new campaign"""
    campaign_id = f"{CAMPAIGN_ID_PREFIX}{secrets.token_urlsafe(12)}"
    
    new_campaign = Campaign(
        id=campaign_id,
        store_id=store_id,
        name=campaign.name,
        campaign_type=campaign.campaign_type,
        target_segment=campaign.target_segment,
        channels=campaign.channels,
        message_template=campaign.message_template,
        status="draft"
    )
    
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    
    return CampaignResponse.from_orm(new_campaign)


@router.get("/{store_id}", response_model=List[CampaignResponse])
async def get_campaigns(
    store_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get campaigns for a store"""
    query = db.query(Campaign).filter(Campaign.store_id == store_id)
    
    if status:
        query = query.filter(Campaign.status == status)
    
    campaigns = query.order_by(Campaign.created_at.desc()).all()
    
    return [CampaignResponse.from_orm(c) for c in campaigns]
