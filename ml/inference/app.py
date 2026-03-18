"""
Inference Service for real-time ML predictions
"""
from fastapi import FastAPI
from typing import Dict, Any
import pickle
import os
import numpy as np
from redis import Redis

app = FastAPI(title="NeuroCommerce Inference Service")

# Load models
MODELS_DIR = os.getenv("MODELS_DIR", "/models")
models = {}

def load_models():
    """Load trained models from disk"""
    global models
    
    try:
        # Load behavior prediction model
        with open(f"{MODELS_DIR}/behavior_model.pkl", "rb") as f:
            models["behavior"] = pickle.load(f)
        
        # Load recommendation model
        with open(f"{MODELS_DIR}/recommendation_model.pkl", "rb") as f:
            models["recommendation"] = pickle.load(f)
        
        # Load churn prediction model
        with open(f"{MODELS_DIR}/churn_model.pkl", "rb") as f:
            models["churn"] = pickle.load(f)
        
        print("Models loaded successfully")
    except Exception as e:
        print(f"Failed to load models: {e}")

# Initialize on startup
load_models()

# Redis cache
redis_client = Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=1)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "models_loaded": len(models) > 0}


@app.post("/predict/behavior")
async def predict_behavior(features: Dict[str, Any]):
    """
    Predict purchase probability, abandonment risk, and intent class
    
    Features:
    - page_views: int
    - product_views: int
    - scroll_depth: float
    - time_on_site: float
    - device: str
    - traffic_source: str
    """
    
    if "behavior" not in models:
        return {"error": "Behavior model not loaded"}
    
    try:
        model = models["behavior"]
        
        # Feature engineering
        X = np.array([[
            features.get("page_views", 0),
            features.get("product_views", 0),
            features.get("scroll_depth", 0),
            features.get("time_on_site", 0),
            1 if features.get("device") == "mobile" else 0,
            1 if features.get("traffic_source") == "organic" else 0
        ]])
        
        # Predict
        probs = model.predict_proba(X)[0]
        
        return {
            "purchase_probability": float(probs[1]),
            "abandonment_probability": 1.0 - float(probs[1]),
            "intent_class": "high" if probs[1] > 0.7 else ("medium" if probs[1] > 0.4 else "low"),
            "confidence": float(max(probs))
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/predict/recommendations")
async def predict_recommendations(product_id: str):
    """
    Get product recommendations based on embeddings
    """
    
    if "recommendation" not in models:
        return {"error": "Recommendation model not loaded"}
    
    try:
        # Check cache
        cached = redis_client.get(f"recs:{product_id}")
        if cached:
            import json
            return json.loads(cached)
        
        model = models["recommendation"]
        
        # Get similar products
        recommendations = model.get_similar(product_id, n=5)
        
        result = {
            "product_ids": recommendations,
            "confidence": 0.75
        }
        
        # Cache result
        import json
        redis_client.setex(f"recs:{product_id}", 86400, json.dumps(result))
        
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/predict/churn")
async def predict_churn(customer_data: Dict[str, Any]):
    """
    Predict customer churn risk
    """
    
    if "churn" not in models:
        return {"error": "Churn model not loaded"}
    
    try:
        model = models["churn"]
        
        X = np.array([[
            customer_data.get("lifetime_value", 0),
            customer_data.get("days_since_purchase", 0),
            customer_data.get("purchase_frequency", 0),
            customer_data.get("avg_order_value", 0),
            customer_data.get("support_tickets", 0)
        ]])
        
        churn_prob = model.predict_proba(X)[0][1]
        
        return {
            "churn_probability": float(churn_prob),
            "confidence": float(max(model.predict_proba(X)[0]))
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
