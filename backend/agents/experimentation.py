"""Experimentation Agent - Automated A/B testing with MAB algorithm"""
from typing import Dict, Any, List
import random
import math
from backend.api.config import (
    OPTIMAL_AGENT_CONFIDENCE,
    MIN_AGENT_CONFIDENCE
)


class ExperimentationAgent:
    """
    Runs automated experiments and optimizes based on results
    
    Algorithms:
    - Multi-armed bandits (Thompson sampling)
    - Reinforcement learning
    
    Experiments:
    - Discount sizes (5%, 10%, 15%, 20%)
    - Checkout copy (different messages)
    - Persuasion timing (when to show offers)
    - Offer types (discount vs free shipping)
    """
    
    def __init__(self, inference_client):
        self.inference_client = inference_client
        self.agent_type = "experimentation"
    
    async def select_variant(self, experiment_id: str, customer_id: str) -> Dict[str, Any]:
        """
        Select best variant for this customer using multi-armed bandit
        
        Uses Thompson sampling to balance exploration/exploitation
        """
        
        # Get experiment config
        experiment = await self.inference_client.predict(
            "experiment",
            {"experiment_id": experiment_id}
        )
        
        variants = experiment.get("variants", [])
        if not variants:
            return {"variant": None, "reason": "No variants available"}
        
        # Try Thompson sampling (ML-based)
        ml_result = self._thompson_sample_ml(variants)
        
        # If ML confidence >= 90%, use it
        if ml_result.get("confidence", 0) >= 0.9:
            return {
                "agent_type": self.agent_type,
                "experiment_id": experiment_id,
                "customer_id": customer_id,
                "selected_variant": ml_result["name"],
                "variant_config": ml_result,
                "confidence": ml_result.get("confidence", MIN_AGENT_CONFIDENCE),
                "source": "ml"
            }
        
        # Fallback to heuristic-based selection
        heuristic_result = self._select_variant_heuristic(variants)
        return {
            "agent_type": self.agent_type,
            "experiment_id": experiment_id,
            "customer_id": customer_id,
            "selected_variant": heuristic_result["name"],
            "variant_config": heuristic_result,
            "confidence": heuristic_result.get("confidence", MIN_AGENT_CONFIDENCE),
            "source": "heuristic"
        }
    
    def _thompson_sample_ml(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Thompson sampling for bandit optimization (ML-based)"""
        
        samples = []
        for variant in variants:
            # Beta distribution sampling
            # Where alpha = successes, beta = failures
            successes = variant.get("conversions", 0) + 1
            failures = variant.get("trials", 0) - variant.get("conversions", 0) + 1
            
            # Sample from beta distribution
            sample = random.betavariate(successes, failures)
            samples.append((sample, variant))
        
        # Return variant with highest sample
        selected = max(samples, key=lambda x: x[0])[1]
        selected["confidence"] = OPTIMAL_AGENT_CONFIDENCE
        return selected
    
    def _select_variant_heuristic(self, variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Heuristic-based variant selection - rule-based fallback
        
        Heuristic: Contextual Bandit approach
        - High trials (>100): Use empirical conversion rate (data-driven)
        - Low trials (<10): Explore equally (reduce cold-start bias)
        - Medium trials: Balance (70% exploitation, 30% exploration)
        - New variants: Give equal treatment (avoid bias)
        
        Confidence: 0.65-0.75 (heuristic-based, less optimal than Thompson)
        """
        
        # Separate variants by data maturity
        high_data = [v for v in variants if v.get("trials", 0) >= 100]
        med_data = [v for v in variants if 10 <= v.get("trials", 0) < 100]
        low_data = [v for v in variants if v.get("trials", 0) < 10]
        
        selected = None
        confidence = 0.65
        
        # Rule 1: High-data variants - use empirical conversion rate
        if high_data:
            selected = max(high_data, key=lambda v: v.get("conversions", 0) / max(v.get("trials", 1), 1))
            confidence = 0.80  # High confidence - plenty of data
        
        # Rule 2: Medium-data variants - mostly exploit, slight explore
        elif med_data:
            conversion_rates = [v.get("conversions", 0) / max(v.get("trials", 1), 1) for v in med_data]
            best_idx = conversion_rates.index(max(conversion_rates))
            
            # 70% chance pick best, 30% chance pick random (exploration)
            if random.random() < 0.7:
                selected = med_data[best_idx]
            else:
                selected = random.choice(med_data)
            confidence = 0.70  # Medium confidence
        
        # Rule 3: Low/new data variants - equal distribution (pure exploration)
        else:
            selected = random.choice(variants) if variants else None
            confidence = 0.60  # Lower confidence - insufficient data
        
        if selected:
            selected["confidence"] = confidence
            return selected
        
        # Fallback: random if no variants
        return {"name": "default", "confidence": 0.5}
    
    
    async def run_experiment(self, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a new experiment"""
        
        return {
            "agent_type": self.agent_type,
            "experiment_id": experiment_config.get("id"),
            "status": "running",
            "variants": experiment_config.get("variants", []),
            "sample_size_per_variant": experiment_config.get("duration_days", 7) * 100,
            "confidence": OPTIMAL_AGENT_CONFIDENCE
        }
