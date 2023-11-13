import json
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class LLM():
    def __init__(self, parameter_file="src/configs/llm_params_default.json"):
        f = open(parameter_file)
        self.params = json.load(f)
        f.close()

        self.model = AutoModelForCausalLM.from_pretrained(self.params["model_name"],
                                                    device_map=self.params["device_map"],
                                                    trust_remote_code=bool(self.params["trust_remote_code"]),
                                                    revision=self.params["revision"])

        self.tokenizer = AutoTokenizer.from_pretrained(self.params["model_name"], use_fast=bool(self.params["use_fast"]))
        
    
    def inference(self, context):
        input_ids = self.tokenizer(prompt, return_tensors='pt').input_ids.cuda()
        output = self.model.generate(inputs=input_ids, 
                                     temperature=self.params['temperature'], 
                                     do_sample=self.params["do_sample"], 
                                     top_p=self.params["top_p"], 
                                     top_k=self.params["top_k"], 
                                     max_new_tokens=self.params["max_new_tokens"])
        return self.tokenizer.decode(output[0])

if __name__ == "__main__":
    llm = LLM()
    system_message = "You are a helpful AI assistant"
    prompt = "What are you capable of?"
    context = f"{system_message}\n\nuser:{prompt}"
    print(llm.inference(context))
