"""
RAG (Retrieval-Augmented Generation) Manager for integrating vector search with LLM responses.

This module coordinates between the retrieval system and LLM generation to provide
context-aware responses based on document knowledge.
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from src.core.retrieval.retrieval_interface import RetrievalInterface
from src.core.retrieval.models import DocumentMatch, SearchResult
from src.core.managers.llm_manager import LLMManager
from src.core.managers.context_manager import ContextManager
from src.core.services.service_container import get_container
from src.logger import get_module_logger

logger = get_module_logger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG operations."""
    enable_retrieval: bool = True
    max_retrieval_results: int = 5
    min_similarity_score: float = 0.3
    context_size: int = 1
    retrieval_query_enhancement: bool = True
    include_source_metadata: bool = True


class RAGManager:
    """
    Manager for Retrieval-Augmented Generation operations.
    
    Coordinates between vector search retrieval and LLM generation to provide
    contextually-aware responses based on document knowledge.
    """
    
    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        retrieval_interface: Optional[RetrievalInterface] = None,
        llm_manager: Optional[LLMManager] = None,
        context_manager: Optional[ContextManager] = None
    ):
        """
        Initialize the RAG manager.
        
        Args:
            config: RAG configuration settings
            retrieval_interface: Interface for document retrieval
            llm_manager: Manager for LLM operations
            context_manager: Manager for conversation context
        """
        self.config = config or RAGConfig()
        
        # Use dependency injection or get from service container
        container = get_container()
        self.retrieval_interface = retrieval_interface or container.retrieval_interface
        self.llm_manager = llm_manager
        self.context_manager = context_manager
        
        logger.info("RAGManager initialized with retrieval integration")

    def generate_rag_response(
        self,
        user_query: str,
        thinking_model: bool = True,
        max_new_tokens: int = 8096
    ) -> Tuple[str, str, Optional[SearchResult]]:
        """
        Generate a response using retrieval-augmented generation.
        
        Args:
            user_query: User's question or prompt
            thinking_model: Whether to use thinking capabilities
            max_new_tokens: Maximum tokens for generation
            
        Returns:
            Tuple of (response, thinking, retrieval_result)
        """
        retrieval_result = None
        
        if self.config.enable_retrieval:
            # Perform retrieval search
            retrieval_result = self._perform_retrieval(user_query)
            
            # Inject retrieved context if found relevant documents
            if retrieval_result and retrieval_result.matches:
                augmented_query = self._augment_query_with_context(user_query, retrieval_result)
                
                # Update context with augmented query
                if self.context_manager:
                    # Store original query
                    self.context_manager.manage_context_window('user', user_query)
                    
                    # Use augmented query for generation but don't store it
                    temp_context = self.context_manager.context_window.copy()
                    temp_context[-1]['content'] = augmented_query
                    
                    # Temporarily override context for generation
                    original_context = self.context_manager.context_window
                    self.context_manager.context_window = temp_context
                    
                    try:
                        # Generate response with augmented context
                        response, thinking = self.llm_manager.generate_chat_response(
                            thinking_model=thinking_model,
                            max_new_tokens=max_new_tokens
                        )
                    finally:
                        # Restore original context
                        self.context_manager.context_window = original_context
                else:
                    # Direct generation without context manager
                    response, thinking = self.llm_manager.generate_chat_response(
                        thinking_model=thinking_model,
                        max_new_tokens=max_new_tokens
                    )
            else:
                # No relevant documents found, proceed normally
                if self.context_manager:
                    self.context_manager.manage_context_window('user', user_query)
                
                response, thinking = self.llm_manager.generate_chat_response(
                    thinking_model=thinking_model,
                    max_new_tokens=max_new_tokens
                )
        else:
            # RAG disabled, use standard generation
            if self.context_manager:
                self.context_manager.manage_context_window('user', user_query)
            
            response, thinking = self.llm_manager.generate_chat_response(
                thinking_model=thinking_model,
                max_new_tokens=max_new_tokens
            )
        
        # Store assistant response in context
        if self.context_manager:
            self.context_manager.manage_context_window('assistant', response)
            if thinking:
                self.context_manager.manage_context_window('assistant-reasoning', thinking)
        
        logger.info(f"RAG response generated with retrieval: {retrieval_result is not None}")
        return response, thinking, retrieval_result

    def _perform_retrieval(self, query: str) -> Optional[SearchResult]:
        """
        Perform document retrieval for the given query.
        
        Args:
            query: Search query
            
        Returns:
            SearchResult or None if no relevant documents found
        """
        try:
            # Enhance query if configured
            search_query = self._enhance_query(query) if self.config.retrieval_query_enhancement else query
            
            # Perform retrieval search
            result = self.retrieval_interface.search_documents(
                query=search_query,
                max_results=self.config.max_retrieval_results
            )
            
            # Filter by minimum similarity score
            if result.matches:
                filtered_matches = [
                    match for match in result.matches 
                    if match.similarity_score >= self.config.min_similarity_score
                ]
                result.matches = filtered_matches
                result.total_matches = len(filtered_matches)
            
            logger.debug(f"Retrieved {len(result.matches)} relevant documents for query: '{query[:50]}...'")
            return result if result.matches else None
            
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query[:50]}...': {str(e)}")
            return None

    def _enhance_query(self, query: str) -> str:
        """
        Enhance the search query for better retrieval results.
        
        Args:
            query: Original query
            
        Returns:
            Enhanced query string
        """
        # Simple query enhancement - can be expanded with more sophisticated methods
        enhanced = query.strip()
        
        # Add context from recent conversation if available
        if self.context_manager and len(self.context_manager.context_window) > 1:
            recent_context = self.context_manager.context_window[-2:]
            context_terms = []
            for msg in recent_context:
                if msg['role'] in ['user', 'assistant'] and len(msg['content']) < 100:
                    context_terms.append(msg['content'])
            
            if context_terms:
                enhanced = f"{query} context: {' '.join(context_terms)}"
        
        return enhanced

    def _augment_query_with_context(self, query: str, retrieval_result: SearchResult) -> str:
        """
        Augment the user query with retrieved context.
        
        Args:
            query: Original user query
            retrieval_result: Results from document retrieval
            
        Returns:
            Augmented query with context
        """
        if not retrieval_result.matches:
            return query
        
        # Build context from retrieved documents
        context_parts = []
        
        for i, match in enumerate(retrieval_result.matches[:self.config.max_retrieval_results]):
            source_info = ""
            if self.config.include_source_metadata:
                source_info = f" (Source: {match.filepath})"
            
            context_parts.append(f"{i+1}. {match.content.strip()}{source_info}")
        
        context_text = "\n".join(context_parts)
        
        # Create augmented prompt
        augmented_query = f"""{query}

Based on the following relevant information from the knowledge base:

{context_text}

Please provide a comprehensive answer using this context where relevant."""
        
        logger.debug(f"Augmented query with {len(retrieval_result.matches)} context documents")
        return augmented_query

    def search_documents(self, query: str, **kwargs) -> SearchResult:
        """
        Direct document search interface.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            SearchResult with matching documents
        """
        return self.retrieval_interface.search_documents(query, **kwargs)

    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the retrieval system.
        
        Returns:
            Dictionary with retrieval statistics
        """
        # This could be expanded to include more detailed stats
        return {
            "config": {
                "enable_retrieval": self.config.enable_retrieval,
                "max_results": self.config.max_retrieval_results,
                "min_similarity": self.config.min_similarity_score,
                "context_size": self.config.context_size,
                "query_enhancement": self.config.retrieval_query_enhancement,
                "include_metadata": self.config.include_source_metadata
            }
        } 