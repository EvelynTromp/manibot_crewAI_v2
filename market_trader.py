# market_trader.py
from analysis.market_analyzer import MarketAnalyzer
from core.manifold_client import ManifoldClient
from core.gpt_client import GPTClient
from utils.report_formatter import ReportFormatter
from utils.logger import get_logger
from config.settings import settings

from typing import Dict, List, Optional
from datetime import datetime
import asyncio

logger = get_logger(__name__)

class MarketTrader:
    """Unified trading system that handles both analysis and execution."""
    
    def __init__(self):
        """Initialize core components for trading."""
        self.manifold_client = ManifoldClient(api_key=settings.MANIFOLD_API_KEY)
        self.gpt_client = GPTClient(api_key=settings.OPENAI_API_KEY)
        # Pass the manifold client to the market analyzer
        self.market_analyzer = MarketAnalyzer(manifold_client=self.manifold_client)
        self.report_formatter = ReportFormatter()
        self._active_positions = []
        
    async def scan_markets(self, limit: int = 5) -> List[Dict]:
        """Scan markets for trading opportunities."""
        logger.info(f"Starting market scan for {limit} markets")
        self.report_formatter.start_session()
        
        try:
            markets = await self.manifold_client.get_markets(limit)
            logger.info(f"Found {len(markets)} markets to analyze")
            
            results = []
            for market in markets:
                try:
                    result = await self.analyze_and_trade(market['id'])
                    results.append(result)
                    await asyncio.sleep(settings.RATE_LIMIT_DELAY)
                except Exception as e:
                    logger.error(f"Error processing market {market['id']}: {str(e)}")
                    results.append({
                        "market_id": market['id'],
                        "success": False,
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in market scan: {str(e)}")
            return []
    
    async def analyze_and_trade(self, market_id: str) -> Dict:
        """Unified method for market analysis and trading."""
        execution_data = {
            "market_id": market_id,
            "success": False,
            "trade_executed": False,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            market_data = await self.manifold_client.get_market(market_id)
            execution_data["market_data"] = market_data
            
            analysis = await self.market_analyzer.analyze_market(market_data)
            execution_data["analysis"] = analysis
            
            if "error" in analysis:
                logger.warning(f"Analysis failed: {analysis['error']}")
                execution_data["error"] = analysis["error"]
                return execution_data
                    # Add binary market validation here
            # if market_data.get('outcomeType') != 'BINARY':
            #     logger.info(f"Skipping non-binary market {market_id}")
            #     execution_data["error"] = "Non-binary market type"
            #     return execution_data
            
            if bet_recommendation := analysis.get('bet_recommendation'):
                trade_result = await self._execute_trade(
                    market_id,
                    bet_recommendation,
                    market_data
                )
                
                execution_data.update(trade_result)
                if trade_result.get('success'):
                    execution_data['trade_executed'] = True
                    self._active_positions.append(trade_result['trade'])
            
            execution_data['success'] = True
            self.report_formatter.log_market_analysis(execution_data)
            
            return execution_data
            
        except Exception as e:
            logger.error(f"Error in analyze_and_trade: {str(e)}")
            execution_data["error"] = str(e)
            return execution_data
            
    
    async def _execute_trade(self, market_id: str, bet_details: Dict, market_data: Dict) -> Dict:
        """
        Execute a trade with comprehensive validation and error handling.
        
        Args:
            market_id: The ID of the market to trade on
            bet_details: Dictionary containing bet parameters
            market_data: Current market data
            
        Returns:
            Dict containing trade result or error information
        """
        try:
            # First validate all bet parameters
            if not await self.manifold_client.validate_bet_parameters(
                market_id, 
                bet_details['amount'], 
                bet_details['probability']
            ):
                return {
                    "success": False,
                    "error": "Failed bet parameter validation",
                    "market_id": market_id
                }
            
            # Log bet details for debugging
            logger.info(f"Executing trade for market {market_id}")
            logger.debug(f"Bet details: {json.dumps(bet_details, indent=2)}")
            
            # Prepare bet parameters
            bet_data = {
                "amount": bet_details['amount'],
                "probability": bet_details['probability'],
                "outcome": bet_details['direction']
            }
            
            # Place the bet
            try:
                bet_result = await self.manifold_client.place_bet(
                    market_id=market_id,
                    **bet_data
                )
                
                # Verify the bet was placed successfully
                if not bet_result:
                    raise ValueError("Empty response from Manifold API")
                    
                if 'id' not in bet_result:
                    logger.error(f"Invalid bet response: {json.dumps(bet_result, indent=2)}")
                    raise ValueError("No bet ID in response")
                    
                # Log successful bet
                logger.info(f"Successfully placed bet {bet_result['id']} on market {market_id}")
                
                return {
                    "success": True,
                    "trade": bet_result,
                    "market_id": market_id,
                    "bet_details": bet_data
                }
                
            except Exception as e:
                logger.error(f"API error during bet placement: {str(e)}")
                if hasattr(e, 'status'):
                    logger.error(f"HTTP Status: {e.status}")
                raise
                
        except Exception as e:
            error_details = {
                "success": False,
                "error": str(e),
                "market_id": market_id,
                "traceback": traceback.format_exc()
            }
            logger.error(f"Error executing trade: {str(e)}", exc_info=True)
            return error_details
        

        
    async def monitor_positions(self) -> List[Dict]:
        """Monitor active trading positions."""
        position_updates = []
        
        for position in self._active_positions:
            try:
                market = await self.manifold_client.get_market(position['market_id'])
                
                position_updates.append({
                    'bet_id': position['bet_id'],
                    'market_id': position['market_id'],
                    'original_probability': position['probability'],
                    'current_probability': market.get('probability'),
                    'is_resolved': market.get('isResolved', False),
                    'resolution': market.get('resolution'),
                    'profit_loss': self._calculate_pnl(position, market)
                })
                
            except Exception as e:
                logger.error(f"Error monitoring position: {str(e)}")
                
        return position_updates
    
    def _calculate_pnl(self, position: Dict, current_market: Dict) -> float:
        """Calculate profit/loss for a position."""
        if current_market.get('isResolved'):
            resolution = current_market.get('resolution')
            if resolution:
                if (resolution == 'YES' and position['outcome'] == 'YES') or \
                   (resolution == 'NO' and position['outcome'] == 'NO'):
                    return position['amount'] * (1 / position['probability'] - 1)
                return -position['amount']
        
        current_prob = float(current_market.get('probability', 0))
        return position['amount'] * (current_prob - position['probability'])