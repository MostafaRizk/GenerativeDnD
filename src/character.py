import json
import os
import chromadb
import uuid
from llm import LLM
from assistant import Assistant
from collections import deque
from datetime import datetime

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
    
    def __init__(self, bio_file, model, assistant, client, world_file="assets/world_info.json"):
        Character.__init__(self, bio_file)
        self.model = model
        self.assistant = assistant
        f = open(world_file)
        self.world_info = json.load(f)
        f.close()
        self.name = self.bio["name"]

        self.client = client
        self.collection_name = "_".join([word.lower() for word in self.name.split()])
        context_size = model.context_size
        tokens_per_observation = model.observation_size
        
        # Half of the context should be allocated to memories retrieved from the database
        # Suppose the model has a context size of 4096 tokens and an observation is 200 tokens long
        # 4096/2 is 2048. 2048/200 is approximately 10. 
        # 10 retrieved memories should be prepended to the chat history
        self.history_allocation = (context_size // 2) // tokens_per_observation

        ########### WARNING! COMMENT OUT FOR NORMAL FUNCTIONALITY #############
        #client.delete_collection(name=self.collection_name)

        try:
            self.collection = client.get_collection(name=self.collection_name)
        except:
            self.initialise_memory()

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
    
    def initialise_memory(self):
        facts = [self.bio["initial_appearance"]] + self.bio['initial_facts'] + self.world_info["common_knowledge"]
        self.collection = self.client.create_collection(name=self.collection_name)
        current_datetime = str(datetime.now())
        self.collection.add(
            documents=facts,
            metadatas=[{"created_at": current_datetime, 
                        "accessed_at": current_datetime,
                        "type": "fact",
                        "importance": 10,
                        "retrieval_score": 0,
                        "citations": ""} for _ in range(len(facts))],
            ids=[str(uuid.uuid4()) for _ in range(len(facts))])
    
    def store_memory(self, memory, importance):
        current_datetime = str(datetime.now())
        self.collection.add(
            documents=[memory],
            metadatas=[{"created_at": current_datetime, 
                        "accessed_at": current_datetime,
                        "type": "observation",
                        "importance": importance,
                        "retrieval_score": 0,
                        "citations": ""}],
            ids=[str(uuid.uuid4())])
    
    def update_description(self):
        self.description = self.generate_description()
        self.system_message = f"{self.roleplay_prompt}{self.description}"
        self.chat_history.popleft()
        self.add_system_message()

    def speak(self):
        retrieved_memories = self.collection.query(query_texts=[self.chat_history[-1]['content']],
                              n_results=self.history_allocation)
        memories = retrieved_memories['documents'][0]
        timestamps = [retrieved_memories['metadatas'][0][i]['created_at'] for i in range(len(memories))]
        memory_tuples = [(timestamps[i], memories[i]) for i in range(len(memories))]
        memory_tuples.sort()
        memory_list = [{"role": "system", "content": f"{memory_tuples[i][1]}", "character": ""} for i in range(len(memory_tuples))]

        done = False
        
        while not done:
            try:
                message = self.model.inference_from_history(memory_list + list(self.chat_history), self.name, inference_type="character")
                done = True
            except Exception as error:
                #print(error)
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