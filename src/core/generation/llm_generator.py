from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import asyncio

from src.core.retrieval.retrieval_interface import RetrievalInterface
from src.core.retrieval.models import DocumentMatch, SearchResult
from src.infrastructure.llm_controller import LLMController
from src.core.context.context_window import ContextWindow
from src.core.generation.rag import RAGTools, RAGToolsConfig
from src.logger import get_module_logger

logger = get_module_logger(__name__)

class LLMGenerator:
    def __init__(
        self,
        retrieval_interface: Optional[RetrievalInterface] = None,
        context_window: Optional[ContextWindow] = None,
        llm_controller: Optional[LLMController] = None,
        rag_config: Optional[RAGToolsConfig] = None
    ):
        """
        Initialize the LLM generator.
        
        Args:
            retrieval_interface: Interface for document retrieval
            context_window: Manager for conversation context
            llm_controller: Controller for LLM operations
            rag_config: Configuration for RAG tools
        """

        self.retrieval_interface = retrieval_interface
        self.context_window = context_window
        self.llm_controller = llm_controller
        self.rag_config = rag_config            
        self.rag_tools = RAGTools(context_window, retrieval_interface, self.rag_config)

        logger.info("LLMGenerator initialized with retrieval integration")

    def generate_response(
        self,
        user_message: str,
        thinking_model: bool = True,
        max_new_tokens: int = 8096,
        rag_enabled: bool = False
    ) -> Tuple[str, str, Optional[SearchResult]]:
        """
        Generate a response using retrieval-augmented generation.
        
        Args:
            user_message: User's question or prompt
            thinking_model: Whether to use thinking capabilities
            max_new_tokens: Maximum tokens for generation
            rag_enabled: Whether to use retrieval-augmented generation
            
        Returns:
            Tuple of (response, thinking, retrieval_result)
        """
        
        retrieval_result = None
        if rag_enabled:
            retrieval_result = self.rag_tools.perform_retrieval(user_message)

        # Generate response with or without retrieval context
        if retrieval_result and retrieval_result.matches:
            # For RAG, augment the user message with context
            augmented_message = self.rag_tools.augment_query_with_context(user_message, retrieval_result)
            logger.info(f"Augmented query: {augmented_message}")
            
            # Create context with augmented message for generation
            context_for_generation = self.context_window.context_window.copy()
            context_for_generation.append({'role': 'user', 'content': augmented_message})
            
            response, thinking = self.llm_controller.generate_response_from_context(
                context_for_generation, thinking_model, max_new_tokens
            )
        else:
            # Standard generation - add user message to context and generate
            context_for_generation = self.context_window.context_window.copy()
            context_for_generation.append({'role': 'user', 'content': user_message})
            
            response, thinking = self.llm_controller.generate_response_from_context(
                context_for_generation, thinking_model, max_new_tokens
            )

        logger.info(f"RAG response generated with retrieval: {retrieval_result is not None}")
        return response, thinking, retrieval_result