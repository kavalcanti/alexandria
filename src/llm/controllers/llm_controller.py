import os
from typing import Optional, Tuple, List, Any
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from src.logger import get_module_logger

logger = get_module_logger(__name__) 

class LLMController:
    """
    Controller class for managing LLM (Language Learning Model) operations.
    
    This class handles model loading, tokenization, and text generation using HuggingFace models.
    The model path is configured through the HF_MODEL environment variable.
    """
    def __init__(self) -> None:
        self.llm_name: str = os.getenv("HF_MODEL")
        self.local_llm_dir: str = f"ai_models/{self.llm_name}"
        self.llm_download_cache_dir: str = f"ai_models/cache"

        if not os.path.exists("ai_models"):
            os.makedirs("ai_models")
            os.makedirs(self.llm_download_cache_dir)
        logger.info(f"LLMController initialized with model: {self.llm_name}")
        self.tokenizer, self.model = self._load_local_llm()
        logger.info(f"LLMController initialized with tokenizer and model")

        return None

    def get_tokenizer(self) -> AutoTokenizer:
        """
        Returns the initialized tokenizer instance.
        
        Returns:
            AutoTokenizer: The HuggingFace tokenizer instance
        """
        return self.tokenizer
    
    def get_model(self) -> AutoModelForCausalLM:
        """
        Returns the initialized model instance.
        
        Returns:
            AutoModelForCausalLM: The HuggingFace model instance
        """
        return self.model
    
    def get_token_count(self, text: str) -> int:
        """
        Counts the number of tokens in the given text.
        
        Args:
            text (str): The input text to tokenize
            
        Returns:
            int: Number of tokens in the text
        """
        return len(self.tokenizer.encode(text))


    def _load_local_llm(self) -> Tuple[AutoTokenizer, AutoModelForCausalLM]:
        """
        Loads or downloads the LLM model and tokenizer.
        
        This method checks if the model exists in the local directory. If not, it downloads
        the model from HuggingFace, saves it locally, and then reloads it from the local
        directory to ensure consistent loading behavior.
        
        Returns:
            tuple: (AutoTokenizer, AutoModelForCausalLM) The loaded tokenizer and model instances
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

    def _parse_llm_response(self, model_outputs: torch.Tensor, model_inputs: Any) -> Tuple[str, Optional[str]]:
        """
        Parses the raw LLM output to extract generated text and thinking content.
        
        This method processes the model's output tokens, separating the thinking content
        (marked by special tokens) from the actual response content.
        
        Args:
            model_outputs: Raw output tensors from the model
            model_inputs: Input tensors provided to the model
            
        Returns:
            tuple: (content, thinking_content)
                - content (str): The main generated response text
                - thinking_content (str|None): The extracted thinking process, if available
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
    
    def generate_response_from_context(
        self,
        context_window: List[dict],
        thinking_model: bool = True,
        max_new_tokens: int = 8096
    ) -> Tuple[str, Optional[str]]:
        """
        Generates LLM output using the provided context window as input.
        
        This method handles the LLM interaction, including tokenization and generation,
        but does not manage conversation state.
        
        Args:
            context_window (list): List of conversation messages
            thinking_model (bool): Whether to use the model's reasoning capability
            max_new_tokens (int): Maximum number of tokens to generate
            
        Returns:
            tuple: (answer_content, thinking_content)
                - answer_content (str): The main generated response
                - thinking_content (str|None): The model's reasoning process, if enabled
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

