from vllm import LLM
from vllm.sampling_params import SamplingParams


llm_name = "Qwen/Qwen3-1.7B"
local_llm_dir = f"ai_models/{llm_name}"

sampling_params = SamplingParams(max_tokens=8192, temperature=0.0)
llm = LLM(model=local_llm_dir, task="generate",gpu_memory_utilization=0.8, max_model_len=16384)  # Name or path of your model
# llm.apply_model(lambda model: print(type(model)))
