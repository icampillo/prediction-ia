from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/crypto_predictions")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    asset = Column(String, index=True)
    interval = Column(String)
    
    # Market data
    current_price = Column(Float)
    market_data = Column(JSON)  # Tous les indicateurs
    
    # AI Reasoning
    reasoning = Column(Text)
    action = Column(String)  # buy, sell, hold
    allocation_usd = Column(Float, nullable=True)
    tp_price = Column(Float, nullable=True)
    sl_price = Column(Float, nullable=True)
    exit_plan = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Account state
    account_balance = Column(Float)
    total_return_pct = Column(Float, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

# ===== app/models/schemas.py =====
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class PredictionRequest(BaseModel):
    assets: List[str] = Field(..., description="Liste des cryptos (ex: ['BTC', 'ETH'])")
    interval: str = Field(default="1h", description="Intervalle de temps (5m, 1h, 4h, 1d)")

class MarketData(BaseModel):
    asset: str
    current_price: Optional[float] = None
    intraday: Optional[dict] = None
    long_term: Optional[dict] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    funding_annualized_pct: Optional[float] = None

class TradeDecision(BaseModel):
    asset: str
    action: str  # buy, sell, hold
    allocation_usd: Optional[float] = None
    tp_price: Optional[float] = None
    sl_price: Optional[float] = None
    exit_plan: Optional[str] = None
    rationale: Optional[str] = None
    confidence: Optional[float] = None

class PredictionResponse(BaseModel):
    timestamp: datetime
    reasoning: str
    trade_decisions: List[TradeDecision]
    market_data: List[MarketData]

class HistoryResponse(BaseModel):
    id: int
    timestamp: datetime
    asset: str
    action: str
    reasoning: str
    current_price: Optional[float]
    confidence: Optional[float]