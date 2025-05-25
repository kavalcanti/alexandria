"""
Dependency injection container for managing shared services and dependencies.

This container follows the Dependency Injection pattern to manage the lifecycle
and relationships between various components in the conversation system.
"""

from typing import Optional
from src.infrastructure.llm_controller import LLMController
from src.infrastructure.db_connector import DatabaseStorage
from src.core.memory.llm_db_cnvs import ConversationsController
from src.core.memory.llm_db_msg import MessagesController
from src.core.managers.prompt_manager import LLMPromptManager
from src.infrastructure.embedder import Embedder
from src.core.retrieval.retrieval_interface import RetrievalInterface
from src.logger import get_module_logger

logger = get_module_logger(__name__)


class ServiceContainer:
    """
    Container for managing shared dependencies and services.
    
    This class implements a simple dependency injection container that manages
    the lifecycle of shared services and ensures proper dependency relationships.
    It uses lazy initialization to create services only when needed.
    """
    
    def __init__(self) -> None:
        """Initialize the service container with empty dependencies."""
        self._db_storage: Optional[DatabaseStorage] = None
        self._embedder: Optional[Embedder] = None
        self._conversations_controller: Optional[ConversationsController] = None
        self._messages_controller: Optional[MessagesController] = None
        self._llm_controller: Optional[LLMController] = None
        self._prompt_controller: Optional[LLMPromptManager] = None
        self._retrieval_interface: Optional[RetrievalInterface] = None
        self._rag_manager: Optional['RAGManager'] = None
        
    @property
    def db_storage(self) -> DatabaseStorage:
        """Get or create the database storage service."""
        if self._db_storage is None:
            self._db_storage = DatabaseStorage()
            logger.debug("Created DatabaseStorage instance")
        return self._db_storage
    
    @property
    def embedder(self) -> Embedder:
        """Get or create the embedder service."""
        if self._embedder is None:
            self._embedder = Embedder()
            logger.debug("Created Embedder instance")
        return self._embedder
    
    @property
    def conversations_controller(self) -> ConversationsController:
        """Get or create the conversations controller."""
        if self._conversations_controller is None:
            self._conversations_controller = ConversationsController(self.db_storage)
            logger.debug("Created ConversationsController instance")
        return self._conversations_controller
    
    @property
    def messages_controller(self) -> MessagesController:
        """Get or create the messages controller."""
        if self._messages_controller is None:
            self._messages_controller = MessagesController(self.db_storage)
            logger.debug("Created MessagesController instance")
        return self._messages_controller
    
    @property
    def llm_controller(self) -> LLMController:
        """Get or create the LLM controller."""
        if self._llm_controller is None:
            self._llm_controller = LLMController()
            logger.debug("Created LLMController instance")
        return self._llm_controller
    
    @property
    def prompt_controller(self) -> LLMPromptManager:
        """Get or create the prompt controller."""
        if self._prompt_controller is None:
            self._prompt_controller = LLMPromptManager()
            logger.debug("Created LLMPromptManager instance")
        return self._prompt_controller

    @property
    def retrieval_interface(self) -> RetrievalInterface:
        """Get or create the retrieval interface."""
        if self._retrieval_interface is None:
            self._retrieval_interface = RetrievalInterface()
            logger.debug("Created RetrievalInterface instance")
        return self._retrieval_interface

    @property 
    def rag_manager(self) -> 'RAGManager':
        """Get or create the RAG manager."""
        if self._rag_manager is None:
            # Import here to avoid circular dependency
            from src.core.managers.rag_manager import RAGManager
            self._rag_manager = RAGManager(
                retrieval_interface=self.retrieval_interface
            )
            logger.debug("Created RAGManager instance")
        return self._rag_manager


# Global container instance - using singleton pattern for shared dependencies
_container: Optional[ServiceContainer] = None

def get_container() -> ServiceContainer:
    """
    Get the global service container instance.
    
    Returns:
        ServiceContainer: The singleton container instance
    """
    global _container
    if _container is None:
        _container = ServiceContainer()
        logger.info("Initialized global service container")
    return _container

def reset_container() -> None:
    """
    Reset the global container instance.
    
    This is primarily useful for testing or when you need to recreate
    all dependencies with fresh instances.
    """
    global _container
    _container = None
    logger.info("Reset global service container") 