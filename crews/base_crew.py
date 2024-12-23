from crewai import Crew
from typing import List, Dict, Optional
from utils.logger import get_logger
from utils.report_formatter import ReportFormatter
from datetime import datetime
import asyncio

logger = get_logger(__name__)

class BaseCrew(Crew):
    """Enhanced base crew with improved logging and error handling."""
    
    def __init__(self, agents: List, tasks: List, verbose: bool = True):
        super().__init__(
            agents=agents,
            tasks=tasks,
            verbose=verbose
        )
        self._execution_history = []
        self._report_formatter = ReportFormatter()
        self._scan_start_time = None
        
    def start_scan_session(self):
        """Initialize a new market scanning session."""
        self._scan_start_time = datetime.now()
        self._execution_history = []
        self._report_formatter.start_new_session()  # Updated method name
        logger.info("Started new market scanning session")
    
    def log_execution(self, execution_data: Dict) -> None:
        """Log execution details with enhanced error tracking."""
        try:
            # Add metadata
            execution_data['timestamp'] = datetime.now().isoformat()
            execution_data['session_duration'] = (
                datetime.now() - self._scan_start_time
            ).total_seconds() if self._scan_start_time else None
            
            # Store execution in history
            self._execution_history.append(execution_data)
            
            # Save the report and get console summary
            report_path = self._report_formatter.save_market_report(execution_data)  # Updated method name
            console_summary = self._report_formatter.get_console_summary(execution_data)
            
            # Log information
            print(console_summary)
            if report_path:
                logger.info(f"Report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Error in log_execution: {str(e)}")
            print(f"Error logging execution: {str(e)}")

    def get_execution_summary(self) -> Dict:
        """Get enhanced execution summary with timing information."""
        if not self._execution_history:
            return {
                "total_executions": 0,
                "scan_duration": None
            }
            
        successful = sum(1 for e in self._execution_history 
                        if e.get('success', False))
        
        return {
            "total_executions": len(self._execution_history),
            "successful_executions": successful,
            "failed_executions": len(self._execution_history) - successful,
            "latest_execution": self._execution_history[-1] if self._execution_history else None,
            "scan_start_time": self._scan_start_time.isoformat() if self._scan_start_time else None,
            "scan_end_time": datetime.now().isoformat(),
            "scan_duration": (datetime.now() - self._scan_start_time).total_seconds() 
                           if self._scan_start_time else None
        }

    def finalize_scan_session(self) -> Optional[str]:
        """Finalize scanning session with enhanced reporting."""
        try:
            report_path = self._report_formatter.save_session_report()  # Updated method name
            
            if report_path:
                logger.info(f"Session report saved to: {report_path}")
                
                # Generate and display enhanced summary
                summary = self.get_execution_summary()
                print("\nScan Session Summary")
                print("===================")
                print(f"Total Markets Analyzed: {summary['total_executions']}")
                print(f"Successful Executions: {summary['successful_executions']}")
                print(f"Failed Executions: {summary['failed_executions']}")
                if summary.get('scan_duration'):
                    print(f"Total Scan Duration: {summary['scan_duration']:.1f}s")
                print(f"Full report saved to: {report_path}")
            
            return str(report_path) if report_path else None
            
        except Exception as e:
            logger.error(f"Error finalizing scan session: {str(e)}")
            return None