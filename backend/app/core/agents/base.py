from typing import Dict, Any, Optional
import logging
from abc import ABC, abstractmethod

class Agent:
    """Base class for all agents"""

    def __init__(self, name:str):
        self.name = name
        self.context: Dict[str, Any]= {}
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output. To be implemented by subclasses."""
        pass
    
    def update_context(self, key: str, value: Any) -> None:
        """Updates the Agent's context with new info"""
        self.logger.debug(f"Updating context: {key}")
        self.context[key] = value
    
    def get_context(self, key: str, default: Optional[Any] = None) -> Any:
        """Get information from the agent's context."""
        return self.context.get(key, default)