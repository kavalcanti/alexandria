import os
from openai import OpenAI
from typing import List, Dict, Tuple, Optional, Any
import re
from src.logger import get_module_logger
from src.core.memory.llm_db_msg import MessagesController

logger = get_module_logger(__name__)

class LLMController:
    """
    Controller class for managing LLM (Language Learning Model) operations.
    
    This class handles model interactions using vLLM server.
    """
    def __init__(self, messages_controller: Optional[MessagesController] = None) -> None:
        self.last_response = None
        self.messages_controller = messages_controller

        # Point to your local vLLM server
        self.client = OpenAI(
            api_key="EMPTY",  # vLLM doesn't require a real API key
            base_url=os.getenv("VLLM_SERVER_URL")
        )
        logger.info("LLMController initialized with vLLM server")

    def generate_response_from_context(
        self,
        context_window: List[dict],
        max_tokens: int = 8096,
        conversation_id: Optional[int] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Generates LLM output using the provided context window as input.
        
        Args:
            context_window (list): List of conversation messages
            max_tokens (int): Maximum number of tokens to generate
            conversation_id (int): Optional conversation ID for message storage
            
        Returns:
            tuple: (answer_content, thinking_content)
                - answer_content (str): The main generated response
                - thinking_content (str|None): The model's reasoning process, if enabled
        """
        try:
            # Get the last user message
            user_message = next((msg['content'] for msg in reversed(context_window) if msg['role'] == 'user'), None)

            logger.info(f"LLMController.generate_response_from_context called with max_tokens={max_tokens}")
            logger.info("Making OpenAI API call with parameters:")
            logger.info(f"- model: Qwen/Qwen3-0.6B")
            logger.info(f"- max_tokens: {max_tokens}")
            logger.info(f"- temperature: 0.7")

            self.last_response = self.client.chat.completions.create(
                model="Qwen/Qwen3-0.6B",  # This should be configurable
                messages=context_window,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            # Extract the response content
            content = self.last_response.choices[0].message.content
            
            # Store messages if we have a conversation ID
            if conversation_id and self.messages_controller:
                # Store user message with prompt tokens
                if user_message:
                    self.messages_controller.insert_single_message(
                        conversation_id=conversation_id,
                        role='user',
                        message=user_message,
                        token_count=self.last_response.usage.prompt_tokens
                    )
            
            # Parse thinking content from <think> tags
            thinking_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
            if thinking_match:
                thinking_content = thinking_match.group(1).strip()
                # Remove thinking content from main response
                answer_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                
                # Store thinking content if we have a conversation ID
                if conversation_id and self.messages_controller:
                    self.messages_controller.insert_single_message(
                        conversation_id=conversation_id,
                        role='assistant-reasoning',
                        message=thinking_content,
                        token_count=0  # Set thinking tokens to zero
                    )
            else:
                thinking_content = None
                answer_content = content

            # Store the main response in the database if we have a conversation ID
            if conversation_id and self.messages_controller:
                self.messages_controller.insert_single_message(
                    conversation_id=conversation_id,
                    role='assistant',
                    message=answer_content,
                    token_count=self.last_response.usage.completion_tokens  # Use full completion tokens
                )
            
            return answer_content, thinking_content
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

