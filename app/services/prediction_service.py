import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))

from src.agents.agent import TradingAgent
from app.database import SessionLocal, Prediction
from app.services.indicator_service import IndicatorService
from datetime import datetime
import json
import logging
import os

logger = logging.getLogger(__name__)

class PredictionService:
    def __init__(self):
        self.agent = TradingAgent()
        self.indicator_service = IndicatorService()
        self.default_balance = float(os.getenv("DEFAULT_BALANCE", 100.0))
    
    async def generate_predictions(self, assets: List[str], interval: str = "1h"):
        """Génère des prédictions pour une liste d'actifs"""
        
        # 1. Récupérer les indicateurs pour tous les assets
        market_sections = []
        for asset in assets:
            indicators = await self.indicator_service.fetch_indicators(asset, interval)
            market_sections.append(indicators)
        
        # 2. Construire le contexte pour l'IA
        context_payload = {
            "account": {
                "balance": self.default_balance,
                "account_value": self.default_balance,
                "total_return_pct": 0.0,
                "positions": []
            },
            "market_data": market_sections,
            "instructions": {
                "assets": assets,
                "requirement": "Analyze market data and provide trade decisions in JSON format."
            }
        }
        
        context = json.dumps(context_payload)
        
        # 3. Appeler l'agent IA
        try:
            outputs = self.agent.decide_trade(assets, context)
            
            if not isinstance(outputs, dict):
                logger.error(f"Invalid output format: {outputs}")
                outputs = {"reasoning": "Error", "trade_decisions": []}
            
            reasoning = outputs.get("reasoning", "")
            trade_decisions = outputs.get("trade_decisions", [])
            
        except Exception as e:
            logger.error(f"Agent error: {e}")
            reasoning = f"Error: {str(e)}"
            trade_decisions = []
        
        # 4. Sauvegarder dans la DB
        db = SessionLocal()
        try:
            for decision in trade_decisions:
                asset = decision.get("asset")
                market_data = next((m for m in market_sections if m["asset"] == asset), {})
                
                prediction = Prediction(
                    timestamp=datetime.utcnow(),
                    asset=asset,
                    interval=interval,
                    current_price=market_data.get("current_price"),
                    market_data=market_data,
                    reasoning=reasoning,
                    action=decision.get("action", "hold"),
                    allocation_usd=decision.get("allocation_usd"),
                    tp_price=decision.get("tp_price"),
                    sl_price=decision.get("sl_price"),
                    exit_plan=decision.get("exit_plan"),
                    rationale=decision.get("rationale"),
                    confidence=decision.get("confidence"),
                    account_balance=self.default_balance,
                    total_return_pct=0.0
                )
                db.add(prediction)
            
            db.commit()
            logger.info(f"Saved {len(trade_decisions)} predictions to database")
        except Exception as e:
            logger.error(f"Database error: {e}")
            db.rollback()
        finally:
            db.close()
        
        return {
            "timestamp": datetime.utcnow(),
            "reasoning": reasoning,
            "trade_decisions": trade_decisions,
            "market_data": market_sections
        }