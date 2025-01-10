# utils/report_formatter.py

from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Optional
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class ReportFormatter:
    """
    A simplified report formatter that focuses on clear, readable reports
    without unnecessary complexity. This version uses a single file per
    session and writes reports incrementally.
    """
    
    def __init__(self):
        """Initialize the report formatter with basic settings."""
        # Create reports directory
        self.reports_dir = Path.cwd() / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize session tracking
        self.current_report_path = None
        self.session_start_time = None
        self.trades_executed = 0
        self.markets_analyzed = 0
        self.successful_analyses = 0
        
    def start_session(self):
        """Start a new trading session and create the report file."""
        self.session_start_time = datetime.now()
        timestamp = self.session_start_time.strftime('%Y%m%d_%H%M%S')
        self.current_report_path = self.reports_dir / f"trading_session_{timestamp}.txt"
        
        # Write session header
        header = self._create_session_header()
        self.current_report_path.write_text(header)
        logger.info(f"Started new trading session: {self.current_report_path}")
        
        # Reset session statistics
        self.trades_executed = 0
        self.markets_analyzed = 0
        self.successful_analyses = 0

    def log_market_analysis(self, execution_data: Dict):
        """Log a single market analysis with clear formatting."""
        if not self.current_report_path:
            logger.error("No active session report file")
            return
            
        try:
            
            # Update session statistics
            self.markets_analyzed += 1
            if execution_data.get('success'):
                self.successful_analyses += 1
            if execution_data.get('trade_executed'):
                self.trades_executed += 1
            
            # Format the analysis entry
            entry = self._format_market_analysis(execution_data)
            
            # Append to report file
            with open(self.current_report_path, 'a', encoding='utf-8') as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(entry)
                f.write("\n" + "=" * 80 + "\n")
                
        except Exception as e:
            logger.error(f"Error logging market analysis: {str(e)}")

    def finalize_session(self) -> Optional[Path]:
        """Finalize the session report with summary statistics."""
        if not self.current_report_path or not self.session_start_time:
            logger.warning("No active session to finalize")
            return None
            
        try:
            # Calculate session duration
            duration = datetime.now() - self.session_start_time
            
            # Create summary content
            summary = [
                "",
                "SESSION SUMMARY",
                "=" * 80,
                f"Session End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Duration: {duration.total_seconds():.1f} seconds",
                "",
                "Statistics:",
                f"Total Markets Analyzed: {self.markets_analyzed}",
                f"Successful Analyses: {self.successful_analyses}",
                f"Success Rate: {(self.successful_analyses/self.markets_analyzed*100):.1f}%" if self.markets_analyzed else "N/A",
                f"Trades Executed: {self.trades_executed}",
                "",
                "=" * 80
            ]
            
            # Append summary to report
            with self.current_report_path.open('a') as f:
                f.write("\n".join(summary))
                
            return self.current_report_path
            
        except Exception as e:
            logger.error(f"Error finalizing session report: {str(e)}")
            return None

    def get_console_summary(self, execution_data: Dict) -> str:
        """Generate a concise console summary of market analysis."""
        market_id = execution_data.get('market_id', 'unknown')
        status = "✅" if execution_data.get('success') else "❌"
        
        if error := execution_data.get('error'):
            return f"{status} Market {market_id}: Failed - {error}"
            
        analysis = execution_data.get('analysis', {})
        prob = analysis.get('estimated_probability')
        conf = analysis.get('confidence_level')
        
        summary = f"{status} Market {market_id}"
        if prob is not None:
            summary += f" (Prob: {prob:.1%}"
            if conf is not None:
                summary += f", Conf: {conf:.1%}"
            summary += ")"
            
        if execution_data.get('trade_executed'):
            summary += " [Trade Executed]"
            
        return summary

    def _create_session_header(self) -> str:
        """Create the initial session header."""
        return "\n".join([
            "TRADING SESSION REPORT",
            "=" * 80,
            f"Session Started: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Settings:",
            f"- Min Bet: ${settings.MIN_BET_AMOUNT}",
            f"- Max Bet: ${settings.MAX_BET_AMOUNT}",
            f"- Min Edge: {settings.MIN_EDGE_REQUIREMENT:.1%}",
            "",
            "MARKET ANALYSES",
            "-" * 14,
            ""
        ])

    def _format_market_analysis(self, execution_data: Dict) -> str:
        """Format a single market analysis entry."""
        market_data = execution_data.get('market_data', {})
        analysis = execution_data.get('analysis', {})
        
        # Format timestamps
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        created_time = market_data.get('createdTime')
        close_time = market_data.get('closeTime')
        
        created_str = (datetime.fromtimestamp(created_time/1000).strftime('%Y-%m-%d %H:%M:%S') 
                      if created_time else 'N/A')
        close_str = (datetime.fromtimestamp(close_time/1000).strftime('%Y-%m-%d %H:%M:%S') 
                    if close_time else 'N/A')
        
        # Build the analysis section
        sections = [
            f"Analysis Time: {timestamp}",
            "",
            "Market Information:",
            f"- ID: {market_data.get('id', 'N/A')}",
            f"- Question: {market_data.get('question', 'N/A')}",
            f"- Created: {created_str}",
            f"- Close Time: {close_str}",
            f"- Current Probability: {market_data.get('probability', 'N/A')}",
            ""
        ]
        
        # Add analysis results
        if analysis:
            sections.extend([
                "Analysis Results:",
                f"- Status: {'Successful' if execution_data.get('success') else 'Failed'}",
                f"- Estimated Probability: {analysis.get('estimated_probability', 'N/A')}",
                f"- Confidence Level: {analysis.get('confidence_level', 'N/A')}",
                "",
                "Reasoning:",
                analysis.get('reasoning', 'No reasoning provided'),
                ""
            ])

            # Add key factors if present
            if key_factors := analysis.get('key_factors'):
                sections.extend(["Key Factors:"])
                sections.extend(f"- {factor}" for factor in key_factors)
                sections.append("")

        # Add trade information if executed
        if execution_data.get('trade_executed'):
            trade_info = execution_data.get('trade', {})
            sections.extend([
                "Trade Execution:",
                f"- Amount: ${trade_info.get('amount', 'N/A')}",
                f"- Probability: {trade_info.get('probability', 'N/A')}",
                f"- Outcome: {trade_info.get('outcome', 'N/A')}",
                ""
            ])

        # Add error information if present
        if error := execution_data.get('error'):
            sections.extend([
                "Error Information:",
                error,
                ""
            ])

        return "\n".join(sections)