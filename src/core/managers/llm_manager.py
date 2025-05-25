from typing import List, Dict, Tuple, Optional, Any

from src.core.memory.llm_db_cnvs import ConversationsController
from src.infrastructure.llm_controller import LLMController
from src.infrastructure.embedder import Embedder
from src.logger import get_module_logger

logger = get_module_logger(__name__) 

class LLMManager:
    def __init__(self, 
                 msg_service: Optional[Any] = None,
                 conversation_id: Optional[int] = None, 
                 load_latest_system: bool = True,
                 conversations_controller: Optional[ConversationsController] = None,
                 llm_controller: Optional[LLMController] = None,
                 embedder: Optional[Embedder] = None) -> None:
        """Initialize the LLMManager.

        This class interacts with the context manager to get the context window and generate responses.

        Args:
            msg_service: Optional context manager instance that manages the context window.
                       If None, the service will maintain its own context window state.
            conversation_id: ID of the conversation. If None, creates a new conversation.
            load_latest_system: Whether to load only the latest system message (True) or all system messages (False).
            conversations_controller: Optional ConversationsController instance for dependency injection.
            llm_controller: Optional LLMController instance for dependency injection.

        Returns:
            None
        """
        # Load dependencies
        self.conversations_controller = conversations_controller or ConversationsController()
        self.llm_controller = llm_controller or LLMController()
        self.embedder = embedder or Embedder()
        self.conversation_id = conversation_id
        self.load_latest_system = load_latest_system
        
        # Store reference to context manager or initialize own context window
        self.context_manager = msg_service
        if self.context_manager is None:
            self._context_window: List[Dict[str, str]] = []
            logger.info("No context manager provided, using internal context window")
        else:
            logger.info(f"Context manager's context window loaded")
        
        return None

    def generate_chat_response(self, thinking_model: bool = True, max_new_tokens: int = 8096) -> Tuple[str, str]:
        """Generate LLM output using the context window as input.

        This method calls the parser to return decoded strings.
        
        Args:
            thinking_model: Whether to utilize Qwen's reasoning capabilities.
            max_new_tokens: Maximum number of new tokens to be generated.
            
        Returns:
            A tuple containing (llm_answer, llm_thinking) where:
                - llm_answer: The generated response
                - llm_thinking: The reasoning behind the response
        """
        # Get context window from appropriate source
        context_window = self.context_manager.context_window if self.context_manager else self._context_window

        # Check context window length for title generation
        window_len = len(context_window)
        
        if window_len in [3, 4]:  # One exchange (user + assistant) with optional system message
            self._generate_conversation_title()
        logger.info(f"Generating standard response.")
        logger.debug(f"Context window: {context_window}")
        llm_answer, llm_thinking = self.llm_controller.generate_response_from_context(
            context_window, 
            thinking_model, 
            max_new_tokens
        )
        logger.info(f"Standard response generated")
        logger.debug(f"Thinking: {llm_thinking}")
        logger.debug(f"Response: {llm_answer}")
      
        return llm_answer, llm_thinking

    def _generate_conversation_title(self, max_new_tokens: int = 120) -> None:
        """Generate a title for the conversation based on the first exchange.

        This method should be called after the first complete exchange (one user message and one assistant response).
        Will work with or without a system message present.
        
        Args:
            max_new_tokens: Maximum number of tokens for the generated title.
            
        Returns:
            None. Updates the conversation title in the database.
        """
        # Get context window from appropriate source
        context_window = self.context_manager.context_window[-2:] if self.context_manager else self._context_window
        window_len = len(context_window)
        
        if window_len not in [2, 3]:  # Ensure we have exactly one exchange (with optional system message)
            return
            
        # Create a prompt for title generation
        title_prompt = [
            {
                'role': 'system',
                'content': 'You summarise conversations to output a concise and descriptive title. Apply no formatting or emojis. (max 120 characters).'
            }
        ] + context_window

        title = self.llm_controller.generate_response_from_context(title_prompt, thinking_model=False, max_new_tokens=max_new_tokens)
        logger.info(f"Title: {title[0]}")
        logger.debug(f"context_window: {context_window}")
        title_embedding = self.embedder.embed(title[0])
        logger.info(f"Title embedding: {len(title_embedding)}")
        # Update the conversation title in the database
        self.conversations_controller.update_conversation_title(self.conversation_id, title[0], title_embedding)

    @property
    def context_window(self) -> List[Dict[str, str]]:
        """Get the current context window.
        
        Returns:
            The current context window as a list of message dictionaries.
        """
        return self.context_manager.context_window if self.context_manager else self._context_window

    @context_window.setter
    def context_window(self, value: List[Dict[str, str]]) -> None:
        """Update the context window.
        
        Args:
            value: The new context window value as a list of message dictionaries.
        """
        if self.context_manager:
            self.context_manager.context_window = value
        else:
            self._context_window = value 