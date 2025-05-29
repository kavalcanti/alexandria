from typing import List, Dict, Any
from src.core.context.prompt_manager import LLMPromptManager

class ContextWindow:
    """Manages a conversation context window for LLM interactions.
    This class maintains SSoT for the conversation context passed to the LLM.
    It also handles the RAG retrieval context and the system prompt.
    """
    
    def __init__(self, conversation_id: int, prompt_manager: LLMPromptManager, context_window_len: int = 5, initial_context: List[Dict[str, str]] = None):
        self.prompt_manager = prompt_manager
        self.conversation_id = conversation_id
        self.context_window_len = context_window_len
        
        if initial_context:
            self.context_window = initial_context
        else:
            # Create system prompt for new conversations
            self.system_prompt = {'role': 'system', 
                                  'content': self.prompt_manager.get_system_prompt()}
            self.context_window = [self.system_prompt]

    def get_context_window(self):
        return self.context_window

    def add_message(self, role: str, message: str):
        self.context_window.append({'role': role, 'content': message})
        self._trim_context_window_to_max_len()

    def add_rag_user_message(self, message: str, retrieval_context: str):
        self.context_window.append(self.prompt_manager.insert_retrieval_in_usr_msg(message, retrieval_context))
        self._trim_context_window_to_max_len()

    def update_rag_system_prompt(self, retrieval_context: str):
        prompt = self.prompt_manager.insert_retrieval_in_system_prompt(retrieval_context)
        self.system_prompt = {'role': 'system', 'content': prompt}
        self.context_window[0] = self.system_prompt
        self._trim_context_window_to_max_len()

    def _trim_context_window_to_max_len(self):
        if len(self.context_window) > self.context_window_len:
            tmp_context_window = self.context_window[-self.context_window_len:]
            self.context_window = [self.system_prompt] + tmp_context_window
            
    def get_title_generation_context(self) -> List[Dict[str, str]]:
        system_prompt_content = self.prompt_manager.get_conversation_title_prompt()
        system_prompt = {'role': 'system', 'content': system_prompt_content}
        return [system_prompt] + self.context_window[-2:]

