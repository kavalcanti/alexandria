from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import asyncio

from src.core.retrieval.retrieval_interface import RetrievalInterface
from src.core.retrieval.models import DocumentMatch, SearchResult
from src.infrastructure.llm_controller import LLMController
from src.core.context.context_window import ContextWindow
from src.core.generation.rag import RAGTools, RAGToolsConfig
from src.core.memory.llm_db_msg import MessagesController
from src.logger import get_module_logger

logger = get_module_logger(__name__)

class LLMGenerator:
    def __init__(
        self,
        retrieval_interface: Optional[RetrievalInterface] = None,
        context_window: Optional[ContextWindow] = None,
        llm_controller: Optional[LLMController] = None,
        rag_config: Optional[RAGToolsConfig] = None,
        messages_controller: Optional[MessagesController] = None
    ):
        """
        Initialize the LLM generator.
        
        Args:
            retrieval_interface: Interface for document retrieval
            llm_generator: Manager for LLM operations
            context_window: Manager for conversation context
        """

        self.retrieval_interface = retrieval_interface
        self.context_window = context_window
        self.llm_controller = llm_controller
        self.messages_controller = messages_controller
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
        
        This method cleanly separates concerns: retrieval, context building,
        and generation without messy context manipulation.
        
        Args:
            user_query: User's question or prompt
            thinking_model: Whether to use thinking capabilities
            max_new_tokens: Maximum tokens for generation
            
        Returns:
            Tuple of (response, thinking, retrieval_result)
        """

        if rag_enabled:
            retrieval_result = self.rag_tools.perform_retrieval(user_message)
        else:
            retrieval_result = None

        self.context_window.add_message('user', user_message)
            
        # Generate response with or without retrieval context
        if retrieval_result and retrieval_result.matches:
            # For RAG, we need to augment the last user message in the context
            augmented_message = self.rag_tools.augment_query_with_context(user_message, retrieval_result)
            logger.info(f"Augmented query: {augmented_message}")
            
            # Temporarily replace the last user message with the augmented one
            context_for_generation = self.context_window.context_window.copy()
            context_for_generation[-1] = {'role': 'user', 'content': augmented_message}
            
            response, thinking = self.llm_controller.generate_response_from_context(
                context_for_generation, thinking_model, max_new_tokens
            )
        else:
            response, thinking = self.llm_controller.generate_response_from_context(
                self.context_window.context_window, thinking_model, max_new_tokens
            )

        # Store assistant response in context
        self.context_window.add_message('assistant', response)
        self.messages_controller.insert_single_message(self.context_window.conversation_id, 'assistant', response, 0)
        if thinking:
            self.context_window.add_message('assistant-reasoning', thinking)
            self.messages_controller.insert_single_message(self.context_window.conversation_id, 'assistant-reasoning', thinking, 0)
        logger.info(f"RAG response generated with retrieval: {retrieval_result is not None}")
        return response, thinking, retrieval_result