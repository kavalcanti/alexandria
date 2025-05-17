'''
LLM Prompt Controller placeholder
'''

class LLMPromptManager:
    def __init__(self):

        # Loads system prompts.
        # Handles prompt injection.
        # Defines specialist prompts.
        self._default_system_prompt = """You are a powerful assistant. Keep your responses concise and to the point."""

        pass

    def get_system_prompt(self):
        """
        Get the system prompt.
        """
        return self._default_system_prompt
    
    def user_prompt_injector(self, user_message: str, retrieval_context: str = None) -> str:
        """
        Inject the user prompt into the system prompt.
        """
        if retrieval_context:
            return f"{user_message} Here is what we currently know about it: {retrieval_context}"
        else:
            return user_message