"""Agent decision and monitoring routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..config import DEFAULT_QUERY_LIMIT
from ...models.models import AgentAction

router = APIRouter()


class AgentDecisionResponse(BaseModel):
    id: str
    agent_type: str
    action: str
    action_details: dict
    confidence: float
    created_at: str

    class Config:
        from_attributes = True


@router.get("/decisions/{store_id}", response_model=List[AgentDecisionResponse])
async def get_agent_decisions(
    store_id: str,
    agent_type: Optional[str] = None,
    limit: int = DEFAULT_QUERY_LIMIT,
    db: Session = Depends(get_db)
):
    """Get agent decisions for a store"""
    query = db.query(AgentAction).filter(AgentAction.store_id == store_id)
    
    if agent_type:
        query = query.filter(AgentAction.agent_type == agent_type)
    
    decisions = query.order_by(AgentAction.created_at.desc()).limit(limit).all()
    
    return [AgentDecisionResponse.from_orm(d) for d in decisions]


@router.get("/stats/{store_id}")
async def get_agent_stats(store_id: str, db: Session = Depends(get_db)):
    """Get agent performance statistics"""
    actions = db.query(AgentAction).filter(AgentAction.store_id == store_id).all()
    
    if not actions:
        return {
            "total_decisions": 0,
            "executed": 0,
            "delivered": 0,
            "converted": 0,
            "conversion_rate": 0,
            "avg_confidence": 0
        }
    
    executed = sum(1 for a in actions if a.executed)
    delivered = sum(1 for a in actions if a.delivered)
    converted = sum(1 for a in actions if a.converted)
    
    return {
        "total_decisions": len(actions),
        "executed": executed,
        "delivered": delivered,
        "converted": converted,
        "conversion_rate": converted / len(actions) if actions else 0,
        "avg_confidence": sum(a.confidence for a in actions) / len(actions) if actions else 0,
        "by_agent_type": {
            agent_type: sum(1 for a in actions if a.agent_type == agent_type)
            for agent_type in set(a.agent_type for a in actions if a.agent_type)
        }
    }
