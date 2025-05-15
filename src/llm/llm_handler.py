import os
from transformers import AutoTokenizer, AutoModelForCausalLM

class LLMHandler:
    def __init__(self):

        self.llm_name = os.getenv("HF_MODEL")
        self.local_llm_dir = f"ai_models/{self.llm_name}"
        self.llm_download_cache_dir = f"ai_models/cache"

        if not os.path.exists("ai_models"):
            os.makedirs("ai_models")
            os.makedirs(self.llm_download_cache_dir)

        self.tokenizer, self.model = self._load_local_llm()

    def get_tokenizer(self):
        return self.tokenizer
    
    def get_model(self):
        return self.model

    def _load_local_llm(self):
        """
            Checks if the model exists in the local dir. Loads or downloads them accordingly.
            A cache wipe will be implemented soon, hence offloading the model after download.
        """

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

    def _parse_llm_response(self, model_outputs, model_inputs):
        """
        Parses the raw llm output to extract vectors, then decodes generated text. 
        Only reasoning token is treated currently.
        Returns the decoded content and thinking content without managing conversation state.
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
        else:
            thinking_content = None
            content = self.tokenizer.decode(llm_output, skip_special_tokens=True).strip("\n")

        return content, thinking_content
    
    def generate_response_from_context(self, context_window, thinking_model: bool = True, max_new_tokens: int = 8096):
        """
        Generates LLM output using the provided context window as input.
        This method only handles the LLM interaction, not conversation management.
        
        Args:
            context_window: List of conversation messages
            thinking_model: Whether to use the model's reasoning capability
            max_new_tokens: Maximum number of tokens to generate
            
        Returns:
            tuple: (answer_content, thinking_content)
        """
        text = self.tokenizer.apply_chat_template(
            context_window,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=thinking_model
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        model_outputs = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens
        )

        return self._parse_llm_response(model_outputs, model_inputs)

