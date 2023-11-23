import os
import chromadb

from character import NonPlayerCharacter, PlayerCharacter
from llm import LLM
from assistant import Assistant
from conversation import Conversation

if __name__ == "__main__":
    model = LLM()
    #model = LLM(file="mistral_params.json")
    assistant_model = model
    client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"))
    
    assistant = Assistant(assistant_model)#Assistant.remote(assistant_model)

    characters = []
    print("Select what characters you want in this conversation")
    print()
    done = False
    counter = 1

    while not done:
        print(f"Character {counter}")
        player_or_npc= input("Enter 'p' if this character is a player. Enter 'n' if they are an NPC. Use 'ep' and 'en' for experimental players and NPCs. Press Enter to quit\n")

        if player_or_npc == "":
            done = True
        
        elif player_or_npc == "p" or player_or_npc == "n" or player_or_npc == "ep" or player_or_npc == "en":
            if player_or_npc == "p":
                pc_name = input("Enter player character name\n")
                
                try:
                    player = "_".join(pc_name.split(" "))
                    characters.append(PlayerCharacter(f"assets/players/{player}.json"))
                    counter += 1
                
                except:
                    print("Invalid player name")
            
            elif player_or_npc == "n":
                npc_name = input("Enter NPC name\n")
                
                try:
                    npc = "_".join(npc_name.split(" "))
                    characters.append(NonPlayerCharacter(f"assets/characters/{npc}.json", model, assistant, client))
                    counter += 1
                
                except:
                    print("Invalid character name")
            
            elif player_or_npc == "ep":
                pc_name = input("Enter player character name\n")
                
                try:
                    player = "_".join(pc_name.split(" "))
                    characters.append(PlayerCharacter(f"assets/experimental_players/{player}.json"))
                    counter += 1
                
                except:
                    print("Invalid player name")
            
            elif player_or_npc == "en":
                npc_name = input("Enter NPC name\n")
                
                try:
                    npc = "_".join(npc_name.split(" "))
                    characters.append(NonPlayerCharacter(f"assets/experimental_characters/{npc}.json", model, assistant, client))
                    counter += 1
                
                except:
                    print("Invalid character name")
        
        else:
            print("Invalid selection")

    
    # characters = [PlayerCharacter("assets/players/Lorde_Moofilton.json"), 
    #               NonPlayerCharacter("assets/characters/Bazza_Summerwood.json", model, assistant, client), 
    #               NonPlayerCharacter("assets/characters/Leanah_Rasteti.json", model, assistant, client)
    #              ]

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

    # Let every character see the others
    appearance_dict = {}
    for character in characters:
        appearance = character.appearance
        importance = assistant.get_importance(appearance)
        appearance_dict[character] = (appearance, importance)
    
    conversation.store_appearances(appearance_dict)

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
