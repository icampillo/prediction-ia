import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))

from src.indicators.taapi_client import TAAPIClient
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class IndicatorService:
    def __init__(self):
        self.taapi = TAAPIClient()
    
    def round_or_none(self, val, decimals=2):
        """Arrondir une valeur ou retourner None"""
        try:
            return round(float(val), decimals) if val is not None else None
        except (ValueError, TypeError):
            return None
    
    def round_series(self, series: List, decimals=2):
        """Arrondir une série de valeurs"""
        if not series:
            return []
        return [self.round_or_none(v, decimals) for v in series]
    
    async def fetch_indicators(self, asset: str, interval: str = "1h") -> Dict:
        """Récupère tous les indicateurs pour un asset"""
        try:
            logger.info(f"Fetching indicators for {asset} at {interval}")
            
            # Indicateurs intraday (5m)
            intraday_tf = "5m"
            ema_series = self.taapi.fetch_series(
                "ema", f"{asset}/USDT", intraday_tf, 
                results=10, params={"period": 20}, value_key="value"
            )
            macd_series = self.taapi.fetch_series(
                "macd", f"{asset}/USDT", intraday_tf, 
                results=10, value_key="valueMACD"
            )
            rsi7_series = self.taapi.fetch_series(
                "rsi", f"{asset}/USDT", intraday_tf, 
                results=10, params={"period": 7}, value_key="value"
            )
            rsi14_series = self.taapi.fetch_series(
                "rsi", f"{asset}/USDT", intraday_tf, 
                results=10, params={"period": 14}, value_key="value"
            )
            
            # Indicateurs long terme (4h)
            lt_ema20 = self.taapi.fetch_value(
                "ema", f"{asset}/USDT", "4h", 
                params={"period": 20}, key="value"
            )
            lt_ema50 = self.taapi.fetch_value(
                "ema", f"{asset}/USDT", "4h", 
                params={"period": 50}, key="value"
            )
            lt_atr3 = self.taapi.fetch_value(
                "atr", f"{asset}/USDT", "4h", 
                params={"period": 3}, key="value"
            )
            lt_atr14 = self.taapi.fetch_value(
                "atr", f"{asset}/USDT", "4h", 
                params={"period": 14}, key="value"
            )
            lt_macd_series = self.taapi.fetch_series(
                "macd", f"{asset}/USDT", "4h", 
                results=10, value_key="valueMACD"
            )
            lt_rsi_series = self.taapi.fetch_series(
                "rsi", f"{asset}/USDT", "4h", 
                results=10, params={"period": 14}, value_key="value"
            )
            
            return {
                "asset": asset,
                "intraday": {
                    "ema20": self.round_or_none(ema_series[-1]) if ema_series else None,
                    "macd": self.round_or_none(macd_series[-1]) if macd_series else None,
                    "rsi7": self.round_or_none(rsi7_series[-1]) if rsi7_series else None,
                    "rsi14": self.round_or_none(rsi14_series[-1]) if rsi14_series else None,
                    "series": {
                        "ema20": self.round_series(ema_series),
                        "macd": self.round_series(macd_series),
                        "rsi7": self.round_series(rsi7_series),
                        "rsi14": self.round_series(rsi14_series)
                    }
                },
                "long_term": {
                    "ema20": self.round_or_none(lt_ema20),
                    "ema50": self.round_or_none(lt_ema50),
                    "atr3": self.round_or_none(lt_atr3),
                    "atr14": self.round_or_none(lt_atr14),
                    "macd_series": self.round_series(lt_macd_series),
                    "rsi_series": self.round_series(lt_rsi_series)
                }
            }
        except Exception as e:
            logger.error(f"Error fetching indicators for {asset}: {e}")
            return {
                "asset": asset,
                "error": str(e),
                "intraday": {},
                "long_term": {}
            }