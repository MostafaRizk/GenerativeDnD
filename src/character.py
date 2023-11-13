import json
from llm import LLM

class Character():
    roleplay_prompt = "Roleplay as a Dungeons and Dragons character with the following description: "
    
    def __init__(self, bio_file, model, client=None):
        self.model = model
        self.client = client
        f = open(bio_file)
        self.bio = json.load(f)
        f.close()
        self.name = self.bio["name"]
        self.description = self.generate_description()
        self.system_message = f"{self.roleplay_prompt}{self.description}"
    
    def generate_description(self):
        return "\n".join(self.bio["facts"])
    
    def generate_history(self):
        history = [
                    {"role": "system", "content": f"{self.system_message}", "character": f"{self.name}"},
                    {"role": "user", "content": f"Hello there, tell me about yourself.", "character": f"Lorde"},
                    {"role": "assistant", "content": "Well what would you like to know, my boy?", "character": f"{self.name}"},
                    {"role": "user", "content": f"I dunno. What are your hobbies?", "character": f"Lorde"},
                    {"role": "assistant", "content": "", "character": f"{self.name}"}
                ]
        return history

    def speak(self, history):
        return self.model.inference_from_history(history, self.name)

if __name__ == "__main__":
    model = LLM()
    character = Character("src/assets/Bazza_Summerwood.json", model)
    history = character.generate_history()
    response = character.speak(history)
    print(response)