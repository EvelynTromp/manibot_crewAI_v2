from crewai import Crew
from typing import List, Dict
from utils.logger import get_logger
from pydantic import Field

logger = get_logger(__name__)

class BaseCrew(Crew):
    """Base crew class with common functionality for all crews."""
    
    # Define execution_history as a proper Pydantic field with a default value
    execution_history: List[Dict] = Field(default_factory=list)
    
    def __init__(self, agents: List, tasks: List, verbose: bool = True):
        super().__init__(
            agents=agents,
            tasks=tasks,
            verbose=verbose
        )
    
    def log_execution(self, execution_data: Dict):
        """Log execution details for tracking and analysis."""
        self.execution_history.append(execution_data)
        logger.info(f"Execution logged: {execution_data}")
    
    def get_execution_summary(self) -> Dict:
        """Get summary of all executions."""
        if not self.execution_history:
            return {"total_executions": 0}
            
        return {
            "total_executions": len(self.execution_history),
            "successful_executions": sum(1 for e in self.execution_history if e.get("success", False)),
            "failed_executions": sum(1 for e in self.execution_history if not e.get("success", False)),
            "latest_execution": self.execution_history[-1] if self.execution_history else None
        }

    async def validate_crew_state(self) -> bool:
        """Validate that the crew is in a valid state to execute tasks."""
        try:
            if not self.agents:
                logger.error("No agents assigned to crew")
                return False
                
            if not self.tasks:
                logger.error("No tasks assigned to crew")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating crew state: {str(e)}")
            return False
    
    async def handle_error(self, error: Exception, context: Dict):
        """Handle errors during crew execution."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        logger.error(f"Crew error occurred: {error_data}")
        
        self.log_execution({
            "success": False,
            "error": error_data,
            "context": context
        })
        
        return error_data