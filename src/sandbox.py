import chromadb
import os

from datetime import datetime
from llm import LLM 
from character import PlayerCharacter, NonPlayerCharacter
from assistant import Assistant

def run_time_loop():
    TIME_SPEEDUP = 6

    start_time = datetime.now()
    world_start = "1 January, 1303 8:00 AM"
    date_format = '%A %B %d %Y, %I:%M %p'
    world_start = datetime.strptime(world_start, date_format)

    while True:
        dummy = input("Press Enter to continue")
        print()
        current_time = datetime.now()
        diff = current_time-start_time

        current_world_time = world_start + diff*TIME_SPEEDUP
        print(f"It is {current_world_time.strftime('%A %B %d %Y, %I:%M %p')}")

model = LLM()
assistant_model = model
assistant = Assistant(assistant_model)
client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"))

def get_character_list():
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
    
    return characters

character_list = get_character_list()
print()

entity_name = "Lorde Moofilton"
entity_observation = "Lorde Moofilton is bench-pressing a horse"

for character in character_list:
    if type(character) == NonPlayerCharacter:
        print(f"{character.name}'s opinion:")
        print(character.get_context_for_observed_entity(entity_name, entity_observation))
        print()