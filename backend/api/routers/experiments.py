"""A/B experiment routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import secrets

from ..database import get_db
from ..config import EXPERIMENT_ID_PREFIX, DEFAULT_EXPERIMENT_STATUS
from ...models.models import Experiment

router = APIRouter()


class ExperimentCreate(BaseModel):
    name: str
    experiment_type: str
    control_variant: dict
    test_variants: List[dict]
    allocation: dict
    duration_days: int


class ExperimentResponse(BaseModel):
    id: str
    name: str
    experiment_type: str
    status: str
    winner: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/{store_id}", response_model=ExperimentResponse)
async def create_experiment(
    store_id: str,
    experiment: ExperimentCreate,
    db: Session = Depends(get_db)
):
    """Create an experiment"""
    exp_id = f"{EXPERIMENT_ID_PREFIX}{secrets.token_urlsafe(12)}"
    
    new_experiment = Experiment(
        id=exp_id,
        store_id=store_id,
        name=experiment.name,
        experiment_type=experiment.experiment_type,
        control_variant=experiment.control_variant,
        test_variants=experiment.test_variants,
        allocation=experiment.allocation,
        duration_days=experiment.duration_days,
        status=DEFAULT_EXPERIMENT_STATUS
    )
    
    db.add(new_experiment)
    db.commit()
    db.refresh(new_experiment)
    
    return ExperimentResponse.from_orm(new_experiment)


@router.get("/{store_id}", response_model=List[ExperimentResponse])
async def get_experiments(
    store_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get experiments for a store"""
    query = db.query(Experiment).filter(Experiment.store_id == store_id)
    
    if status:
        query = query.filter(Experiment.status == status)
    
    experiments = query.order_by(Experiment.created_at.desc()).all()
    
    return [ExperimentResponse.from_orm(e) for e in experiments]
