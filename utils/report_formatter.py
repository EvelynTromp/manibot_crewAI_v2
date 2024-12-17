from datetime import datetime
from typing import Dict, List, Optional
import os
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class ReportFormatter:
    """Handles formatting and storage of comprehensive market analysis reports."""
    
    def __init__(self):
        # Create reports directory if it doesn't exist
        self.reports_dir = os.path.join(os.getcwd(), 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # Initialize scan session storage
        self.current_scan_analyses = []
        self.scan_start_time = None

    def start_new_scan(self):
        """Initialize a new scan session."""
        self.current_scan_analyses = []
        self.scan_start_time = datetime.now()

    def format_market_analysis(self, execution_data: Dict) -> str:
        """Format a single market analysis into our comprehensive template."""
        try:
            # Extract all data components
            market_data = execution_data.get('research_data', {}).get('market_data', {})
            research_data = execution_data.get('research_data', {})
            analysis = execution_data.get('analysis', {})
            result = execution_data.get('result', {})
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Build comprehensive report with all analysis steps
            report = f"""
{'='*80}
MARKET ANALYSIS REPORT - {timestamp}
{'='*80}

MARKET OVERVIEW
--------------
Market ID: {market_data.get('id', 'N/A')}
Question: {market_data.get('question', 'N/A')}
Created Time: {datetime.fromtimestamp(market_data.get('createdTime', 0)/1000).strftime('%Y-%m-%d %H:%M:%S') if market_data.get('createdTime') else 'N/A'}
Close Time: {datetime.fromtimestamp(market_data.get('closeTime', 0)/1000).strftime('%Y-%m-%d %H:%M:%S') if market_data.get('closeTime') else 'N/A'}

Market Status:
* Trading Volume: {market_data.get('volume', 0)}
* Total Liquidity: {market_data.get('totalLiquidity', 0)}
* Current Probability: {market_data.get('probability', 0):.2%}
* Market Type: {market_data.get('outcomeType', 'N/A')} ({market_data.get('mechanism', 'N/A')})
* Unique Bettor Count: {market_data.get('uniqueBettorCount', 0)}

Market Description:
{self._format_description(market_data.get('textDescription', ''))}

DETAILED RESEARCH ANALYSIS
------------------------
{self._format_research_analysis(research_data)}

GPT ANALYSIS PROCESS
------------------
{self._format_gpt_analysis(analysis)}

DECISION MAKING PROCESS
---------------------
{self._format_decision_process(analysis, result)}

EXECUTION OUTCOME
---------------
Result: {'SUCCESS' if result.get('success') else 'NO TRADE'}
Reason: {result.get('reason', 'No reason provided')}
Details: {result.get('details', 'No additional details')}

{'='*80}
"""
            # Store analysis for consolidated report
            self.current_scan_analyses.append(report)
            
            return report
            
        except Exception as e:
            error_msg = f"Error formatting market analysis: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _format_description(self, description: str) -> str:
        """Format the market description with proper wrapping."""
        if not description:
            return "No description provided"
            
        # Wrap text at 80 characters
        words = description.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= 80:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
                
        if current_line:
            lines.append(' '.join(current_line))
            
        return '\n'.join(lines)

    def _format_research_analysis(self, research_data: Dict) -> str:
        """Format the complete research analysis including all findings."""
        findings = research_data.get('research_findings', [])
        
        if not findings:
            return "No research findings available"
            
        analysis = "Research Queries and Results:\n\n"
        
        for i, finding in enumerate(findings, 1):
            analysis += f"Query {i}: {finding.get('query')}\n"
            analysis += "-" * 80 + "\n"
            
            results = finding.get('results', '')
            # Process and format each search result
            for line in results.split('\n'):
                if line.strip():
                    # Indent continuation lines
                    if line.startswith('   '):
                        analysis += f"    {line}\n"
                    else:
                        analysis += f"{line}\n"
            
            analysis += "\n"
            
        return analysis

    def _format_gpt_analysis(self, analysis: Dict) -> str:
        """Format the complete GPT analysis process."""
        if not analysis:
            return "No GPT analysis available"
            
        gpt_analysis = """
Step-by-Step Analysis Process:
----------------------------\n"""
        
        # Add the full reasoning process
        reasoning = analysis.get('reasoning', '')
        gpt_analysis += reasoning + "\n\n"
        
        # Add probability and confidence assessments
        gpt_analysis += f"""
Key Analysis Metrics:
------------------
Estimated Probability: {analysis.get('estimated_probability')}
Confidence Level: {analysis.get('confidence_level')}

Key Decision Factors:
{self._format_key_factors(analysis.get('key_factors', []))}
"""
        
        return gpt_analysis

    def _format_key_factors(self, factors: List[str]) -> str:
        """Format the list of key factors with proper indentation."""
        if not factors:
            return "No key factors identified"
            
        return '\n'.join(f"* {factor}" for factor in factors)

    def _format_decision_process(self, analysis: Dict, result: Dict) -> str:
        """Format the decision-making process including all considerations."""
        decision = f"""
Analysis Summary:
---------------
"""
        
        if analysis.get('bet_recommendation'):
            bet_rec = analysis['bet_recommendation']
            decision += f"""
Recommended Position:
* Amount: ${bet_rec.get('amount', 0):.2f}
* Edge: {bet_rec.get('edge', 0):.2%}
* Confidence: {bet_rec.get('confidence', 0):.2%}
* Market Quality Score: {bet_rec.get('market_quality_score', 0):.2f}
"""
        else:
            decision += "No betting opportunity identified\n"
            
        return decision

    def save_consolidated_report(self) -> str:
        """Save all analyses from the current scan session to a single file."""
        try:
            if not self.current_scan_analyses:
                return ""
                
            # Create date-specific directory
            date_dir = os.path.join(self.reports_dir, datetime.now().strftime('%Y-%m-%d'))
            os.makedirs(date_dir, exist_ok=True)
            
            # Generate unique filename for the scan session
            timestamp = self.scan_start_time.strftime('%Y%m%d_%H%M%S')
            filename = f"consolidated_scan_report_{timestamp}.txt"
            filepath = os.path.join(date_dir, filename)
            
            # Create the consolidated report
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write scan session header
                f.write(f"""
{'#'*100}
CONSOLIDATED SCAN REPORT
{'#'*100}
Scan Start Time: {self.scan_start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Markets Analyzed: {len(self.current_scan_analyses)}

""")
                
                # Write all market analyses
                for analysis in self.current_scan_analyses:
                    f.write(analysis)
                    f.write("\n\n")
                    
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving consolidated report: {str(e)}")
            return ""

    def format_console_summary(self, execution_data: Dict) -> str:
        """Format a concise summary for console output."""
        try:
            market_data = execution_data.get('research_data', {}).get('market_data', {})
            result = execution_data.get('result', {})
            
            return f"""Market Analysis: {market_data.get('question', 'N/A')}
Current Prob: {market_data.get('probability', 0):.2%}
Decision: {'EXECUTE' if result.get('success') else 'NO TRADE'}
Reason: {result.get('reason', 'N/A')}
---------------------"""
            
        except Exception as e:
            logger.error(f"Error formatting console summary: {str(e)}")
            return "Error generating summary"