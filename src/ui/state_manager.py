"""
UI state management and context window integration.

This module handles the state management for the Alexandria UI, including chat history,
thinking process display, and conversation context management.
"""
from typing import Optional, List, Dict, Tuple, TypeAlias
from prompt_toolkit.layout.controls import FormattedTextControl
from src.core.services.conversation_service import ConversationService, create_conversation_service, create_rag_conversation_service
from src.core.managers.rag_manager import RAGConfig
from src.core.services.service_right_pane import RightPaneService
from src.ui.markdown_formatter import MarkdownFormatter
from src.logger import get_module_logger
from src.utils.file_utils import save_llm_output

logger = get_module_logger(__name__)

# Type alias for formatted text used in prompt_toolkit
FormattedText: TypeAlias = List[Tuple[str, str]]

class StateManager:
    def __init__(
        self,
        chat_control: FormattedTextControl,
        thinking_control: FormattedTextControl,
        conversation_service: ConversationService,
        enable_rag: bool = True,
        rag_config: Optional[RAGConfig] = None
    ) -> None:
        """
        Initialize the state manager.
        
        Args:
            chat_control: Control for displaying chat messages in the UI
            thinking_control: Control for displaying thinking/reasoning process in the UI
            conversation_service: Service handling conversation state and context
            enable_rag: Whether RAG capabilities are enabled
            rag_config: Optional RAG configuration settings
        
        Returns:
            None
        """
        self.chat_control = chat_control
        self.thinking_control = thinking_control
        self.conversation_service = conversation_service
        self.enable_rag = enable_rag
        self.rag_config = rag_config
        self.markdown_formatter = MarkdownFormatter()
        self.right_pane_service = RightPaneService(self.conversation_service.messages_controller)
        # Store the latest retrieval info for saving
        self.latest_retrieval_info: Optional[Dict] = None
        # Initialize empty state
        self.chat_control.text = []
        self.thinking_control.text = []
        
        # Load initial conversation state
        if conversation_service.conversation_id:
            self._load_right_pane_messages()
            self._load_initial_conversation()
        
        # Log RAG status
        if self.enable_rag and hasattr(self.conversation_service, 'is_rag_enabled'):
            logger.info(f"RAG enabled in UI: {self.conversation_service.is_rag_enabled}")
        else:
            logger.info("RAG not enabled in UI")

    def _format_message(self, role: str, content: str) -> FormattedText:
        """
        Format a message for display in the UI with Markdown support.
        
        Args:
            role: Message role identifier ('user', 'assistant', 'system', 'assistant-reasoning', 'retrieval-info')
            content: Raw message content to be formatted
            
        Returns:
            FormattedText: Formatted message with role header, Markdown rendering, and spacing
        """
        role_display = {
            'user': 'You',
            'assistant': 'LLM',
            'system': 'System',
            'assistant-reasoning': 'Thoughts',
            'retrieval-info': 'Knowledge Base'
        }
        
        display_role = role_display.get(role, role.title())
        
        # Use special styling for knowledge base role
        if role == 'retrieval-info':
            header = [("class:knowledge-base", f"{display_role}:\n\n")]
        else:
            header = [("class:role", f"{display_role}:\n\n")]
        
        # Convert content to formatted text with Markdown support
        formatted_content = self.markdown_formatter.convert_to_formatted_text(content)
        
        # Add spacing after message
        footer = [("", "\n")]
        
        return header + formatted_content + footer
    
    def _load_initial_conversation(self) -> None:
        """
        Load the current conversation from the context window into the UI.
        Formats and displays all messages in reverse chronological order.
        
        Returns:
            None
        """
        chat_text: FormattedText = []
        
        # Get messages from context window in reverse order
        for message in reversed(self.conversation_service.context_window):
            role = message.get('role')
            content = message.get('content', '')
            
            if role != 'system':
                formatted_msg = self._format_message(role, content)
                chat_text.extend(formatted_msg)
        
        # Update UI controls with messages in reverse chronological order
        self.chat_control.text = chat_text

    def _load_right_pane_messages(self) -> None:
        """
        Load the right pane messages for the conversation, displaying the AI's
        thinking process and reasoning.
        
        Returns:
            None
        """
        thinking_text: FormattedText = []
        for message in self.right_pane_service.get_thinking_messages(self.conversation_service.conversation_id):
            formatted_msg = self._format_message('assistant-reasoning', message)
            thinking_text.extend(formatted_msg)
        self.thinking_control.text = thinking_text
        logger.info(f"Right pane messages: {thinking_text}")
        
    def append_user_message(self, message: str) -> None:
        """
        Append a user message to both UI and context window.
        
        This method is used for standard generation (Ctrl+Space) where the state manager
        handles both UI and context updates.
        
        Args:
            message: The user's message content to be added
            
        Returns:
            None
        """
        formatted_message = self._format_message('user', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        
        # Add to context window for standard generation
        self.conversation_service.manage_context_window("user", message)
        
    def append_assistant_message(self, message: str, thinking: Optional[str] = None, retrieval_info: Optional[Dict] = None) -> None:
        """
        Append an assistant message to UI and context window.
        
        This method is used for standard generation (Ctrl+Space) where the state manager
        handles both UI and context updates.
        
        Args:
            message: The assistant's response content
            thinking: Optional thinking/reasoning process to display in right pane
            retrieval_info: Optional information about retrieved documents
            
        Returns:
            None
        """
        # Store retrieval info for saving
        if retrieval_info:
            self.latest_retrieval_info = retrieval_info
        
        # Handle thinking process
        if thinking:
            formatted_thinking = self._format_message('assistant-reasoning', thinking)
            self.thinking_control.text = formatted_thinking + self.thinking_control.text
            # Add thinking to context window for standard generation
            self.conversation_service.manage_context_window("assistant-reasoning", thinking)
            logger.debug(f"Appending assistant reasoning message: {thinking}")

        # Handle retrieval information in the right pane
        if retrieval_info and retrieval_info.get('total_matches', 0) > 0:
            retrieval_text = self._format_retrieval_info(retrieval_info)
            formatted_retrieval = self._format_message('retrieval-info', retrieval_text)
            
            # Add retrieval info to thinking pane
            if thinking:
                # Insert retrieval info after thinking
                self.thinking_control.text = formatted_retrieval + self.thinking_control.text
            else:
                # Add retrieval info alone if no thinking
                self.thinking_control.text = formatted_retrieval + self.thinking_control.text
            
            logger.info(f"Added retrieval info to thinking pane: {retrieval_info['total_matches']} documents")

        # Format and display main assistant message (without retrieval info)
        formatted_message = self._format_message('assistant', message)
        self.chat_control.text = formatted_message + self.chat_control.text
        
        # Add assistant message to context window for standard generation
        self.conversation_service.manage_context_window("assistant", message)
        logger.debug(f"Appending assistant message: {message}")

    def _format_retrieval_info(self, retrieval_info: Dict) -> str:
        """
        Format retrieval information for display in the thinking pane.
        
        Args:
            retrieval_info: Dictionary containing retrieval results
            
        Returns:
            str: Formatted retrieval information text
        """
        total_matches = retrieval_info.get('total_matches', 0)
        matches = retrieval_info.get('matches', [])
        search_time = retrieval_info.get('search_time_ms', 0)
        
        if total_matches == 0:
            return "No relevant documents found in knowledge base."
        
        # Header with summary
        lines = [
            f"Retrieved {total_matches} document(s) from knowledge base",
            f"Search completed in {search_time:.1f}ms",
            ""
        ]
        
        # List each document with similarity score
        lines.append("Documents used:")
        for i, match in enumerate(matches, 1):
            filepath = match.get('filepath', 'Unknown')
            similarity = match.get('similarity_score', 0.0)
            lines.append(f"  {i}. {filepath} (relevance: {similarity:.3f})")
        
        return "\n".join(lines)

    def reset_state(self) -> None:
        """
        Reset both UI controls and create a new conversation manager instance.
        
        Returns:
            None
        """
        self.chat_control.text = []
        self.thinking_control.text = []
        self.latest_retrieval_info = None
        
        # Create new conversation service with same RAG settings
        if self.enable_rag:
            self.conversation_service = create_rag_conversation_service(rag_config=self.rag_config)
        else:
            self.conversation_service = create_conversation_service()
        
        # Update right pane service
        self.right_pane_service = RightPaneService(self.conversation_service.messages_controller)

    def save_current_output(self) -> Optional[str]:
        """
        Save the most recent LLM output to a markdown file.
        
        Returns:
            Optional[str]: Path to the saved file if there was output to save, None otherwise
        """
        # Get the most recent assistant message by iterating in reverse order
        latest_assistant_message = None
        for message in reversed(self.conversation_service.context_window):
            if message.get('role') == 'assistant':
                latest_assistant_message = message
                break
        
        if latest_assistant_message:
            content = latest_assistant_message.get('content', '')
            
            # Get the most recent thinking message
            thinking_messages = self.right_pane_service.get_thinking_messages(self.conversation_service.conversation_id)
            thinking = thinking_messages[0] if thinking_messages else None
            
            # Use stored retrieval info if available
            retrieval_info_text = None
            if self.latest_retrieval_info and self.latest_retrieval_info.get('total_matches', 0) > 0:
                retrieval_info_text = self._format_retrieval_info(self.latest_retrieval_info)
            
            # Save to file
            saved_path = save_llm_output(content, thinking, retrieval_info_text)
            logger.info(f"Manually saved latest LLM output to: {saved_path}")
            return saved_path
        
        logger.info("No assistant message found to save")
        return None

    def get_chat_text(self) -> FormattedText:
        """
        Get current chat text.
        
        Returns:
            FormattedText: Current formatted chat text
        """
        return self.chat_control.text

    def get_thinking_text(self) -> FormattedText:
        """
        Get current thinking text.
        
        Returns:
            FormattedText: Current formatted thinking text
        """
        return self.thinking_control.text

