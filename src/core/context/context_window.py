from typing import List, Dict, Any
from src.core.context.prompt_manager import LLMPromptManager
from src.core.memory.llm_db_msg import MessagesController
from src.core.memory.llm_db_cnvs import ConversationsController

class ContextWindow:
    def __init__(self, conversation_id: int, prompt_manager: LLMPromptManager, context_window_len: int = 5):
        self.prompt_manager = prompt_manager
        self.messages_controller = MessagesController()
        self.conversations_controller = ConversationsController()
        self.context_window_len = context_window_len

        if conversation_id:
            self.context_window = self.conversations_controller.get_context_window_messages(conversation_id, self.context_window_len)
        else:
            self.conversation_id = self.conversations_controller.get_next_conversation_id()
            self.conversations_controller.insert_single_conversation(self.conversation_id, 0, "", None)
            self.system_prompt = {'role': 'system', 
                                  'content': self.prompt_manager.get_system_prompt()}
            self.messages_controller.insert_single_message(self.conversation_id, 'system', self.system_prompt['content'], 0)
            self.context_window = [self.system_prompt]

    def get_context_window(self):
        return self.context_window

    def add_message(self, role: str, message: str):
        self.context_window.append({'role': role, 'content': message})
        self.messages_controller.insert_single_message(self.conversation_id, role, message, 0)
        self._trim_context_window_to_max_len()

    def add_rag_user_message(self, message: str, retrieval_context: str):
        self.context_window.append(self.prompt_manager.insert_retrieval_in_usr_msg(message, retrieval_context))
        self.messages_controller.insert_single_message(self.conversation_id, 'user', message, 0)
        self._trim_context_window_to_max_len()

    def update_rag_system_prompt(self, retrieval_context: str):
        prompt = self.prompt_manager.insert_retrieval_in_system_prompt(retrieval_context)
        self.system_prompt = {'role': 'system', 'content': prompt}
        self.context_window[0] = self.system_prompt
        self.messages_controller.insert_single_message(self.conversation_id, 'system', self.system_prompt['content'], 0)
        self._trim_context_window_to_max_len()

    def _trim_context_window_to_max_len(self):
        if len(self.context_window) > self.context_window_len:
            tmp_context_window = self.context_window[-self.context_window_len:]
            self.context_window = [self.system_prompt] + tmp_context_window
            

