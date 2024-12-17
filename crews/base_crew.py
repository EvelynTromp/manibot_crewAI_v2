from crewai import Crew
from typing import List, Dict, Optional
from utils.logger import get_logger
from utils.report_formatter import ReportFormatter
from datetime import datetime

logger = get_logger(__name__)

class BaseCrew(Crew):
    """Base crew class with enhanced reporting capabilities."""
    
    def __init__(self, agents: List, tasks: List, verbose: bool = True):
        super().__init__(
            agents=agents,
            tasks=tasks,
            verbose=verbose
        )
        self._execution_history = []
        self._report_formatter = ReportFormatter()
        
    def start_scan_session(self):
        """Initialize a new market scanning session."""
        self._report_formatter.start_new_scan()
        logger.info("Started new market scanning session")
    
    def log_execution(self, execution_data: Dict) -> None:
        """Log execution details with comprehensive analysis."""
        try:
            # Add timestamp to execution data
            execution_data['timestamp'] = datetime.now().isoformat()
            
            # Store execution in history
            self._execution_history.append(execution_data)
            
            # Generate detailed report
            detailed_report = self._report_formatter.format_market_analysis(execution_data)
            
            # Generate console summary
            console_summary = self._report_formatter.format_console_summary(execution_data)
            
            # Log console summary
            print(console_summary)
            logger.info(f"Execution logged with full analysis chain")
            
        except Exception as e:
            logger.error(f"Error in log_execution: {str(e)}")
            print(f"Error logging execution: {str(e)}")

    def get_execution_summary(self) -> Dict:
        """Get comprehensive summary of all executions."""
        if not self._execution_history:
            return {"total_executions": 0}
            
        successful = sum(1 for e in self._execution_history 
                        if e.get("result", {}).get("success", False))
        failed = len(self._execution_history) - successful
        
        return {
            "total_executions": len(self._execution_history),
            "successful_executions": successful,
            "failed_executions": failed,
            "latest_execution": self._execution_history[-1] if self._execution_history else None,
            "scan_start_time": self._execution_history[0].get('timestamp') 
                             if self._execution_history else None,
            "scan_end_time": self._execution_history[-1].get('timestamp') 
                           if self._execution_history else None
        }

    def finalize_scan_session(self) -> str:
        """Finalize the scanning session and save consolidated report."""
        try:
            # Save consolidated report
            report_path = self._report_formatter.save_consolidated_report()
            
            if report_path:
                logger.info(f"Consolidated scan report saved to: {report_path}")
                
                # Generate and display final summary
                summary = self.get_execution_summary()
                print("\nScan Session Complete!")
                print(f"Total Markets Analyzed: {summary['total_executions']}")
                print(f"Successful Executions: {summary['successful_executions']}")
                print(f"Failed Executions: {summary['failed_executions']}")
                print(f"Full report saved to: {report_path}")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Error finalizing scan session: {str(e)}")
            return ""

    async def handle_error(self, error: Exception, context: Dict) -> Dict:
        """Handle errors during crew execution with enhanced error reporting."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.error(f"Crew error occurred: {error_data}")
        
        self.log_execution({
            "success": False,
            "error": error_data,
            "context": context
        })
        
        return error_data