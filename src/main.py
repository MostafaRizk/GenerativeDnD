import os
import chromadb

from character import NonPlayerCharacter, PlayerCharacter
from llm import LLM
from assistant import Assistant
from conversation import Conversation

if __name__ == "__main__":
    model = LLM(file="mistral_params.json")
    assistant_model = model#LLM(file="mistral_params.json")
    client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"))
    
    assistant = Assistant(assistant_model)#Assistant.remote(assistant_model)
    characters = [PlayerCharacter("assets/players/Lorde_Moofilton.json"), 
                  NonPlayerCharacter("assets/characters/Bazza_Summerwood.json", model, assistant, client), 
                  NonPlayerCharacter("assets/characters/Leanah_Rasteti.json", model, assistant, client)
                 ]

    def list_characters(characters):
        name_sequence = ", ".join([character.name for character in characters[:-1]])
        name_sequence = name_sequence + " and " + characters[-1].name
        return name_sequence

    default_setup = f"It is a quiet day and the Red Olive lobby is completely silent. Nobody is around save for {list_characters(characters)}"

    setup = input("Set the scene for your interaction. Press enter to use the default: ")
    if setup == "":
        setup = default_setup
    
    print()
    print(setup)
    print()
    print("--------")
    for character in characters:
        if type(character) == NonPlayerCharacter:
            #assistant.reflect_for_character(character)
            print(character.description)
            print()
    print("--------")
    
    conversation = Conversation(characters, setup)
    conversation.store_observation(observation=setup, importance=1)

    while True:
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
        assistant.try_to_reflect_for_character(speaker)
