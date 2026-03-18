# Agent Heuristics - Quick Reference

**Date:** March 15, 2026  
**Status:** ✅ COMPLETE

---

## Architecture

```
┌─────────────────────────────────────────┐
│           Agent Request                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Try ML Prediction   │
        │ (inference_client)   │
        └──────┬───────────────┘
               │
               ▼
    ┌──────────────────────────┐
    │ Confidence >= 90% ?       │
    └───┬────────────────┬──────┘
        │ YES            │ NO
        ▼                ▼
    ┌────────┐    ┌──────────────────┐
    │ Return │    │ Try Heuristic    │
    │   ML   │    │ (rule-based)     │
    │Result  │    └──────┬───────────┘
    └────────┘           │
                         ▼
                   ┌───────────────┐
                   │ Return        │
                   │ Heuristic     │
                   │ Result        │
                   └───────────────┘
```

---

## Agents & Their Heuristics

### 1️⃣ Checkout Persuasion
**When:** Confidence < 90%  
**Heuristic:** Cart value segmentation  

| Cart Value | Action | Confidence |
|-----------|--------|-----------|
| < $50 | Free shipping | 0.70 |
| $50-150 | Discount coupon | 0.65-0.75 |
| > $150 | Bundle/upsell | 0.75 |

---

### 2️⃣ Retention
**When:** Confidence < 90%  
**Heuristic:** Customer lifecycle stages  

| Segment | Action | Confidence |
|---------|--------|-----------|
| VIP (LTV > $500) | Loyalty | 0.75 |
| Repeat (30-90d) | Replenishment | 0.70 |
| Churned (90+ d) | Win-back | 0.80 |
| Default | Cross-sell | 0.65 |

---

### 3️⃣ Pricing Optimization
**When:** Confidence < 90%  
**Heuristic:** Price elasticity formula  

```
Discount = Base + Abandonment - LTV - CartSize
          ├─ New customer base: 12%
          ├─ + High abandon: (prob - 0.7) * 50
          ├─ - High LTV > $500: up to -10%
          └─ - High cart > $300: up to -30%
```

**Result:** 0-35% discount, confidence 0.70-0.80

---

### 4️⃣ Cart Recovery
**When:** Confidence < 90%  
**Heuristic:** 3-touch email/SMS sequence  

| Touch | Timing | Channel | Discount | Confidence |
|-------|--------|---------|----------|-----------|
| 1 | 1-2h | Email | 0-10% | 0.75 |
| 2 | 24h | Email/SMS | 10-15% | 0.80 |
| 3 | 72h | SMS | 15-20% | 0.85 |

---

### 5️⃣ Experimentation
**When:** Confidence < 90%  
**Heuristic:** Contextual bandit exploration/exploitation  

| Data Level | Strategy | Confidence |
|-----------|----------|-----------|
| High (100+) | Exploit best | 0.80 |
| Medium (10-100) | 70% best + 30% explore | 0.70 |
| Low (<10) | Random | 0.60 |

---

### 6️⃣ Recommendation
**When:** Confidence < 90%  
**Heuristic:** Layered product discovery  

```
Layer 1: Frequently Bought Together    (conf 0.70)
Layer 2: Category Best-Sellers         (conf 0.65)
Layer 3: Price-Based Upsell            (conf 0.70)
Layer 4: Browsing History (fallback)   (conf 0.50)
```

**Result:** 3-5 products, confidence 0.65-0.75

---

### 7️⃣ Behavior Intelligence
**When:** Confidence < 90%  
**Heuristic:** Engagement signal scoring  

```
Purchase Intent = 
  (page_views * 0.1) +
  (product_views * 0.15) +
  (scroll_depth * 0.2) +
  (time_on_site / 300 * 0.2) +
  (has_cart * 0.2)

Abandonment = 
  quick_exit +
  device_friction +
  traffic_source_signal
```

**Result:** Confidence 0.70-0.80

---

## Key Implementation Code

```python
# Pattern used in ALL agents:

async def decision_method(self, data):
    # Tier 1: ML-based
    ml_result = await self._method_ml(data)
    if ml_result.get("confidence", 0) >= 0.9:
        return ml_result
    
    # Tier 2: Heuristic-based fallback
    return self._method_heuristic(data)


# Response format:
{
    "agent_type": "checkout_persuasion",
    "action": "...",
    "confidence": 0.72,
    "source": "heuristic",  # or "ml"
    "reasoning": "..."
}
```

---

## Confidence Levels

```
0.90-1.00: Use ML result
0.80-0.90: Good heuristic (use with confidence)
0.70-0.80: Moderate heuristic (reasonable)
0.60-0.70: Lower confidence heuristic (fallback)
< 0.60:   Very low confidence (need more data)
```

---

## Environment Usage

### Development
- Limited ML training data
- Heuristics: 40-60% of decisions
- Good for testing agent behavior
- Fast iteration without models

### Production  
- ML models fully trained
- Heuristics: 5-20% of decisions
- Only for edge cases/new scenarios
- Better accuracy overall

---

## Monitoring

**Track these metrics:**

```python
# Per agent, per heuristic:
metrics = {
    "heuristic_usage_rate": 0.15,      # % time using heuristic
    "heuristic_conversion": 0.05,      # Conversion rate
    "heuristic_revenue_per_user": 1.20,
    
    "ml_usage_rate": 0.80,
    "ml_conversion": 0.08,
    "ml_revenue_per_user": 1.50,
    
    "source_breakdown": {
        "ml": 0.80,
        "heuristic": 0.15,
        "fallback": 0.05
    }
}
```

---

## Testing

```python
# Unit test example
def test_checkout_heuristic():
    agent = CheckoutPersuasionAgent(None)
    result = agent._select_tactic_heuristic(
        cart_value=45,
        session_data={"customer_segment": "new"}
    )
    
    assert result["action"] == "free_shipping"
    assert result["source"] == "heuristic"
    assert result["confidence"] == 0.70
```

---

## Research Sources

| Topic | Source |
|-------|--------|
| Persuasion | Cialdini "Influence" |
| Ecommerce | Baymard Institute |
| Pricing | McKinsey + MIT |
| Cart Recovery | Baymard (10-30% recovery) |
| SMS | SMS metrics (98% open) |
| Recommendations | Amazon/Netflix papers |
| Behavior | Nielsen/Qualtrics |

---

## Common Patterns

### Pattern 1: Low Confidence Handling
```python
# When ML isn't confident
if ml_confidence < 0.9:
    use_heuristic = True
    # Provides backup decision
```

### Pattern 2: Confidence Boost
```python
# High-LTV customer → increase confidence
if ltv > 500:
    confidence += 0.05
```

### Pattern 3: Multi-layered Fallback
```python
# Recommendation: Try 4 layers before giving up
try_fbt()           # Layer 1
try_bestsellers()   # Layer 2
try_upsell()        # Layer 3
try_browsing_hist() # Layer 4
```

### Pattern 4: Source Tracking
```python
# Always include source in response
return {
    "result": ...,
    "confidence": 0.72,
    "source": "heuristic",  # Enables debugging
}
```

---

## Quick Wins

✅ Add heuristics when:
- ML confidence < 90%
- New agent or scenario
- Edge cases/cold starts
- Model unavailable

✅ Monitor heuristics:
- Track usage rate
- Compare conversion vs ML
- Adjust threshold if outperforming

✅ Improve heuristics:
- A/B test variations
- Learn from data
- Update based on season/segment

---

## Next Steps

1. **Deploy & Monitor**
   - Track heuristic performance
   - Log source of decisions
   - Monitor confidence scores

2. **Iterate**
   - Adjust 90% threshold if needed
   - Add domain-specific rules
   - Experiment with combinations

3. **Evolve**
   - Learn heuristics from data
   - Ensemble ML + heuristic
   - Build confidence over time

---

## File Locations

```
/backend/agents/
├── checkout_persuasion.py      (Psychology-based)
├── retention.py                (Lifecycle-based)
├── pricing_optimization.py     (Elasticity-based)
├── cart_recovery.py           (Baymard-based)
├── experimentation.py         (Contextual bandit)
├── recommendation.py          (Layered discovery)
└── behavior_intelligence.py   (Signal-based)

/docs/
├── AGENT_HEURISTICS.md        (Complete reference)
└── AGENT_HEURISTICS_COMPLETE.md (Summary)
```

---

**Status:** ✅ PRODUCTION READY

All agents have research-backed heuristics for reliable decisions when ML confidence < 90%.
