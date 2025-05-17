'''
LLM Prompt Controller
'''

class LLMPromptController:
    def __init__(self, db_storage):
        self.db_storage = db_storage

    

    def get_prompt(self):
        return self.prompt_controller.get_prompt()
