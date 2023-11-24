import json
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from auto_gptq import exllama_set_max_input_length

class LLM():
    def __init__(self, config_path="configs", file="thespis_params.json"):
        current_path = os.getcwd()
        parameter_file = os.path.join(current_path, config_path, file)
        f = open(parameter_file)
        self.params = json.load(f)
        f.close()
        self.context_size = self.params["context_size"]
        self.observation_size = self.params["summary_params"]["max_new_tokens"]

        self.model = AutoModelForCausalLM.from_pretrained(self.params["model_name"],
                                                    device_map=self.params["device_map"],
                                                    trust_remote_code=bool(self.params["trust_remote_code"]),
                                                    revision=self.params["revision"])
        
        self.model = exllama_set_max_input_length(self.model, self.context_size)

        self.tokenizer = AutoTokenizer.from_pretrained(self.params["model_name"], use_fast=bool(self.params["use_fast"]))
        chat_template_file = os.path.join(current_path, config_path, self.params["chat_template"])
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
        
        self.summary_pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=self.params["summary_params"]["max_new_tokens"],
            do_sample=self.params["summary_params"]["do_sample"],
            temperature=self.params["summary_params"]['temperature'],
            top_p=self.params["summary_params"]["top_p"],
            top_k=self.params["summary_params"]["top_k"],
            repetition_penalty=self.params["summary_params"]["repetition_penalty"]
            )
        
        self.planner_pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=self.params["planner_params"]["max_new_tokens"],
            do_sample=self.params["planner_params"]["do_sample"],
            temperature=self.params["planner_params"]['temperature'],
            top_p=self.params["planner_params"]["top_p"],
            top_k=self.params["planner_params"]["top_k"],
            repetition_penalty=self.params["planner_params"]["repetition_penalty"]
            )
    
    def inference_from_history(self, history, character_name, inference_type):
        if self.assistant_token == "":
            assistant_token = character_name + ": "
        else:
            assistant_token = self.assistant_token
        
        context = self.tokenizer.apply_chat_template(history, tokenize=False) + assistant_token
        
        if inference_type == "character":
            result = self.character_pipe(context)[0]['generated_text'][len(context):]
        elif inference_type == "summary":
            result = self.summary_pipe(context)[0]['generated_text'][len(context):]
        elif inference_type == "planner":
            result = self.planner_pipe(context)[0]['generated_text'][len(context):]
        
        torch.cuda.empty_cache()

        return result

if __name__ == "__main__":
    llm = LLM()
    system_message = "You are a helpful AI assistant"
    prompt = "What are you capable of?"
    context = f"{system_message}\n\nuser:{prompt}"
    print(llm.inference(context))
