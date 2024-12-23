from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class ReportFormatter:
    """
    A consolidated report formatter that creates a single, comprehensive report
    for market analysis sessions. This implementation combines both individual
    market analyses and session summaries into one file for better tracking
    and easier review.
    """
    
    def __init__(self):
        """Initialize the report formatter with basic settings."""
        # Create reports directory in current working directory
        self.reports_dir = Path.cwd() / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize session tracking
        self.current_analyses = []
        self.session_start_time = None
        self.report_path = None
        
    def start_new_session(self):
        """
        Start a new analysis session and create the report file.
        The report file is created at session start and updated incrementally.
        """
        self.current_analyses = []
        self.session_start_time = datetime.now()
        
        # Create the report file with initial session header
        timestamp = self.session_start_time.strftime('%Y%m%d_%H%M%S')
        self.report_path = self.reports_dir / f"trading_report_{timestamp}.txt"
        
        # Write initial session header
        header = [
            "TRADING SESSION REPORT",
            f"Session Started: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            "MARKET ANALYSES",
            "-" * 14,
            ""
        ]
        
        self.report_path.write_text("\n".join(header))
        logger.info(f"Started new trading session: {self.report_path}")

    def format_market_analysis(self, execution_data: Dict) -> str:
        """Format a single market analysis into a readable report section."""
        try:
            market_data = execution_data.get('market_data', {})
            analysis = execution_data.get('analysis', {})
            
            # Format timestamps for readability
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            created_time = market_data.get('createdTime')
            close_time = market_data.get('closeTime')
            
            created_str = (datetime.fromtimestamp(created_time/1000).strftime('%Y-%m-%d %H:%M:%S') 
                         if created_time else 'N/A')
            close_str = (datetime.fromtimestamp(close_time/1000).strftime('%Y-%m-%d %H:%M:%S') 
                        if close_time else 'N/A')
            
            # Build the analysis section
            report = [
                "MARKET ANALYSIS",
                f"Time: {timestamp}",
                "-" * 80,
                "",
                "Market Information:",
                f"ID: {market_data.get('id', 'N/A')}",
                f"Question: {market_data.get('question', 'N/A')}",
                f"Created: {created_str}",
                f"Close Time: {close_str}",
                f"Current Probability: {market_data.get('probability', 'N/A')}",
                "",
                "Analysis Results:",
                f"Status: {'Successful' if execution_data.get('success') else 'Failed'}",
                f"Estimated Probability: {analysis.get('estimated_probability', 'N/A')}",
                f"Confidence Level: {analysis.get('confidence_level', 'N/A')}",
                "",
                "Reasoning:",
                analysis.get('reasoning', 'No reasoning provided'),
                ""
            ]

            # Add error information if present
            if error := execution_data.get('error'):
                report.extend([
                    "Error Information:",
                    error,
                    ""
                ])

            # Add key factors if present
            if key_factors := analysis.get('key_factors'):
                report.extend([
                    "Key Factors:"
                ])
                report.extend(f"- {factor}" for factor in key_factors)
                report.append("")

            # Add trade information if executed
            if execution_data.get('trade_executed'):
                trade_info = execution_data.get('trade', {})
                report.extend([
                    "Trade Execution:",
                    f"Amount: {trade_info.get('amount', 'N/A')}",
                    f"Probability: {trade_info.get('probability', 'N/A')}",
                    f"Outcome: {trade_info.get('outcome', 'N/A')}",
                    ""
                ])

            # Add sources if present
            if sources := analysis.get('sources'):
                report.extend([
                    "Sources Consulted:"
                ])
                report.extend(
                    f"- {source.get('url', 'N/A')} (Credibility: {source.get('credibility', 'N/A')})"
                    for source in sources
                )
                report.append("")

            return "\n".join(report)

        except Exception as e:
            logger.error(f"Error formatting market analysis: {str(e)}")
            return f"Error generating analysis section: {str(e)}"

    def append_market_analysis(self, execution_data: Dict) -> None:
        """
        Append a market analysis to the current session report.
        Updates the report file incrementally instead of rewriting the whole file.
        """
        try:
            if not self.report_path or not self.report_path.exists():
                logger.error("No active session report file")
                return
            
            # Format the analysis
            analysis_content = self.format_market_analysis(execution_data)
            
            # Add separator and append to file
            with self.report_path.open('a') as f:
                f.write("=" * 80 + "\n")
                f.write(analysis_content)
                f.write("=" * 80 + "\n\n")
            
            # Store analysis metadata
            self.current_analyses.append({
                'timestamp': datetime.now(),
                'market_id': execution_data.get('market_data', {}).get('id', 'unknown'),
                'success': execution_data.get('success', False),
                'trade_executed': execution_data.get('trade_executed', False)
            })
            
            logger.info(f"Appended analysis for market {execution_data.get('market_data', {}).get('id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error appending market analysis: {str(e)}")

    def finalize_session(self) -> Optional[Path]:
        """
        Finalize the session report by adding summary statistics.
        Returns the path to the complete report file.
        """
        if not self.current_analyses or not self.report_path:
            logger.warning("No analyses to summarize or no report file")
            return None
            
        try:
            # Calculate session statistics
            successful_analyses = sum(1 for a in self.current_analyses if a['success'])
            trades_executed = sum(1 for a in self.current_analyses if a['trade_executed'])
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            
            # Create summary content
            summary = [
                "",
                "SESSION SUMMARY",
                "=" * 80,
                f"Session End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Duration: {session_duration:.1f} seconds",
                "",
                "Statistics:",
                f"- Total Markets Analyzed: {len(self.current_analyses)}",
                f"- Successful Analyses: {successful_analyses}",
                f"- Failed Analyses: {len(self.current_analyses) - successful_analyses}",
                f"- Trades Executed: {trades_executed}",
                "",
                "Success Rate:",
                f"- Analysis Success Rate: {successful_analyses/len(self.current_analyses):.1%}",
                f"- Trade Execution Rate: {trades_executed/len(self.current_analyses):.1%}",
                "",
                "=" * 80
            ]
            
            # Append summary to report file
            with self.report_path.open('a') as f:
                f.write("\n".join(summary))
            
            logger.info("Finalized session report")
            return self.report_path
            
        except Exception as e:
            logger.error(f"Error finalizing session report: {str(e)}")
            return None

    def get_console_summary(self, execution_data: Dict) -> str:
        """Generate a concise summary for console output."""
        try:
            market_data = execution_data.get('market_data', {})
            analysis = execution_data.get('analysis', {})
            
            status = "✅" if execution_data.get('success') else "❌"
            market_id = market_data.get('id', 'unknown')
            
            if error := execution_data.get('error'):
                return f"{status} Market {market_id}: Failed - {error}"
            
            prob = analysis.get('estimated_probability')
            conf = analysis.get('confidence_level')
            prob_str = f"{prob:.1%}" if prob is not None else "N/A"
            conf_str = f"{conf:.1%}" if conf is not None else "N/A"
            
            summary = f"{status} Market {market_id}: Prob={prob_str}, Conf={conf_str}"
            
            if execution_data.get('trade_executed'):
                summary += " [Trade Executed]"
                
            return summary
            
        except Exception as e:
            logger.error(f"Error generating console summary: {str(e)}")
            return f"❌ Error formatting summary: {str(e)}"