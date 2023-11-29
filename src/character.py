import json
import os
import chromadb
import uuid
from llm import LLM
from collections import deque
from datetime import datetime
from helpers import *

class Character():
    def __init__(self, bio_file, world, using_streamlit=False):
        f = open(bio_file)
        self.bio = json.load(f)
        f.close()
        self.name = self.bio["name"]
        self.appearance = self.bio["initial_appearance"]
        self.location = self.bio["initial_location"]
        self.world = world
        self.using_streamlit=using_streamlit
    
    def speak(self):
        pass

    def listen(self):
        pass


class PlayerCharacter(Character):
    def __init__(self, bio_file, world, using_streamlit=False):
        Character.__init__(self, bio_file, world, using_streamlit)
        self.last_response = None
    
    def speak(self, other_characters=None, observations=None, character_observation=None, date_and_time=None):
        if self.using_streamlit:
            response = self.last_response
        else:
            response = input()
        
        return response

    def listen(self, content, other_character, other_role):
        pass

    def set_last_response(self, response):
        self.last_response = response

class NonPlayerCharacter(Character):
    roleplay_prompt = "Roleplay as a Dungeons and Dragons character, in a medieval fantasy world, with the following character description: "
    
    def __init__(self, bio_file, model, assistant, client, world, world_facts_file="assets/world_info.json"):
        Character.__init__(self, bio_file, world)
        self.model = model
        self.assistant = assistant
        f = open(world_facts_file)
        self.world_info = json.load(f)
        f.close()
        self.name = self.bio["name"]

        self.client = client
        self.collection_name = "_".join([word.lower() for word in self.name.split()]).replace('\'', '')
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

        # Constants for memory retrieval
        self.DECAY_RATE = 0.995 # Taken from paper
        self.TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
        self.IMPORTANCE_WEIGHT = 1
        self.RELEVANCE_WEIGHT = 1
        self.RECENCY_WEIGHT = 1

        # Constants and variables for reflection
        self.NUM_MEMORIES = 100
        self.importance_tally = 0

        self.description = self.generate_description()
        self.system_message = f"{self.roleplay_prompt}{self.description}"
        self.chat_history = deque([self.system_message])
        
        # Planning
        self.plan = deque()
        self.DEFAULT_TASK = f"{self.name} has nothing on their schedule right now"
        self.current_task = self.DEFAULT_TASK
        self.ITINERARY_TIME_FORMAT = "%I:%M%p"
        self.DATE_AND_TIME_FORMAT = '%A %d %B %Y, %I:%M %p'
    
    def add_system_message(self):
        self.chat_history.appendleft({"role": "system", "content": f"{self.system_message}"})

    def generate_description(self):
        """Get a description of the character based on the facts stored in their database

        Returns:
            string: A short text excerpt summarising who the character is as a person
        """
        #facts = "\n".join([self.bio["initial_appearance"]] + self.bio['initial_facts'])
        memories = self.retrieve_memories(self.name)
        memories.sort(key = lambda x: x[1]) # Sort by memory creation date
        facts = "\n".join([memories[i][2] for i in range(len(memories))])
        #print(facts)
        summary = self.assistant.get_character_summary_from_bio(self.name, facts)
        last_newline = summary.rfind('\n')
        last_full_stop = summary.rfind('.')
        cutoff_index = max(last_newline, last_full_stop)
        summary = summary[:cutoff_index]

        return summary
    
    def update_description(self):
        self.description = self.generate_description()
        self.system_message = f"{self.roleplay_prompt}{self.description}"
        self.chat_history.popleft()
        self.add_system_message()
    
    def initialise_memory(self):
        facts = [self.bio["initial_appearance"]] + self.bio['initial_facts'] + self.world_info["common_knowledge"]
        self.collection = self.client.create_collection(name=self.collection_name, metadata={"hnsw:space": "cosine"})
        current_datetime = str(datetime.now())
        self.collection.add(
            documents=facts,
            metadatas=[{"created_at": current_datetime, 
                        "accessed_at": current_datetime,
                        "type": "fact",
                        "importance": 10,
                        "citations": ""} for _ in range(len(facts))],
            ids=[str(uuid.uuid4()) for _ in range(len(facts))])
    
    def store_memory(self, memory, importance, memory_type="observation"):
        current_datetime = str(datetime.now())
        self.collection.add(
            documents=[memory],
            metadatas=[{"created_at": current_datetime, 
                        "accessed_at": current_datetime,
                        "type": memory_type,
                        "importance": importance,
                        "citations": ""}],
            ids=[str(uuid.uuid4())])
        
        if memory_type == "observation":
            self.importance_tally += importance
    
    def retrieve_memories(self, query):
        """Retrieve memories from database according to a calculated retrieval score

        Args:
            query (string): The query given to the vector database (usually the last utterance of another character)

        Returns:
            list: List of tuples (retrieval score, creation time, memory) sorted from highest retrieval score to lowest
        """
        all_memories = self.collection.query(query_texts=[query],
                                             n_results=self.collection.count())
        pairings = [None]*len(all_memories['documents'][0])
        
        for i in range(len(all_memories['documents'][0])):
            # Normalise relevance score
            try:
                relevance = 1 / all_memories['distances'][0][i]
            except ZeroDivisionError:
                relevance = 1
            # Normalise importance score
            importance = all_memories['metadatas'][0][i]['importance'] / 10
            # Normalise recency score
            current_time = datetime.now()
            access_time = all_memories['metadatas'][0][i]['accessed_at']
            access_time = datetime.strptime(access_time, self.TIME_FORMAT)
            time_diff = (current_time-access_time).seconds
            time_diff = seconds_to_hours(time_diff)
            recency = exponential_decay(self.DECAY_RATE, time_diff)

            # Calculate weighted sum and store in 'retrieval'
            retrieval_score = self.RELEVANCE_WEIGHT*relevance + self.IMPORTANCE_WEIGHT*importance + self.RECENCY_WEIGHT*recency
            pairings[i] = (retrieval_score, all_memories['metadatas'][0][i]['created_at'], all_memories['documents'][0][i], i, all_memories['ids'][0][i])
        
        # Sort by retrieval
        pairings.sort(reverse=True)
        
        # Get top n
        results = pairings[:self.history_allocation]

        for result in results:
            self.collection.upsert(documents=[all_memories['documents'][0][result[3]]],
            metadatas=[{"created_at": all_memories['metadatas'][0][result[3]]['created_at'], 
                        "accessed_at": str(current_time),
                        "type": all_memories['metadatas'][0][result[3]]['type'],
                        "importance": all_memories['metadatas'][0][result[3]]['importance'],
                        "citations": ""}],
            ids=[all_memories['ids'][0][result[3]]])
        
        return results
    
    def get_most_recent_memories(self, num_memories=None):
        """Retrieves the n most recent memories of this character

        Args:
            num_memories (int, optional): The number of memories to retrieve. Defaults to self.NUM_MEMORIES.

        Returns:
            deque: A deque containing all n memories
        """
        if num_memories == None:
            num_memories = self.NUM_MEMORIES
        
        all_memories = self.collection.get()
        pairings = [None]*len(all_memories['documents'])
        
        for i in range(len(all_memories['documents'])):
            created_at = all_memories['metadatas'][i]['created_at']
            created_at = datetime.strptime(created_at, self.TIME_FORMAT)
            pairings[i] = (created_at, all_memories['documents'][i])
        
        pairings.sort(reverse=True)
        pairings = pairings[:num_memories][::-1]
        memories = deque([{"role": "system", "content": f"{pairings[i][1]}"} for i in range(len(pairings))])

        return memories

    def get_context_for_observed_entity(self, observed_entity_name, observation):
        """Given an entity that the character observes and an observation about the entity's current state, generates relevant context from the character's memory
        For example, if the character sees their friend and observes that friend to be drinking tea, this function will retrieve all memories relating to the character's relationship with 
        that friend and the observation of them drinking tea. It will then summarise the combined memories.

        Args:
            observed_entity_name (string): The name of the entity being observed e.g. a character's name or an object
            observation (string): A description of the observation made by the character regarding this

        Returns:
            string: The summarised context
        """
        query1 = f"What is {self.name}'s relationship with {observed_entity_name}?"
        query2 = observation
        retrieved_memories = self.retrieve_memories(query1) + self.retrieve_memories(query2)
        retrieved_memories.sort(key = lambda x: x[1]) # Sort by memory creation date
        memory_list = [retrieved_memories[i][2] for i in range(len(retrieved_memories))]
        memory_string = "\n".join(memory_list)
        context = self.assistant.summarise_context(memory_string, self.name, observed_entity_name)
        
        return context

    def get_context_for_observed_entities(self, observed_entity_names, observations):
        retrieved_memories = []
        
        for i in range(len(observed_entity_names)):
            query1 = f"What is {self.name}'s relationship with {observed_entity_names[i]}?"
            query2 = observations[i]

            for mem in self.retrieve_memories(query1):
                retrieved_memories.append(mem)
            
            for mem in self.retrieve_memories(query2):
                retrieved_memories.append(mem)
        
        retrieved_memories.sort(key = lambda x: x[1]) # Sort by memory creation date
        memory_list = [retrieved_memories[i][2] for i in range(len(retrieved_memories))]
        memory_string = "\n".join(memory_list)
        context = self.assistant.summarise_context(memory_string, list_entities(observed_entity_names))
        
        return context
    
    def vanilla_speech(self):
        """Generate the character's next utterance using a bunch of retrieved memories taking up half the context combined with however much of the chat history fits  

        Returns:
            str: The utterance of the character
        """
        retrieved_memories = self.retrieve_memories(f"{self.chat_history[-1]['character']}: {self.chat_history[-1]['content']}")
        retrieved_memories.sort(key = lambda x: x[1]) # Sort by memory creation date
        memory_list = [{"role": "system", "content": f"{retrieved_memories[i][2]}", "character": ""} for i in range(len(retrieved_memories))]

        done = False
        
        while not done:
            try:
                message = self.model.inference_from_history(memory_list + list(self.chat_history), self.name, inference_type="character")
                done = True
            except RuntimeError:
                self.chat_history.popleft()
                self.chat_history.popleft()
                self.add_system_message()
        
        cutoff_index = message.find("\n")
        if cutoff_index != -1:
            message = message[:cutoff_index]

        self.chat_history.append({"role": "assistant", "content": f"{message}", "character": f"{self.name}"})
        return message
    
    def conditioned_speech(self, all_characters, observations, date_and_time):
        """Generate the character's next utterance by conditioning the prompt on the summary of the relevant context relating to what is currently happening.
        For example, if they are speaking to character A, they retrieve the relevant context about that character from their memories and put that in the context of the prompt   

        Returns:
            str: The utterance of the character
        """
        
        assert len(all_characters) == len(observations), "The number of characters and observations must be the same"
        #assert self not in other_characters, "Character can not be included in their own conditioned speech function call"

        retrieved_memories = self.retrieve_memories(f"{self.chat_history[-1]['character']}: {self.chat_history[-1]['content']}")
        retrieved_memories.sort(key = lambda x: x[1]) # Sort by memory creation date
        memory_list = [{"role": "system", "content": f"{retrieved_memories[i][2]}", "character": ""} for i in range(len(retrieved_memories))]

        context = []
        
        names = [c.name for c in all_characters]
        context.append(self.get_context_for_observed_entities(names, observations))
        
        if len(all_characters) <= 1:
            context.append(f"{self.name} sees absolutely nobody around. {self.name} is completely alone.")
        
        context = "\n\n".join(context)
        #observations = "\n\n".join(observations)
        self.update_current_task(date_and_time)
        verbose_location_string, _, _, _ = self.world.get_location_context_for_character(self)
        speech_prompt = f"Given {self.name}'s scheduled task and the current situation, what does {self.name} say/do next?"
        speech_prompt = [{"role": "system", "content": f"{speech_prompt}", "character": ""}]

        context_string = f"""It is {datetime.strftime(date_and_time, self.DATE_AND_TIME_FORMAT)}.\n\n{self.name}'s currently scheduled task is:\n\n{self.current_task}\n\n{verbose_location_string}\n\n{context}"""

        # print("-----------------------")
        # print(context_string)
        # print("-----------------------")

        memory_list.append({"role": "system", "content": f"{context_string}", "character": ""})

        done = False
        
        while not done:
            try:
                message = self.model.inference_from_history(memory_list + list(self.chat_history) + speech_prompt, self.name, inference_type="character")
                done = True
            except RuntimeError:
                self.chat_history.popleft()
                self.chat_history.popleft()
                self.add_system_message()
        
        cutoff_index = message.find("\n")
        if cutoff_index != -1:
            message = message[:cutoff_index]

        self.chat_history.append({"role": "assistant", "content": f"{message}", "character": f"{self.name}"})
        return message

    def speak(self, other_characters=None, observations=None, date_and_time=None):
        return self.conditioned_speech(other_characters, observations, date_and_time)
    
    def listen(self, content, other_character_name, other_role):
        message = {"role": f"{other_role}", "content": f"{content}", "character": f"{other_character_name}"}
        self.chat_history.append(message)
    
    def set_plan(self, plan):
        assert type(plan) == deque, "Plan must be a deque object"
        self.plan = plan
    
    def update_current_task(self, current_time):
        if len(self.plan) == 0:
            self.current_task = self.DEFAULT_TASK
        
        current_time = datetime.strftime(current_time, self.ITINERARY_TIME_FORMAT)
        current_time = datetime.strptime(current_time, self.ITINERARY_TIME_FORMAT)
        
        done = False

        while not done and len(self.plan) > 0:
            top_task, top_time = self.plan[0]
            top_time = datetime.strptime(top_time, self.ITINERARY_TIME_FORMAT)

            if top_time < current_time:
                self.plan.popleft()
                self.current_task = top_task
            else:
                done = True

if __name__ == "__main__":
    model = LLM()
    character = Character("src/assets/Bazza_Summerwood.json", model)
    history = character.generate_history()
    response = character.speak(history)
    print(response)