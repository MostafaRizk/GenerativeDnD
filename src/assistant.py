class Assistant():
    def __init__(self, model, system_message):
        self.model = model
        self.system_message = system_message
        self.name = "assistant"
    
    def get_character_summary_from_bio(self, name, bio):
        prompt = f"Write a summary of {name} based on the following information: \n\n {bio}"
        history = [
                    {"role": "system", "content": f"{self.system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name)

if __name__ == "__main__":
    pass
