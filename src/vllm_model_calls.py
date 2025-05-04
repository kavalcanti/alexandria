
from vllm.sampling_params import SamplingParams
from vllm import LLM
import os
from contextlib import redirect_stderr, redirect_stdout


llm_name = "Qwen/Qwen3-1.7B"
local_llm_dir = f"ai_models/{llm_name}"


sampling_params = SamplingParams(max_tokens=8192, temperature=0.0)
llm = LLM(model=local_llm_dir, task="generate",gpu_memory_utilization=0.8, max_model_len=16384,disable_log_stats=True)  # Name or path of your model

# class ConversationHandler:
#     def __init__(self, vllm_model):




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
