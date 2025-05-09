import asyncio
# from vllm.sampling_params import SamplingParams
# from vllm import AsyncLLMEngine, AsyncEngineArgs

from vllm import AsyncEngineArgs, SamplingParams, LLM
from vllm.engine.async_llm_engine import AsyncLLMEngine

import os
from contextlib import redirect_stderr, redirect_stdout


## ---- ###

# from vllm import AsyncEngineArgs, SamplingParams
# from vllm.engine.async_llm_engine import AsyncLLMEngine
# import asyncio
# class ConversationHandler:
#     def __init__(self, vllm_model, context_window_len=5):
#         self.local_llm_dir = f"ai_models/(vllm_model)"
#         self.sampling_params = SamplingParams(max_tokens=8192, temperature=0.0)
#         engine_args = AsyncEngineArgs(model=self.local_llm_dir, task="generate", gpu_memory_utilization=0.8, max_model_len=16384, disable_log_stats=True)
#         self.engine = AsyncLLMEngine.from_engine_args(engine_args)
#         self.context_window = []
#         self.context_window_len = context_window_len

#     async def chat_completion(self):
#         # Manually apply chat template (example, adjust as needed)
#         tokenizer = await self.engine.get_tokenizer()
#         prompt = tokenizer.apply_chat_template(self.context_window, tokenize=False, add_generation_prompt=True)
#         request_id = "your_unique_id"
#         async for output in self.engine.generate(prompt, self.sampling_params, request_id):
#             return output


## ---- ###


 # Name or path of your model

class ConversationHandler:
    def __init__(self, vllm_model, context_window_len=5):

        self.local_llm_dir = f"ai_models/{vllm_model}"
        self.sampling_params = SamplingParams(max_tokens=8192, temperature=0.0)

        # engine_args = AsyncEngineArgs(model=self.local_llm_dir, task="generate", gpu_memory_utilization=0.8, max_model_len=16384, disable_log_stats=True)
        # self.engine = AsyncLLMEngine.from_engine_args(engine_args)

        self.llm = LLM(model=self.local_llm_dir, task="generate", gpu_memory_utilization=0.8, max_model_len=16384,disable_log_stats=True) 
        
        self.context_window = []
        self.context_window_len = context_window_len

    def chat_completion(self):

        # tokenizer = await self.engine.get_tokenizer()
        # prompt = tokenizer.apply_chat_template(self.context_window, tokenize=False, add_generation_prompt=True)
        # request_id = "your_unique_id"
        # async for output in self.engine.generate(prompt, self.sampling_params, request_id):
        #     print(output)
        #     return output

        llm_response_object = self.llm.chat(self.context_window, sampling_params=self.sampling_params)
        print(self.context_window)

        return llm_response_object


    def llm_response_parser(self, llm_response_object):

        raw_response = llm_response_object[0].outputs[0].text

        think_token = "</think>"
        idx = raw_response.find(think_token)

        llm_response = raw_response[idx+9:-1]

        return llm_response

    def context_window_manager(self, role, message):

        formatter = {
            "role":role,
            "message":message 
        }

        system_prompt = self.context_window[0] if self.context_window and self.context_window[0]["role"] == "system" else None

        if system_prompt and len(self.context_window) >= self.context_window_len:
            self.context_window.pop(2)
            self.context_window.append(formatter)
        elif len(self.context_window) >= self.context_window_len:
            self.context_window.pop(1)
            self.context_window.append(formatter)
        else:
            self.context_window.append(formatter)

        return None

# conversation = [
#     {
#         "role": "system",
#         "content": "You are a helpful assistant"
#     },
#     {
#         "role": "user",
#         "content": "Hello"
#     },
#     {
#         "role": "assistant",
#         "content": "Hello! How can I assist you today?"
#     },
#     {
#         "role": "user",
#         "content": "Tell me about the AWK command.",
#     },
# ]

# # response = llm.chat(conversation, sampling_params=sampling_params)
# # print(response)
