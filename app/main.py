from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import (
    PredictionRequest, PredictionResponse, HistoryResponse
)
from app.services.prediction_service import PredictionService
from app.database import init_db, SessionLocal, Prediction
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Crypto Prediction API",
    description="API de prédictions de trading crypto avec IA",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la DB au démarrage
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")

prediction_service = PredictionService()

@app.get("/")
async def root():
    return {
        "message": "Crypto Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/api/v1/predict",
            "history": "/api/v1/history/{asset}",
            "health": "/health"
        }
    }

@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Génère des prédictions pour une liste de cryptos
    
    Exemple:
    ```json
    {
        "assets": ["BTC", "ETH"],
        "interval": "1h"
    }
    ```
    """
    try:
        result = await prediction_service.generate_predictions(
            request.assets, 
            request.interval
        )
        return result
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/history/{asset}", response_model=List[HistoryResponse])
async def get_history(
    asset: str,
    limit: int = Query(default=50, le=200)
):
    """
    Récupère l'historique des prédictions pour un asset
    """
    db = SessionLocal()
    try:
        predictions = db.query(Prediction)\
            .filter(Prediction.asset == asset)\
            .order_by(Prediction.timestamp.desc())\
            .limit(limit)\
            .all()
        
        return [
            {
                "id": p.id,
                "timestamp": p.timestamp,
                "asset": p.asset,
                "action": p.action,
                "reasoning": p.reasoning,
                "current_price": p.current_price,
                "confidence": p.confidence
            }
            for p in predictions
        ]
    finally:
        db.close()

@app.get("/api/v1/latest/{asset}")
async def get_latest(asset: str):
    """Récupère la dernière prédiction pour un asset"""
    db = SessionLocal()
    try:
        prediction = db.query(Prediction)\
            .filter(Prediction.asset == asset)\
            .order_by(Prediction.timestamp.desc())\
            .first()
        
        if not prediction:
            raise HTTPException(status_code=404, detail="No predictions found")
        
        return {
            "id": prediction.id,
            "timestamp": prediction.timestamp,
            "asset": prediction.asset,
            "action": prediction.action,
            "allocation_usd": prediction.allocation_usd,
            "tp_price": prediction.tp_price,
            "sl_price": prediction.sl_price,
            "rationale": prediction.rationale,
            "confidence": prediction.confidence,
            "current_price": prediction.current_price
        }
    finally:
        db.close()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "crypto-prediction-api"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
