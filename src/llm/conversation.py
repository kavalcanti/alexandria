import os
from transformers import AutoTokenizer, AutoModelForCausalLM
from src.logger import *
from src.llm.llm_db_loggers import *

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

        # Initialize directories
        self.llm_name = llm_name
        self.local_llm_dir = f"ai_models/{llm_name}"
        self.llm_download_cache_dir = f"ai_models/cache"

        if not os.path.exists("ai_models"):
            os.makedirs("ai_models")
            os.makedirs(self.llm_download_cache_dir)

        # Load llm and storage objects
        self.tokenizer, self.model = self._load_local_llm()
        self.context_window_len = context_window_len
        self.db_storage = DatabaseStorage()

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

    def _load_local_llm(self):
        """
            Checks if the model exists in the local dir. Loads or downloads them accordingly.
            A cache wipe will be implemented soon, hence offloading the model after download.
        """

        if len(os.listdir(self.local_llm_dir)) == 0:
            
            if not os.path.exists(self.local_llm_dir):
                os.makedirs(self.local_llm_dir)
            
            tokenizer = AutoTokenizer.from_pretrained(self.llm_name, cache_dir=self.llm_download_cache_dir)
            model = AutoModelForCausalLM.from_pretrained(self.llm_name, torch_dtype="auto", device_map="auto", cache_dir=self.llm_download_cache_dir)

            model.save_pretrained(self.local_llm_dir)
            tokenizer.save_pretrained(self.local_llm_dir)

            tokenizer = None
            model = None

        tokenizer = AutoTokenizer.from_pretrained(self.local_llm_dir)
        model = AutoModelForCausalLM.from_pretrained(self.local_llm_dir, torch_dtype="auto", device_map="auto")

        return tokenizer, model

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

    def _parse_llm_response(self, model_outputs, model_inputs):
        """
        Parses the raw llm output to extract vectors, then decodes generated text. 
        Only reasoning token is treated currently.
        Saves llm output and token counts to database.
        """
        llm_output = model_outputs[0][len(model_inputs.input_ids[0]):].tolist()

        try:
            # Find 151668 (</think>) token idx
            index = len(llm_output) - llm_output[::-1].index(151668)
        except ValueError:
            index = 0

        if index != 0:
            llm_output_think = llm_output[:index]
            llm_output_content = llm_output[index:]

            llm_output_think.pop()
            llm_output_think.pop(0)

            thinking_content = self.tokenizer.decode(llm_output_think, skip_special_tokens=True).strip("\n")
            content = self.tokenizer.decode(llm_output_content, skip_special_tokens=True).strip("\n")

            # Store messages in a consistent order - first reasoning, then response
            if thinking_content:
                self.manage_context_window("assistant-reasoning", thinking_content)
            self.manage_context_window("assistant", content)

        else:
            thinking_content = None
            content = self.tokenizer.decode(llm_output, skip_special_tokens=True).strip("\n")
            self.manage_context_window("assistant", content)

        return content, thinking_content

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
        text = self.tokenizer.apply_chat_template(
            self.context_window,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=thinking_model
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        model_outputs = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens
        )

        llm_answer, llm_thinking = self._parse_llm_response(model_outputs, model_inputs)

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

        # Generate title using the model
        text = self.tokenizer.apply_chat_template(
            title_prompt,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # No need for thinking mode for title generation
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        model_outputs = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens
        )

        # Extract the generated title
        title_output = model_outputs[0][len(model_inputs.input_ids[0]):].tolist()
        title = self.tokenizer.decode(title_output, skip_special_tokens=True).strip("\n")

        # Update the conversation title in the database
        self.db_storage.update_conversation_title(self.conversation_id, title)
