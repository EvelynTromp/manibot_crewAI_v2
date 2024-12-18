import sqlite3
from datetime import datetime
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self, db_path: str = "manibot.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create analyzed markets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyzed_markets (
                    market_id TEXT PRIMARY KEY,
                    first_analyzed_at TIMESTAMP,
                    last_analyzed_at TIMESTAMP,
                    analysis_count INTEGER DEFAULT 1,
                    last_probability REAL,
                    last_volume INTEGER,
                    last_liquidity REAL
                )
            """)
            
            conn.commit()

    def record_market_analysis(self, market_data: Dict):
        """Record that a market has been analyzed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.utcnow()
                market_id = market_data.get('id')
                
                # Check if market has been analyzed before
                cursor.execute(
                    "SELECT analysis_count FROM analyzed_markets WHERE market_id = ?",
                    (market_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing record
                    cursor.execute("""
                        UPDATE analyzed_markets 
                        SET last_analyzed_at = ?,
                            analysis_count = analysis_count + 1,
                            last_probability = ?,
                            last_volume = ?,
                            last_liquidity = ?
                        WHERE market_id = ?
                    """, (
                        now,
                        float(market_data.get('probability', 0)),
                        int(market_data.get('volume', 0)),
                        float(market_data.get('totalLiquidity', 0)),
                        market_id
                    ))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO analyzed_markets (
                            market_id, first_analyzed_at, last_analyzed_at,
                            last_probability, last_volume, last_liquidity
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        market_id,
                        now,
                        now,
                        float(market_data.get('probability', 0)),
                        int(market_data.get('volume', 0)),
                        float(market_data.get('totalLiquidity', 0))
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording market analysis: {str(e)}")

    def get_recently_analyzed_markets(self, hours: int = 24) -> List[str]:
        """Get list of market IDs analyzed within the specified hours."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT market_id 
                    FROM analyzed_markets 
                    WHERE last_analyzed_at > datetime('now', ?) 
                """, (f'-{hours} hours',))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting recently analyzed markets: {str(e)}")
            return []

    def get_market_analysis_stats(self, market_id: str) -> Optional[Dict]:
        """Get analysis statistics for a specific market."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        first_analyzed_at,
                        last_analyzed_at,
                        analysis_count,
                        last_probability,
                        last_volume,
                        last_liquidity
                    FROM analyzed_markets 
                    WHERE market_id = ?
                """, (market_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'first_analyzed_at': row[0],
                        'last_analyzed_at': row[1],
                        'analysis_count': row[2],
                        'last_probability': row[3],
                        'last_volume': row[4],
                        'last_liquidity': row[5]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting market analysis stats: {str(e)}")
            return None