import os
import chromadb

from character import NonPlayerCharacter, PlayerCharacter
from llm import LLM
from assistant import Assistant
from conversation import Conversation
from datetime import datetime
from helpers import *

TIME_SPEEDUP = 6
DATE_FORMAT = '%A %d %B %Y, %I:%M %p'
WORLD_START = datetime.strptime("Monday 1 January 1303, 8:00 AM", DATE_FORMAT)


def list_characters(characters):
        name_sequence = ", ".join([character.name for character in characters[:-1]])
        name_sequence = name_sequence + " and " + characters[-1].name
        return name_sequence

def make_plans_for_characters(characters):
    for character in characters:
        if type(character) == NonPlayerCharacter:
            plan = assistant.get_plan_for_character(character, current_world_time)
            character.set_plan(plan)

if __name__ == "__main__":
    #model = LLM()
    model = LLM(file="mistral_params.json")
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
                
                except Exception as error:
                    print("Invalid character name")
                    print(error)
        
        else:
            print("Invalid selection")

    
    # characters = [PlayerCharacter("assets/players/Lorde_Moofilton.json"), 
    #               NonPlayerCharacter("assets/characters/Bazza_Summerwood.json", model, assistant, client), 
    #               NonPlayerCharacter("assets/characters/Leanah_Rasteti.json", model, assistant, client)
    #              ]

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

    # Get or set world creation time
    start_time_path = "assets/start_time.txt" #TODO: This path should be an environment variable or something

    if os.path.isfile(start_time_path):
        f = open(start_time_path, "r")
        raw_text = f.read()
        f.close()
        start_time = datetime.strptime(raw_text, DATE_FORMAT)
    
    else:
        start_time = datetime.now()
        f = open(start_time_path, 'w+')
        f.write(datetime.strftime(start_time, DATE_FORMAT))
        f.close()

    last_plan_made = None

    while True:
        # Update time
        current_time = datetime.now()
        diff = current_time-start_time
        current_world_time = WORLD_START + diff*TIME_SPEEDUP
        current_world_time = datetime.strftime(current_world_time, DATE_FORMAT)

        if not last_plan_made:
            make_plans_for_characters(characters)
            last_plan_made = current_world_time
        
        else:
            time_since_last_plan = datetime.strptime(current_world_time, DATE_FORMAT) - datetime.strptime(last_plan_made, DATE_FORMAT)
            if time_since_last_plan.days > 0:
                make_plans_for_characters(characters)
                last_plan_made = current_world_time

        speaker = conversation.get_speaker()
        
        if conversation.is_player_next():
            name = conversation.get_speaker_name()
            print(f"{name}: ", end="")
            conversation.generate_next_message(datetime.strptime(current_world_time, DATE_FORMAT))
            
        else:
            name, response = conversation.generate_next_message(datetime.strptime(current_world_time, DATE_FORMAT))
            print(f"{name}: {response}")
        
        print()
        conv_buffer = conversation.get_conversation_buffer()
        observation = assistant.get_observation_for_character(conv_buffer, speaker)
        importance = assistant.get_importance(observation)
        conversation.store_observation(observation, importance, speaker)
        assistant.try_to_reflect_for_character(speaker)
