'''
LLM Prompt Controller placeholder
'''

class LLMPromptController:
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