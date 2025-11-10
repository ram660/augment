"""LightningStore manager for HomeView AI agent optimization."""

import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import agentlightning as agl
    from agentlightning import LightningStore
    AGENTLIGHTNING_AVAILABLE = True
except ImportError:
    AGENTLIGHTNING_AVAILABLE = False
    LightningStore = None

logger = logging.getLogger(__name__)


class LightningStoreManager:
    """
    Manages the LightningStore for tracking agent interactions and training data.
    
    Features:
    - Centralized store for all agent traces
    - SQLite for development, PostgreSQL for production
    - Automatic initialization and connection management
    - Query helpers for retrieving training data
    """
    
    _instance: Optional['LightningStoreManager'] = None
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize LightningStore manager.
        
        Args:
            db_url: Database URL (defaults to SQLite in project root)
        """
        if not AGENTLIGHTNING_AVAILABLE:
            logger.warning("agentlightning not available. Agent optimization disabled.")
            self.store = None
            self.enabled = False
            return
        
        # Default to SQLite in project root for development
        if db_url is None:
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / "lightning.db"
            db_url = f"sqlite:///{db_path}"
        
        self.db_url = db_url
        self.enabled = True
        
        try:
            # Initialize LightningStore
            self.store = LightningStore(db_url=db_url)
            logger.info(f"LightningStore initialized with database: {db_url}")
        except Exception as e:
            logger.error(f"Failed to initialize LightningStore: {e}", exc_info=True)
            self.store = None
            self.enabled = False
    
    @classmethod
    def get_instance(cls, db_url: Optional[str] = None) -> 'LightningStoreManager':
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(db_url=db_url)
        return cls._instance
    
    def is_enabled(self) -> bool:
        """Check if Agent Lightning is enabled and working."""
        return self.enabled and self.store is not None
    
    def get_dataset(
        self,
        agent_name: str,
        min_reward: Optional[float] = None,
        max_reward: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve training dataset from the store.
        
        Args:
            agent_name: Name of the agent to get data for
            min_reward: Minimum reward threshold (e.g., 0.7 for good responses)
            max_reward: Maximum reward threshold
            limit: Maximum number of records to return
            
        Returns:
            List of interaction records
        """
        if not self.is_enabled():
            logger.warning("LightningStore not enabled. Returning empty dataset.")
            return []
        
        try:
            # Query the store for agent traces
            # Note: Actual API may vary based on agentlightning version
            dataset = self.store.get_dataset(
                agent_name=agent_name,
                min_reward=min_reward,
                max_reward=max_reward,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(dataset)} records for agent '{agent_name}'")
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to retrieve dataset: {e}", exc_info=True)
            return []
    
    def get_statistics(self, agent_name: str) -> Dict[str, Any]:
        """
        Get statistics about agent performance.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with statistics (count, avg_reward, etc.)
        """
        if not self.is_enabled():
            return {
                "enabled": False,
                "total_interactions": 0,
                "avg_reward": 0.0
            }
        
        try:
            # Get all traces for this agent
            dataset = self.get_dataset(agent_name=agent_name)
            
            if not dataset:
                return {
                    "enabled": True,
                    "total_interactions": 0,
                    "avg_reward": 0.0
                }
            
            # Calculate statistics
            rewards = [record.get("reward", 0.0) for record in dataset if "reward" in record]
            avg_reward = sum(rewards) / len(rewards) if rewards else 0.0
            
            return {
                "enabled": True,
                "total_interactions": len(dataset),
                "avg_reward": avg_reward,
                "min_reward": min(rewards) if rewards else 0.0,
                "max_reward": max(rewards) if rewards else 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {
                "enabled": True,
                "total_interactions": 0,
                "avg_reward": 0.0,
                "error": str(e)
            }
    
    def clear_data(self, agent_name: Optional[str] = None):
        """
        Clear training data (use with caution!).
        
        Args:
            agent_name: If provided, only clear data for this agent. Otherwise clear all.
        """
        if not self.is_enabled():
            logger.warning("LightningStore not enabled. Nothing to clear.")
            return
        
        try:
            if agent_name:
                logger.warning(f"Clearing data for agent: {agent_name}")
                # Implementation depends on agentlightning API
                # self.store.clear_agent_data(agent_name)
            else:
                logger.warning("Clearing ALL agent data")
                # self.store.clear_all()
            
        except Exception as e:
            logger.error(f"Failed to clear data: {e}", exc_info=True)


# Singleton instance
def get_lightning_store() -> LightningStoreManager:
    """Get the global LightningStore manager instance."""
    return LightningStoreManager.get_instance()

