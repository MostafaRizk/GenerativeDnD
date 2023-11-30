#import requests
import os
import chromadb

#from ray import serve
from character import NonPlayerCharacter, PlayerCharacter, Character
from llm import LLM
from assistant import Assistant
from datetime import datetime
from collections import deque, defaultdict

class Conversation():
    def __init__(self, characters, setup, location):
        assert type(characters) == list, "Must pass a list of characters"
        assert len(characters) > 0, "Character list is empty"
        
        for i in range(len(characters)):
            for j in range(i+1, len(characters)):
                assert characters[i] != characters[j], "List contains duplicate characters"
        
        self.characters = characters
        self.current_speaker_index = 0
        self.buffer_size = 1
        self.conversation_buffer = deque(maxlen=len(characters)*self.buffer_size)
        self.observations = defaultdict(str)

        for character in self.characters:
            character.listen(setup, "", "system")
        
        self.location = location
        self.appearance_dict = {}
    
    def add_character(self, character):
        #assert type(character) == Character, "The character must be of type Character"
        assert character not in self.characters, "The character must not already be in the conversation"

        self.characters.append(character)
        self.observations[character.name] = ""
        
        # Grow conversation buffer
        new_buffer = deque(maxlen=len(self.characters)*self.buffer_size)
        while len(self.conversation_buffer) > 0:
            new_buffer.append(self.conversation_buffer.popleft())
        self.conversation_buffer = new_buffer

        self.store_single_appearance(character, character.appearance, character.apperance_importance)
        self.newbie_observes_appearances(character)

        specific_location = self.location.split(":")[-1]
        character_setup = f"*{character.name} enters {specific_location}*"

        if type(character) == PlayerCharacter:
            role = "user"
        else:
            role = "assistant"
        
        # The new character hears the last thing everybody said
        # for message in self.conversation_buffer:
        #     character.listen(message['content'], message['character'], message['role'])
        
        # All characters become aware of the new character walking in, including the new character
        for existing_character in self.characters:
            existing_character.listen(character_setup, character.name, role)
        
        self.conversation_buffer.append({"role": f"{role}", "content": f"{character_setup}", "character": f"{character.name}"})
    
    def remove_character(self, character):
        assert character in self.characters, "The character is not in the conversation"
        
        index_to_remove = self.characters.index(character)
        self.characters.remove(character)

        if len(self.characters) == 0:
            return

        del self.observations[character.name]

        if self.current_speaker_index == index_to_remove:
            self.current_speaker_index %= len(self.characters)
        
        elif self.current_speaker_index > index_to_remove:
            self.current_speaker_index -= 1
        
        # Shrink conversation buffer
        new_buffer = deque(maxlen=len(self.characters)*self.buffer_size)
        while len(self.conversation_buffer) > 0:
            new_buffer.append(self.conversation_buffer.popleft())
        self.conversation_buffer = new_buffer

        del self.appearance_dict[character]

        specific_location = self.location.split(":")[-1]
        character_departure = f"*{character.name} leaves {specific_location}*"

        if type(character) == PlayerCharacter:
            role = "user"
        else:
            role = "assistant"
        
        # All characters become aware of the new character leaving
        for existing_character in self.characters:
            existing_character.listen(character_departure, character.name, role)
        
        self.conversation_buffer.append({"role": f"{role}", "content": f"{character_departure}", "character": f"{character.name}"})
    
    def generate_next_message(self, date_and_time):
        character = self.characters[self.current_speaker_index]
        
        all_characters = [c for c in self.characters]
        observations = [self.observations[c.name] for c in self.characters]

        response = character.speak(all_characters, observations, date_and_time)
        
        if type(character) == PlayerCharacter:
            role = "user"
        else:
            role = "assistant"

        self.conversation_buffer.append({"role": f"{role}", "content": f"{response}", "character": f"{character.name}"})

        for other_character in self.characters:
            if other_character != character:
                other_character.listen(response, character.name, "assistant")

        self.current_speaker_index += 1
        self.current_speaker_index %= len(self.characters)
        
        return character.name, response
    
    def store_observation(self, observation, importance, observed_character=None):
        for character in self.characters:
            if type(character) != PlayerCharacter:
                character.store_memory(observation, importance)
        
        if observed_character:
            self.observations[observed_character.name] = observation
    
    def store_single_appearance(self, character, appearance, importance):
        """Characters already in the conversation observe a given character's appearance

        Args:
            character (Character): Character to be observed
            appearance (str): String describing the appearance of the character to be observed
            importance (int): Importance score associated with the character's observed appearances
        """
        for other_character in self.characters:
            if other_character != character and type(other_character) == NonPlayerCharacter:
                other_character.listen(appearance, "", "system")
                other_character.store_memory(appearance, importance)
                self.appearance_dict[character] = (appearance, importance)


    def store_appearances(self, appearance_dict):
        """Allows each character to observe the appearances of the other characters when they enter into a conversation.
        This means including it in the chat history and storing it in their database.

        Args:
            appearance_dict (dictionary): A dictionary where the keys are character objects and the values are tuples of appearance and importance
        """
        for character in self.characters:
            appearance, importance = appearance_dict[character]
            # Debugging
            #print(appearance, importance)
            self.store_single_appearance(character, appearance, importance)
        
        #print()
    
    def newbie_observes_appearances(self, new_character):
        """A new character entering the conversation observes the appearances of everyone else already in the conversation

        Args:
            new_character (Character): The character entering the conversation
        """
        for character in self.characters:
            if character != new_character and type(character) != NonPlayerCharacter:
                appearance, importance = self.appearance_dict[character]
                new_character.listen(appearance, "", "system")
                new_character.store_memory(appearance, importance)
    
    def is_player_next(self):
        next_speaker = self.characters[self.current_speaker_index]
        if type(next_speaker) == PlayerCharacter:
            return True
        else:
            return False
    
    def get_speaker_name(self):
        next_speaker = self.characters[self.current_speaker_index]
        return next_speaker.name
    
    def get_speaker(self):
        next_speaker = self.characters[self.current_speaker_index]
        return next_speaker
    
    def get_conversation_buffer(self):
        return self.conversation_buffer

if __name__ == "__main__":
    model = LLM(file="mistral_params.json")
    assistant_model = model#LLM(file="mistral_params.json")
    client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"))
    
    assistant = Assistant(assistant_model)#Assistant.remote(assistant_model)
    characters = [PlayerCharacter("assets/players/Lorde_Moofilton.json"), 
                  #NonPlayerCharacter("assets/characters/Bazza_Summerwood.json", model, assistant), 
                  NonPlayerCharacter("assets/characters/Leanah_Rasteti.json", model, assistant, client)]

    def list_characters(characters):
        name_sequence = ",".join([character.name for character in characters[:-1]])
        name_sequence = name_sequence + " and " + characters[-1].name
        return name_sequence

    setup = f"It is a quiet day and the Red Olive lobby is completely silent. Nobody is around save for {list_characters(characters)}"
    print(setup)
    print()
    
    conversation = Conversation(characters, setup)
    conversation.store_observation(observation=setup, importance=1)

    for i in range(1000):
        speaker = conversation.get_speaker()
        
        if conversation.is_player_next():
            name = conversation.get_speaker_name()
            print(f"{name}: ", end="")
            conversation.generate_next_message()
            
        else:
            name, response = conversation.generate_next_message()
            print(f"{name}: {response}")
        
        print()
        conv_buffer = conversation.get_conversation_buffer()
        observation = assistant.get_observation_for_character(conv_buffer, speaker)
        importance = assistant.get_importance(observation)
        conversation.store_observation(observation, importance)

        # print("------")
        # print(observation)
        # print(importance)
        # print("------")