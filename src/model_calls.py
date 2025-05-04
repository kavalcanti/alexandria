# from llm_models import load_local_llm

# tokenizer, model = load_local_llm()


# def generate_response(message, history=[], ):


#     # prepare the model input
#     prompt = message
#     messages = [
#         {"role": "user", "content": prompt}

#     ]
#     text = tokenizer.apply_chat_template(
#         messages,
#         tokenize=False,
#         add_generation_prompt=True,
#         enable_thinking=True # Switches between thinking and non-thinking modes. Default is True.
#     )

#     print(text)

#     model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

#     # conduct text completion
#     generated_ids = model.generate(
#         **model_inputs,
#         max_new_tokens=32768
#     )
#     output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

#     # parsing thinking content
#     try:
#         # rindex finding 151668 (</think>)
#         index = len(output_ids) - output_ids[::-1].index(151668)
#     except ValueError:
#         index = 0

#     thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
#     content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

#     return thinking_content, content


# prompt = 'Provide a brief overview of AWK.'

# thinking_content, content = generate_response(prompt)

# print("thinking content:", thinking_content)
# print("content:", content)

# model = None
# tokenizer = None