from datetime import datetime
from typing import Dict, List, Optional
import os
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class ReportFormatter:
    """Handles formatting and storage of comprehensive market analysis reports with collapsible sections."""
    
    def __init__(self):
        self.reports_dir = os.path.join(os.getcwd(), 'reports')
        os.makedirs(self.reports_dir, exist_ok=True)
        self.current_scan_analyses = []
        self.scan_start_time = None

    def start_new_scan(self):
        """Initialize a new scan session."""
        self.current_scan_analyses = []
        self.scan_start_time = datetime.now()

    def _create_collapsible_section(self, title: str, content: str) -> str:
        """Create a collapsible markdown section."""
        return f"""<details>
<summary>{title}</summary>

{content}
</details>
"""

    def format_market_analysis(self, execution_data: Dict) -> str:
        """Format a single market analysis into collapsible sections."""
        try:
            market_data = execution_data.get('research_data', {}).get('market_data', {})
            research_data = execution_data.get('research_data', {})
            analysis = execution_data.get('analysis', {})
            result = execution_data.get('result', {})
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Main header
            report = f"""# Market Analysis Report - {timestamp}

"""
            # Market Overview Section
            market_overview = f"""Market ID: {market_data.get('id', 'N/A')}
Question: {market_data.get('question', 'N/A')}
Created Time: {datetime.fromtimestamp(market_data.get('createdTime', 0)/1000).strftime('%Y-%m-%d %H:%M:%S') if market_data.get('createdTime') else 'N/A'}
Close Time: {datetime.fromtimestamp(market_data.get('closeTime', 0)/1000).strftime('%Y-%m-%d %H:%M:%S') if market_data.get('closeTime') else 'N/A'}

Trading Volume: {market_data.get('volume', 0)}
Total Liquidity: {market_data.get('totalLiquidity', 0)}
Current Probability: {market_data.get('probability', 0):.2%}
Market Type: {market_data.get('outcomeType', 'N/A')} ({market_data.get('mechanism', 'N/A')})
Unique Bettor Count: {market_data.get('uniqueBettorCount', 0)}"""

            report += self._create_collapsible_section("Market Overview", market_overview)
            
            # Market Description Section
            description = self._format_description(market_data.get('textDescription', ''))
            report += self._create_collapsible_section("Market Description", description)
            
            # Research Analysis Section
            research_analysis = self._format_research_analysis(research_data)
            report += self._create_collapsible_section("Research Analysis", research_analysis)
            
            # GPT Analysis Section
            gpt_analysis = self._format_gpt_analysis(analysis)
            report += self._create_collapsible_section("GPT Analysis Process", gpt_analysis)
            
            # Decision Process Section
            decision_process = self._format_decision_process(analysis, result)
            report += self._create_collapsible_section("Decision Making Process", decision_process)
            
            # Execution Outcome Section
            execution_outcome = f"""Result: {'SUCCESS' if result.get('success') else 'NO TRADE'}
Reason: {result.get('reason', 'No reason provided')}
Details: {result.get('details', 'No additional details')}
Raw execution data: {execution_data}"""
            
            report += self._create_collapsible_section("Execution Outcome", execution_outcome)
            

            report += "\n---\n"  # Separator between market analyses
            
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
            
        analysis = ""
        
        for i, finding in enumerate(findings, 1):
            query_section = f"""Query {i}: {finding.get('query')}
{'-' * 80}

{finding.get('results', '')}

"""
            analysis += self._create_collapsible_section(f"Research Query {i}", query_section)
            
        return analysis

    def _format_gpt_analysis(self, analysis: Dict) -> str:
        """Format the complete GPT analysis process."""
        if not analysis:
            return "No GPT analysis available"
            
        # Reasoning Process Section
        reasoning = analysis.get('reasoning', '')
        
        # Metrics Section
        metrics = f"""Estimated Probability: {analysis.get('estimated_probability')}
Confidence Level: {analysis.get('confidence_level')}

Key Decision Factors:
{self._format_key_factors(analysis.get('key_factors', []))}"""
        
        full_analysis = self._create_collapsible_section("Analysis Process", reasoning)
        full_analysis += self._create_collapsible_section("Analysis Metrics", metrics)
        
        return full_analysis

    def _format_key_factors(self, factors: List[str]) -> str:
        """Format the list of key factors with proper indentation."""
        if not factors:
            return "No key factors identified"
            
        return '\n'.join(f"* {factor}" for factor in factors)

    def _format_decision_process(self, analysis: Dict, result: Dict) -> str:
        """Format the decision-making process including all considerations."""
        decision = ""
        
        if analysis.get('bet_recommendation'):
            bet_rec = analysis['bet_recommendation']
            decision = f"""Recommended Position:
* Amount: ${bet_rec.get('amount', 0):.2f}
* Edge: {bet_rec.get('edge', 0):.2%}
* Confidence: {bet_rec.get('confidence', 0):.2%}
* Market Quality Score: {bet_rec.get('market_quality_score', 0):.2f}"""
        else:
            decision = "No betting opportunity identified"
            
        return decision

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

    def save_consolidated_report(self) -> str:
        """Save all analyses from the current scan session to a single file."""
        try:
            if not self.current_scan_analyses:
                return ""
                
            date_dir = os.path.join(self.reports_dir, datetime.now().strftime('%Y-%m-%d'))
            os.makedirs(date_dir, exist_ok=True)
            
            timestamp = self.scan_start_time.strftime('%Y%m%d_%H%M%S')
            filename = f"consolidated_scan_report_{timestamp}.md"  # Changed to .md extension
            filepath = os.path.join(date_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write scan session header
                header = f"""# Consolidated Scan Report

<details>
<summary>Scan Session Information</summary>

* Start Time: {self.scan_start_time.strftime('%Y-%m-%d %H:%M:%S')}
* End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
* Total Markets Analyzed: {len(self.current_scan_analyses)}

</details>

---

"""
                f.write(header)
                
                # Write all market analyses
                for analysis in self.current_scan_analyses:
                    f.write(analysis)
                    f.write("\n\n")
                    
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving consolidated report: {str(e)}")
            return ""