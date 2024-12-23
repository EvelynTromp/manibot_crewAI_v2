from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class ReportFormatter:
    """
    A simplified report formatter for market analysis that handles both individual 
    and consolidated reports. This implementation focuses on reliability and 
    debuggability over complex features.
    """
    
    def __init__(self):
        """Initialize the report formatter with basic settings."""
        # Create reports directory in current working directory
        self.reports_dir = Path.cwd() / 'reports'
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize session tracking
        self.current_analyses = []
        self.session_start_time = None
        
    def start_new_session(self):
        """Start a new analysis session."""
        self.current_analyses = []
        self.session_start_time = datetime.now()
        logger.info("Started new analysis session")

    def format_market_analysis(self, execution_data: Dict) -> str:
        """
        Format a single market analysis into a readable report.
        This is the core formatting function that creates the actual report content.
        """
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
            
            # Build the report content
            report = [
                "MARKET ANALYSIS REPORT",
                f"Generated: {timestamp}",
                "=" * 80,
                "",
                "MARKET INFORMATION",
                "-" * 17,
                f"ID: {market_data.get('id', 'N/A')}",
                f"Question: {market_data.get('question', 'N/A')}",
                f"Created: {created_str}",
                f"Close Time: {close_str}",
                f"Current Probability: {market_data.get('probability', 'N/A')}",
                "",
                "ANALYSIS RESULTS",
                "-" * 15,
                f"Analysis Status: {'Successful' if execution_data.get('success') else 'Failed'}",
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
                    "ERROR INFORMATION",
                    "-" * 16,
                    error,
                    ""
                ])

            # Add key factors if present
            if key_factors := analysis.get('key_factors'):
                report.extend([
                    "KEY FACTORS",
                    "-" * 11
                ])
                report.extend(f"- {factor}" for factor in key_factors)
                report.append("")

            # Add sources if present
            if sources := analysis.get('sources'):
                report.extend([
                    "SOURCES CONSULTED",
                    "-" * 16
                ])
                report.extend(
                    f"- {source.get('url', 'N/A')} (Credibility: {source.get('credibility', 'N/A')})"
                    for source in sources
                )

            return "\n".join(report)

        except Exception as e:
            logger.error(f"Error formatting market analysis: {str(e)}")
            return f"Error generating report: {str(e)}"

    def save_market_report(self, execution_data: Dict) -> Optional[Path]:
        """
        Save an individual market analysis report.
        Returns the path to the saved report file, or None if saving failed.
        """
        try:
            # Generate report content
            report_content = self.format_market_analysis(execution_data)
            
            # Create filename using timestamp and market ID
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            market_id = execution_data.get('market_data', {}).get('id', 'unknown')
            filename = f"market_analysis_{timestamp}_{market_id}.txt"
            
            # Save report
            report_path = self.reports_dir / filename
            report_path.write_text(report_content)
            
            # Store for session tracking
            self.current_analyses.append({
                'timestamp': timestamp,
                'market_id': market_id,
                'content': report_content,
                'success': execution_data.get('success', False)
            })
            
            logger.info(f"Saved market report: {filename}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error saving market report: {str(e)}")
            return None

    def save_session_report(self) -> Optional[Path]:
        """
        Save a consolidated report for the current session.
        Returns the path to the saved report file, or None if saving failed.
        """
        if not self.current_analyses:
            logger.warning("No analyses to save in session report")
            return None
            
        try:
            # Generate session summary
            successful_analyses = sum(1 for a in self.current_analyses if a['success'])
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            
            # Create session report content
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_content = [
                "SESSION ANALYSIS REPORT",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 80,
                "",
                "SESSION SUMMARY",
                "-" * 14,
                f"Total Markets Analyzed: {len(self.current_analyses)}",
                f"Successful Analyses: {successful_analyses}",
                f"Failed Analyses: {len(self.current_analyses) - successful_analyses}",
                f"Session Duration: {session_duration:.1f} seconds",
                "",
                "INDIVIDUAL MARKET ANALYSES",
                "-" * 25,
                ""
            ]
            
            # Add individual reports
            for analysis in self.current_analyses:
                report_content.append("=" * 80)
                report_content.append(analysis['content'])
                report_content.append("=" * 80)
                report_content.append("")
            
            # Save consolidated report
            filename = f"session_report_{timestamp}.txt"
            report_path = self.reports_dir / filename
            report_path.write_text("\n".join(report_content))
            
            logger.info(f"Saved session report: {filename}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error saving session report: {str(e)}")
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