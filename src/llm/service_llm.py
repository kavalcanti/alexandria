import os
from src.llm.llm_db_cnvs_controller import ConversationsController
from src.llm.llm_controller import LLMController

from src.logger import get_module_logger

logger = get_module_logger(__name__) 

class LLMService:
    def __init__(self, 
                 msg_service = None,
                 conversation_id: int = None, 
                 load_latest_system: bool = True,
                 conversations_controller: ConversationsController = None,
                 llm_handler: LLMController = None):
        """
        Interacts with the context manager to get the context window and generate responses.

        Params:
            msg_service: Optional ContextManager instance that manages the context window.
                       If None, the service will maintain its own context window state.
            conversation_id: int id of the conversation. If None, creates a new conversation.
            load_latest_system: bool whether to load only the latest system message (True) or all system messages (False)
            conversations_controller: Optional ConversationsController instance for dependency injection
            llm_handler: Optional LLMHandler instance for dependency injection
        """
        # Load dependencies
        self.conversations_controller = conversations_controller or ConversationsController()
        self.llm_handler = llm_handler or LLMController()
        self.conversation_id = conversation_id
        self.load_latest_system = load_latest_system
        
        # Store reference to context manager or initialize own context window
        self.context_manager = msg_service
        if self.context_manager is None:
            self._context_window = []
            logger.info("No context manager provided, using internal context window")
        else:
            logger.info(f"Context manager's context window loaded")
        
        return None

    def generate_chat_response(self, thinking_model: bool = True, max_new_tokens: int = 8096):
        """
        Generates llm output using the context window as input.
        Calls parser to return decoded strings.
        
        Params:
            thinking_model: str defaults to True to utilize Qwen's reasoning.
            max_new_tokens: int max new tokens to be generated
            
        Returns:
            tuple: (llm_answer, llm_thinking) containing the response and reasoning
        """
        # Get context window from appropriate source
        context_window = self.context_manager.context_window if self.context_manager else self._context_window

        # Check context window length for title generation
        window_len = len(context_window)
        
        if window_len in [2, 3]:  # One exchange (user + assistant) with optional system message
            self._generate_conversation_title()
        logger.info(f"Generating response.")
        logger.debug(f"Context window: {context_window}")
        llm_answer, llm_thinking = self.llm_handler.generate_response_from_context(
            context_window, 
            thinking_model, 
            max_new_tokens
        )
        logger.info(f"Response generated")
        logger.debug(f"Thinking: {llm_thinking}")
        logger.debug(f"Response: {llm_answer}")
      
        return llm_answer, llm_thinking

    def _generate_conversation_title(self, max_new_tokens: int = 120):
        """
        Generate a title for the conversation based on the first exchange between user and assistant.
        This method should be called after the first complete exchange (one user message and one assistant response).
        Will work with or without a system message present.
        
        Args:
            max_new_tokens: Maximum number of tokens for the generated title
            
        Returns:
            None, but updates the conversation title in the database
        """
        # Get context window from appropriate source
        context_window = self.context_manager.context_window if self.context_manager else self._context_window
        window_len = len(context_window)
        
        if window_len not in [2, 3]:  # Ensure we have exactly one exchange (with optional system message)
            return
            
        # Create a prompt for title generation
        title_prompt = [
            {
                "role": "system",
                "content": "You are an expert at summarizing conversations. Based on the following exchange, generate a concise and descriptive title (max 120 characters)."
            }
        ] + context_window

        title = self.llm_handler.generate_response_from_context(title_prompt, thinking_model=False, max_new_tokens=max_new_tokens)
        logger.info(f"Title: {title}")
        # Update the conversation title in the database
        self.conversations_controller.update_conversation_title(self.conversation_id, title)

    @property
    def context_window(self):
        """Get the current context window."""
        return self.context_manager.context_window if self.context_manager else self._context_window

    @context_window.setter
    def context_window(self, value):
        """Update the context window."""
        if self.context_manager:
            self.context_manager.context_window = value
        else:
            self._context_window = value
