import chromadb
import os
import json

from datetime import datetime
from llm import LLM 
from character import PlayerCharacter, NonPlayerCharacter
from conversation import Conversation
from assistant import Assistant
from helpers import *
from collections import deque, defaultdict
from world import World

import streamlit as st
import random
import time

st.set_page_config(layout="wide")

# Helper functions
def load_characters(characters_by_location, world, character_names_file, json_path, player_flag, using_streamlit=False, model=None, assistant=None, client=None):
    f = open(character_names_file)
    names = f.read().strip().split("\n")
    f.close()
    for n in names:
        if n != "":
            formatted_name = "_".join(n.split(" ")) + ".json"
            
            if player_flag:
                new_character = PlayerCharacter(os.path.join(os.getcwd(), json_path, formatted_name), world, using_streamlit)
            
            else:
                new_character = NonPlayerCharacter(os.path.join(os.getcwd(), json_path, formatted_name), model, assistant, client, world)
            
            characters_by_location[world.expand_loc_string(new_character.location)].append(new_character)

# Constants
WORLD_PATH = "assets/experimental_world_map.json"
PLAYER_PATH = "assets/players"
CHARACTER_PATH = "assets/characters"
EXPERIMENTAL_PLAYER_PATH = "assets/experimental_players"
EXPERIMENTAL_CHARACTER_PATH = "assets/experimental_characters"
TIME_SPEEDUP = 6
DATE_FORMAT = '%A %d %B %Y, %I:%M %p'
WORLD_START = datetime.strptime("Monday 1 January 1303, 8:00 AM", DATE_FORMAT)
START_TIME_PATH = "assets/start_time.txt"

# Variables
if "setup_complete" not in st.session_state:
    print("Creating important variables")
    st.session_state.model = LLM(file="mistral_params.json")
    st.session_state.assistant_model = st.session_state.model
    st.session_state.client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"))
    st.session_state.assistant = Assistant(st.session_state.assistant_model)
    st.session_state.world = World(WORLD_PATH)
    st.session_state.characters_by_location = defaultdict(list)
    st.session_state.conversations_by_location = {}

    # Load players and characters
    # TODO: Allow adjusting speaking order
    print("Loading characters")
    load_characters(st.session_state.characters_by_location, st.session_state.world, "assets/players.txt", PLAYER_PATH, player_flag=True, using_streamlit=True)
    load_characters(st.session_state.characters_by_location, st.session_state.world, "assets/experimental_players.txt", EXPERIMENTAL_PLAYER_PATH, player_flag=True, using_streamlit=True)
    load_characters(st.session_state.characters_by_location, st.session_state.world, "assets/characters.txt", CHARACTER_PATH, player_flag=False, model=st.session_state.model, assistant=st.session_state.assistant, client=st.session_state.client)
    load_characters(st.session_state.characters_by_location, st.session_state.world, "assets/experimental_characters.txt", EXPERIMENTAL_CHARACTER_PATH, player_flag=False, model=st.session_state.model, assistant=st.session_state.assistant, client=st.session_state.client)

    print("Setting up conversations")
    for location, character_list in st.session_state.characters_by_location.items():
        # Create a conversation for each location
        default_setup = []

        for c in character_list:
            verbose_location_string, _, _, _ = st.session_state.world.get_location_context_for_character(c)
            default_setup.append(verbose_location_string)
        
        default_setup = ". ".join(default_setup)
        setup = default_setup

        st.session_state.conversations_by_location[location] = Conversation(character_list, setup, location)
        st.session_state.conversations_by_location[location].store_observation(observation=setup, importance=1)

        # Let every character see the others 
        appearance_dict = {}

        for character in character_list:
            appearance = character.appearance
            importance = st.session_state.assistant.get_importance(appearance)
            appearance_dict[character] = (appearance, importance)
        
        st.session_state.conversations_by_location[location].store_appearances(appearance_dict)

    # Get or set world creation time
    print("Setting world time")
    if os.path.isfile(START_TIME_PATH):
        f = open(START_TIME_PATH, "r")
        raw_text = f.read()
        f.close()
        st.session_state.start_time = datetime.strptime(raw_text, DATE_FORMAT)

    else:
        st.session_state.start_time = datetime.now()
        f = open(START_TIME_PATH, 'w+')
        f.write(datetime.strftime(st.session_state.start_time, DATE_FORMAT))
        f.close()

    st.session_state.last_plan_made = None
    st.session_state.setup_complete = True

# Update time
print("Updating world time")
st.session_state.current_time = datetime.now()
diff = st.session_state.current_time - st.session_state.start_time
st.session_state.current_world_time = WORLD_START + diff*TIME_SPEEDUP
st.session_state.current_world_time = datetime.strftime(st.session_state.current_world_time, DATE_FORMAT)

# Update plans
print("Updating plans")
if not st.session_state.last_plan_made:
    for location, characters in st.session_state.characters_by_location.items():
        st.session_state.assistant.make_plans_for_characters(characters, st.session_state.current_world_time)
        st.session_state.last_plan_made = st.session_state.current_world_time

else:
    time_since_last_plan = datetime.strptime(st.session_state.current_world_time, DATE_FORMAT) - datetime.strptime(st.session_state.last_plan_made, DATE_FORMAT)
    if time_since_last_plan.days > 0:
        for location, characters in st.session_state.characters_by_location.items():
            st.session_state.assistant.make_plans_for_characters(characters, st.session_state.current_world_time)
            st.session_state.last_plan_made = st.session_state.current_world_time

if "messages" not in st.session_state:
        st.session_state.messages = defaultdict(list)

#st.title("Simple chat")
st.write(f"{st.session_state.current_world_time}")
cols = st.columns(len(st.session_state.conversations_by_location), gap="large")

col_to_location = {}
location_to_col = {}

for i, loc in enumerate(st.session_state.conversations_by_location):
    col_to_location[cols[i]] = loc
    location_to_col[loc] = cols[i]

def display_messages(column, speaker_name, response, player_flag):
    for message in st.session_state.messages[col_to_location[column]]:
        with st.chat_message(message["character"]):
            st.markdown(message["content"])

    with st.chat_message(speaker_name):
        message_placeholder = st.empty()
        full_response = ""
        
        # Simulate stream of response with milliseconds delay
        for chunk in response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)

    if player_flag:
        role = "user"
    else:
        role = "assistant"
    
    # Add response to chat history
    st.session_state.messages[location].append({"role": role, "content": full_response, "character": speaker_name})

# Display contexts
for col in cols:
    with col:
        location = col_to_location[col]
        st.write(location)
        st.write(f'Conversation contains {list_characters(st.session_state.characters_by_location[location])}')

print("Updating conversations")
for location, conversation in st.session_state.conversations_by_location.items():
    speaker = conversation.get_speaker()
    print(f"{speaker.name} is speaking")
            
    if conversation.is_player_next():
        # st.write(f"It is {speaker.name}'s turn to speak")
        # st.write(f"{speaker.name} is in {speaker.location}")
        name = conversation.get_speaker_name()
        response = st.chat_input("Type your message here")

        if response:
            speaker.set_last_response(response)
            conversation.generate_next_message(datetime.strptime(st.session_state.current_world_time, DATE_FORMAT))
            if response:
                #st.session_state.messages[location].append({"role": "user", "content": response, "character": speaker.name})
                display_messages(location_to_col[location], name, response, player_flag=True)
            
            while not conversation.is_player_next():
                name, response = conversation.generate_next_message(datetime.strptime(st.session_state.current_world_time, DATE_FORMAT))
                with location_to_col[location]:
                    display_messages(location_to_col[location], name, response, player_flag=False)
        
    else:
        name, response = conversation.generate_next_message(datetime.strptime(st.session_state.current_world_time, DATE_FORMAT))
        with location_to_col[location]:
            display_messages(location_to_col[location], name, response, player_flag=False)
            #st.session_state.messages[location].append({"role": "assistant", "content": response, "character": speaker.name})

    conv_buffer = conversation.get_conversation_buffer()
    observation = st.session_state.assistant.get_observation_for_character(conv_buffer, speaker)
    importance = st.session_state.assistant.get_importance(observation)
    conversation.store_observation(observation, importance, speaker)
    st.session_state.assistant.try_to_reflect_for_character(speaker)

    #location = st.session_state.assistant.get_location(speaker, st.session_state.world, conv_buffer)
    # if location and location != speaker.location:
    #     speaker.location = location
    #     character_locations[speaker.name] = location


