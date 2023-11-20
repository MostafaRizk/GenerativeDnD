import json
from llm import LLM
from assistant import Assistant
from collections import deque

class Character():
    def __init__(self, bio_file):
        f = open(bio_file)
        self.bio = json.load(f)
        f.close()
        self.name = self.bio["name"]
        self.appearance = self.bio["initial_appearance"]
    
    def speak(self):
        pass

    def listen(self):
        pass


class PlayerCharacter(Character):
    def __init__(self, bio_file):
        Character.__init__(self, bio_file)
    
    def speak(self):
        response = input()
        return response

    def listen(self, content, other_character, other_role):
        pass

class NonPlayerCharacter(Character):
    roleplay_prompt = "Roleplay as a Dungeons and Dragons character with the following description: "
    
    def __init__(self, bio_file, model, assistant, client=None):
        Character.__init__(self, bio_file)
        self.model = model
        self.assistant = assistant
        self.client = client
        self.description = self.generate_description()
        self.system_message = f"{self.roleplay_prompt}{self.description}"
        self.chat_history = deque([self.system_message])
        self.plan = []
    
    def add_system_message(self):
        self.chat_history.appendleft({"role": "system", "content": f"{self.system_message}"})

    def generate_description(self):
        facts = "\n".join([self.bio["initial_appearance"]] + self.bio['initial_facts'])
        summary = self.assistant.get_character_summary_from_bio(self.name, facts)
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
                message = self.model.inference_from_history(self.chat_history, self.name, inference_type="character")
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
    
    def listen(self, content, other_character_name, other_role):
        message = {"role": f"{other_role}", "content": f"{content}", "character": f"{other_character_name}"}
        self.chat_history.append(message)

if __name__ == "__main__":
    model = LLM()
    character = Character("src/assets/Bazza_Summerwood.json", model)
    history = character.generate_history()
    response = character.speak(history)
    print(response)