# import os
# from transformers import AutoTokenizer, AutoModelForCausalLM

# llm_name = "Qwen/Qwen3-1.7B"
# local_llm_dir = f"ai_models/{llm_name}"

# def load_local_llm(llm_name=False):

#     if not llm_name:
#         llm_name = "Qwen/Qwen3-1.7B"

#     local_llm_dir = f"ai_models/{llm_name}"

#     if not os.path.exists(local_llm_dir):
#         os.makedirs(local_llm_dir)

#         tokenizer = AutoTokenizer.from_pretrained(llm_name)
#         model = AutoModelForCausalLM.from_pretrained(llm_name, torch_dtype="auto", device_map="auto")

#         model.save_pretrained(local_llm_dir)
#         tokenizer.save_pretrained(local_llm_dir)

#         tokenizer = None
#         model = None

#     tokenizer = AutoTokenizer.from_pretrained(local_llm_dir)
#     model = AutoModelForCausalLM.from_pretrained(local_llm_dir, torch_dtype="auto", device_map="auto")

#     return tokenizer, model

