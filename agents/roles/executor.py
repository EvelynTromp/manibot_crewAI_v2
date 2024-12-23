from crewai import Agent
from typing import Dict, List
from core.manifold_client import ManifoldClient
from utils.logger import get_logger
from config.settings import settings 
import json

logger = get_logger(__name__)

class ExecutorAgent(Agent):
    """Agent responsible for executing trades and managing positions."""

    def __init__(self):
        super().__init__(
            role='Market Executor',
            goal='Execute trading decisions efficiently and reliably',
            backstory="""You are a precise market executor responsible for 
            implementing trading decisions. Your focus is on executing trades 
            accurately while maintaining detailed records.""",
            verbose=True,
            allow_delegation=False
        )
        
        self._manifold_client = None
        self._active_bets = []
        self._user_info = None  # Add this to store user info
    
    @property
    async def user_info(self):
        """Lazy initialization of user information."""
        if self._user_info is None:
            try:
                self._user_info = await self.manifold_client._make_request("GET", "me")
                logger.info(f"Authenticated as Manifold user: {self._user_info.get('username')} (ID: {self._user_info.get('id')})")
            except Exception as e:
                logger.error(f"Failed to get user info: {str(e)}")
                self._user_info = {}
        return self._user_info

    @property
    def manifold_client(self):
        """Lazy initialization of manifold client."""
        if self._manifold_client is None:
            self._manifold_client = ManifoldClient(api_key=settings.MANIFOLD_API_KEY)
        return self._manifold_client
    
    

    @property
    def active_bets(self):
        """Access to active bets list."""
        if self._active_bets is None:
            self._active_bets = []
        return self._active_bets



    
    async def execute_trade(self, market_id: str, decision: Dict, research_data: Dict) -> Dict:
        """Execute trade with improved validation and logging."""
        try:
            market = research_data['market_data']
            
            # Get user info before attempting trade
            user_info = await self.user_info
            username = user_info.get('username', 'Unknown')
            user_id = user_info.get('id', 'Unknown')
            
            # Log the execution attempt with user context
            logger.info(f"Attempting trade as user {username} (ID: {user_id})")
                        
            # Validate market is tradeable
            if not self._is_market_tradeable(market):
                logger.warning(f"Market {market_id} is not tradeable")
                return {
                    "success": False,
                    "error": "Market is not currently tradeable",
                    "details": "Market validation failed"
                }
            
            # Get bet parameters
            bet_recommendation = decision.get('bet_recommendation')
            if not bet_recommendation:
                logger.warning("No bet recommendation provided")
                return {
                    "success": False,
                    "error": "No bet recommendation provided",
                    "details": "Missing bet parameters"
                }
            
            amount = bet_recommendation['amount']
            probability = bet_recommendation['probability']
            
            # Determine bet direction
            outcome = "YES" if probability > 0.5 else "NO"
            logger.info(f"Attempting bet: {amount}M @ {probability} on {outcome}")
            
            # Execute the trade
            bet_result = await self.manifold_client.place_bet(
                market_id=market_id,
                amount=amount,
                probability=probability,
                outcome=outcome
            )
            
            # Validate bet result
            if not bet_result.get('id'):
                logger.error("Bet placement failed - no bet ID received")
                return {
                    "success": False,
                    "error": "Bet placement failed",
                    "details": "No bet confirmation received"
                }
                
            # Log successful trade with details
            logger.info(f"Successfully executed trade: Bet ID {bet_result['id']}")
            logger.info(f"Trade details: {json.dumps(bet_result, indent=2)}")
            
            # Record the trade
            trade_record = self._record_trade(market_id, decision, bet_result)
            self._active_bets.append(trade_record)
            
            return {
                "success": True,
                "trade": trade_record,
                "bet_details": bet_result
            }
                
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "details": "Trade execution failed"
            }


    def _is_market_tradeable(self, market: Dict) -> bool:
        """Check if market is currently tradeable."""
        # Basic checks
        if market.get('isResolved', False) or market.get('isClosed', False):
            return False
            
        # For binary markets
        if market.get('outcomeType') == 'BINARY':
            return True
            
        # For multiple choice markets: currently not allowed
        
        if market.get('outcomeType') == 'MULTIPLE_CHOICE':
            return False
            #answers = market.get('answers', [])
            #return len(answers) > 0
            
        return True  # Default to allowing trades if we don't recognize the market type


    def _record_trade(self, market_id: str, decision: Dict, bet_result: Dict) -> Dict:
        """Record trade details for tracking."""
        return {
            'market_id': market_id,
            'timestamp': bet_result.get('createdTime'),
            'amount': decision['bet_recommendation']['amount'],
            'probability': decision['bet_recommendation']['probability'],
            'edge': decision['bet_recommendation']['edge'],
            'confidence': decision['bet_recommendation']['confidence'],
            'bet_id': bet_result.get('id'),
            'outcome': bet_result.get('outcome')
        }

    async def monitor_positions(self) -> List[Dict]:
        """Monitor and report on active positions."""
        position_updates = []
        
        for bet in self._active_bets:
            try:
                # Get current market status
                market = await self.manifold_client.get_market(bet['market_id'])
                
                position_updates.append({
                    'bet_id': bet['bet_id'],
                    'market_id': bet['market_id'],
                    'original_probability': bet['probability'],
                    'current_probability': market.get('probability'),
                    'is_resolved': market.get('isResolved', False),
                    'resolution': market.get('resolution'),
                    'profit_loss': self._calculate_pnl(bet, market)
                })
                
            except Exception as e:
                logger.error(f"Error monitoring position: {str(e)}")
        
        return position_updates

    def _calculate_pnl(self, bet: Dict, current_market: Dict) -> float:
        """Calculate profit/loss for a position."""
        if not current_market.get('isResolved'):
            # For unresolved markets, calculate unrealized P&L
            original_prob = bet['probability']
            current_prob = float(current_market.get('probability', 0))
            
            # Simple P&L calculation - could be made more sophisticated
            return bet['amount'] * (current_prob - original_prob)
            
        # For resolved markets, calculate realized P&L
        resolution = current_market.get('resolution')
        if resolution:
            if (resolution == 'YES' and bet['outcome'] == 'YES') or \
               (resolution == 'NO' and bet['outcome'] == 'NO'):
                return bet['amount'] * (1 / bet['probability'] - 1)
            else:
                return -bet['amount']
        
        return 0.0

    async def get_portfolio_summary(self) -> Dict:
        """Get summary of all trading activities."""
        active_positions = await self.monitor_positions()
        
        total_invested = sum(bet['amount'] for bet in self._active_bets)
        total_pnl = sum(pos['profit_loss'] for pos in active_positions)
        
        return {
            'total_positions': len(self._active_bets),
            'total_invested': total_invested,
            'total_pnl': total_pnl,
            'active_positions': len([p for p in active_positions if not p['is_resolved']]),
            'resolved_positions': len([p for p in active_positions if p['is_resolved']]),
            'position_details': active_positions
        }

    async def close_position(self, market_id: str) -> Dict:
        """
        Attempt to close a position in a market.
        
        Args:
            market_id: ID of the market position to close
            
        Returns:
            Dictionary containing close position results
        """
        try:
            # Find the existing bet for this market
            existing_bet = next((bet for bet in self._active_bets 
                               if bet['market_id'] == market_id), None)
            
            if not existing_bet:
                return {"success": False, "error": "No active position found"}
            
            # Place an opposing bet to close the position
            close_amount = existing_bet['amount']
            close_probability = 1 - existing_bet['probability']
            
            close_result = await self.manifold_client.place_bet(
                market_id=market_id,
                amount=close_amount,
                probability=close_probability,
                outcome="NO" if existing_bet['outcome'] == "YES" else "YES"
            )
            
            # Update position records
            self._active_bets = [bet for bet in self._active_bets 
                               if bet['market_id'] != market_id]
            
            return {"success": True, "close_details": close_result}
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return {"success": False, "error": str(e)}