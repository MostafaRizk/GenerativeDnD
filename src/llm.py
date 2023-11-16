import json
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class LLM():
    def __init__(self, path="src/configs", file="thespis_params.json"):
        parameter_file = os.path.join(path, file)
        f = open(parameter_file)
        self.params = json.load(f)
        f.close()

        self.model = AutoModelForCausalLM.from_pretrained(self.params["model_name"],
                                                    device_map=self.params["device_map"],
                                                    trust_remote_code=bool(self.params["trust_remote_code"]),
                                                    revision=self.params["revision"])

        self.tokenizer = AutoTokenizer.from_pretrained(self.params["model_name"], use_fast=bool(self.params["use_fast"]))
        chat_template_file = os.path.join(path, self.params["chat_template"])
        f = open(chat_template_file)
        self.tokenizer.chat_template = f.read()
        f.close()
        self.assistant_token = self.params["assistant_token"]
        self.character_pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=self.params["character_params"]["max_new_tokens"],
            do_sample=self.params["character_params"]["do_sample"],
            temperature=self.params["character_params"]['temperature'],
            top_p=self.params["character_params"]["top_p"],
            top_k=self.params["character_params"]["top_k"],
            repetition_penalty=self.params["character_params"]["repetition_penalty"]
            )
        self.assistant_pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=self.params["assistant_params"]["max_new_tokens"],
            do_sample=self.params["assistant_params"]["do_sample"],
            temperature=self.params["assistant_params"]['temperature'],
            top_p=self.params["assistant_params"]["top_p"],
            top_k=self.params["assistant_params"]["top_k"],
            repetition_penalty=self.params["assistant_params"]["repetition_penalty"]
            )
    
    def inference_from_history(self, history, character_name, inference_type):
        if self.assistant_token == "":
            assistant_token = character_name + ": "
        else:
            assistant_token = self.assistant_token
        
        context = self.tokenizer.apply_chat_template(history, tokenize=False) + assistant_token
        
        if inference_type == "character":
            return self.character_pipe(context)[0]['generated_text'][len(context):]
        elif inference_type == "assistant":
            return self.assistant_pipe(context)[0]['generated_text'][len(context):]

if __name__ == "__main__":
    llm = LLM()
    system_message = "You are a helpful AI assistant"
    prompt = "What are you capable of?"
    context = f"{system_message}\n\nuser:{prompt}"
    print(llm.inference(context))
