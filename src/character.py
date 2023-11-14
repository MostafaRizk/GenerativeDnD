import json
from llm import LLM
from assistant import Assistant
from collections import deque

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
        self.chat_history = deque([self.system_message])
        self.plan = []
    
    def add_system_message(self):
        self.chat_history.appendleft({"role": "system", "content": f"{self.system_message}"})

    def generate_description(self):
        assistant = Assistant(self.model, "You are a helpful AI assistant. Your job is to summarise text.")
        facts = "\n".join(self.bio['facts'])
        summary = assistant.get_character_summary_from_bio(self.name, facts)
        # print("------")
        # print(summary)
        # print("------")
        return summary
    
    def update_description(self):
        self.description = self.generate_description()
        self.system_message = f"{self.roleplay_prompt}{self.description}"
        self.chat_history.popleft()
        self.add_system_message()

    def speak(self):
        done = False
        
        while not done:
            try:
                message = self.model.inference_from_history(self.chat_history, self.name)
                done = True
            except:
                self.chat_history.popleft()
                self.chat_history.popleft()
                self.add_system_message()
        
        cutoff_index = message.find("\n")
        if cutoff_index != -1:
            message = message[:cutoff_index]

        self.chat_history.append({"role": "assistant", "content": f"{message}", "character": f"{self.name}"})
        return message
    
    def listen(self, content, other_character, other_role):
        message = {"role": f"{other_role}", "content": f"{content}", "character": f"{other_character}"}
        self.chat_history.append(message)

if __name__ == "__main__":
    model = LLM()
    character = Character("src/assets/Bazza_Summerwood.json", model)
    history = character.generate_history()
    response = character.speak(history)
    print(response)