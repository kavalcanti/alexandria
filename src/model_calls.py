import os
from transformers import AutoTokenizer, AutoModelForCausalLM
from src.logger import *
from src.llm_db_loggers import *

log_file = os.getenv("LOGFILE")

class ConversationHandler:
    def __init__(self, llm_name, context_window_len=5):

        if not llm_name:
            self.llm_name = "Qwen/Qwen3-1.7B"
        else:
            self.llm_name = llm_name
        
        self.context_window_len = context_window_len
        self.local_llm_dir = f"ai_models/{llm_name}"
        self.tokenizer, self.model = self._load_local_llm(self.llm_name)
        self.context_window = []
        self.db_storage = DatabaseStorage()

    def _load_local_llm(self, llm_name=False):

        if not os.path.exists(self.local_llm_dir):
            os.makedirs(self.local_llm_dir)

            tokenizer = AutoTokenizer.from_pretrained(self.llm_name)
            model = AutoModelForCausalLM.from_pretrained(self.llm_name, torch_dtype="auto", device_map="auto")

            model.save_pretrained(self.local_llm_dir)
            tokenizer.save_pretrained(self.local_llm_dir)

            tokenizer = None
            model = None

        tokenizer = AutoTokenizer.from_pretrained(self.local_llm_dir)
        model = AutoModelForCausalLM.from_pretrained(self.local_llm_dir, torch_dtype="auto", device_map="auto")

        return tokenizer, model


    def _parse_llm_response(self, llm_output):

        # Breaks output on specific tokens to separate thinking
        # TODO Base this on tokenizer.json

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

            self.db_storage.insert_single_message("assistant-reasoning", thinking_content, len(llm_output_think))
            self.db_storage.insert_single_message("assistant", content, len(llm_output_content))

            return content, thinking_content
        
        else:

            content = self.tokenizer.decode(llm_output, skip_special_tokens=True).strip("\n")

            self.db_storage.insert_single_message("assistant", content, len(llm_output_content))

            return content


    def generate_chat_response(self, thinking_model = True, max_new_tokens=8096):



        text = self.tokenizer.apply_chat_template(
            self.context_window,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=thinking_model
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens
        )
        
        llm_output = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

        last_user_message = self.context_window[-1]['content']

        logger(last_user_message, "debug.log")
        logger(model_inputs["input_ids"][0].size(0), "debug.log")
        self.db_storage.insert_single_message(self.context_window[-1]['role'], last_user_message, model_inputs["input_ids"][0].size(0))

        llm_answer, llm_thinking = self._parse_llm_response(llm_output)

        return llm_thinking, llm_answer


    def manage_context_window(self, role, message):

        formatter = {
            "role":role,
            "content":message 
        }

        system_prompt = self.context_window[0] if self.context_window and self.context_window[0]["role"] == "system" else None

        if system_prompt and len(self.context_window) > self.context_window_len:
            self.context_window.pop(1)
            self.context_window.append(formatter)
        elif len(self.context_window) >= self.context_window_len:
            self.context_window.pop(0)
            self.context_window.append(formatter)
        else:
            self.context_window.append(formatter)

        return None
