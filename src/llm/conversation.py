import os
from src.llm.llm_db_loggers import *
from src.llm.llm_handler import LLMHandler

# log_file = os.getenv("LOGFILE")

logger = logging.getLogger(__name__)

class ConversationHandler:
    def __init__(self, llm_name: str = "Qwen/Qwen3-0.6B", context_window_len: int = 5, conversation_id: int = None, load_latest_system: bool = True):
        """
            Conversation instance class. Will keep its context window according to set lenght.
            Initializes its DatabaseStorage and keeps a log of messages.
            Tested to work with Qwen3 Models. Defaults to Qwen3 0.6B.

            Params:
            llm_name: str HF LLM name. Defaults to Qwen3 0.6B
            context_window_len: int number of messages to keep in context window, including system message.
            conversation_id: int id of the conversation. If None, creates a new conversation.
            load_latest_system: bool whether to load only the latest system message (True) or all system messages (False)
        """

        # Load llm and storage objects 
        self.context_window_len = context_window_len
        self.db_storage = DatabaseStorage()
        self.llm_handler = LLMHandler()

        self.tokenizer = self.llm_handler.get_tokenizer()
        self.model = self.llm_handler.get_model()

        # Initialize conversation
        if conversation_id is None:
            # Create a new conversation
            self.conversation_id = self.db_storage.get_next_conversation_id()
            self.db_storage.insert_single_conversation(self.conversation_id)
        else:
            # Use existing conversation or create it if it doesn't exist
            self.conversation_id = conversation_id
            if not self.db_storage.conversation_exists(self.conversation_id):
                self.db_storage.insert_single_conversation(self.conversation_id)

        self.load_latest_system = load_latest_system

        # Load initial context window from database
        self.context_window = self._load_context_window()

        return None

    def _load_context_window(self):
        """
        Load context window from database with proper message ordering and system message handling.
        Returns a list of message dictionaries in the correct sequence.
        """
        # Get messages from database
        messages = self.db_storage.get_context_window_messages(
            self.conversation_id,
            self.context_window_len
        )

        # If we should only load the latest system message
        if self.load_latest_system:
            # Filter system messages
            system_messages = [msg for msg in messages if msg['role'] == 'system']
            non_system_messages = [msg for msg in messages if msg['role'] != 'system']
            
            # Only keep the latest system message if any exist
            if system_messages:
                latest_system = system_messages[-1]
                messages = [latest_system] + non_system_messages
            else:
                messages = non_system_messages

        # Ensure messages are in chronological order
        messages.sort(key=lambda x: x.get('timestamp', 0))
        
        return messages

    def manage_context_window(self, role: str, message: str):
        """
        Handles the context window by storing message in database and refreshing context.
        The context window is always loaded from the database to ensure consistency.
        Only user and assistant messages are included in the context window.
        Assistant reasoning messages are stored but not included in the context.
        """
        # Store the new message if it's a valid role
        if role in ['user', 'assistant', 'system', 'assistant-reasoning']:
            self.db_storage.insert_single_message(
                self.conversation_id,
                role,
                message,
                len(self.tokenizer.encode(message))  # Get token count
            )

            # Only refresh context window for messages that should be in it
            if role in ['user', 'assistant', 'system']:
                self.context_window = self._load_context_window()
        else:
            logger.warning(f"Invalid message role: {role}")

        return None

    def generate_chat_response(self, thinking_model: bool = True, max_new_tokens: int = 8096):
        """
            Generates llm output using the context window as input.
            Calls parser to return decoded strings.
            Params:
            thinking_model: str defaults to True to utilize Qwen's reasoning.
            max_new_tokens: int max new tokens to be generated
            Returns
            llm_anser: str answer to the user query
            llm_thinking: str reasoning process
        """

        self.db_storage.update_message_count(self.conversation_id)

        llm_answer, llm_thinking = self.llm_handler.generate_response_from_context(self.context_window, thinking_model, max_new_tokens)

        self.db_storage.update_message_count(self.conversation_id)
        
        # After the first exchange, generate a title for the conversation
        # Account for both cases: with and without system message
        if len(self.context_window) in [2, 3]:  # One exchange (user + assistant) with optional system message
            self.generate_conversation_title()
        
        return llm_answer, llm_thinking

    def generate_conversation_title(self, max_new_tokens: int = 50):
        """
        Generate a title for the conversation based on the first exchange between user and assistant.
        This method should be called after the first complete exchange (one user message and one assistant response).
        Will work with or without a system message present.
        
        Args:
            max_new_tokens: Maximum number of tokens for the generated title
            
        Returns:
            None, but updates the conversation title in the database
        """
        window_len = len(self.context_window)
        if window_len not in [2, 3]:  # Ensure we have exactly one exchange (with optional system message)
            return
            
        # Create a prompt for title generation
        title_prompt = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Based on the following exchange, generate a concise and descriptive title (max 50 characters)."
            }
        ] + self.context_window

        title = self.llm_handler.generate_response_from_context(title_prompt, thinking_model=False, max_new_tokens=max_new_tokens)

        # Update the conversation title in the database
        self.db_storage.update_conversation_title(self.conversation_id, title)
