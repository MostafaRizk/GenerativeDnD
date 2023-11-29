import chromadb
import os
import json

from datetime import datetime
from llm import LLM 
from character import PlayerCharacter, NonPlayerCharacter
from assistant import Assistant
from helpers import *
from collections import deque, defaultdict

import streamlit as st
import random
import time

print("Setup")
st.set_page_config(layout="wide")
st.title("Simple chat")
st.write("08:00 AM")
col1, col2, col3, col4 = st.columns(4, gap="large")
key_to_column = {'col1': col1,
              'col2': col2,
              'col3': col3,
              'col4': col4}
if "messages" not in st.session_state:
    st.session_state.messages = defaultdict(list)
    print("Creating message dict")

if "col_to_character" not in st.session_state:
    st.session_state.col_to_character = {'col1' : ["Leanah", "Xorde"],
                        'col2': ["Myrna", "Jar'ra"],
                        'col3': ["Bazza"],
                        'col4': ["Ghelram"]}

if "col_to_place" not in st.session_state:
    st.session_state.col_to_place = {'col1': "Lobby",
                    'col2': "Tavern",
                    'col3': "Bazza's office",
                    'col4': "Bhelram's store"}

def message_loop(column):
    st.write(st.session_state.col_to_place[column])

    print(f"Printing history ")
    for message in st.session_state.messages[st.session_state.col_to_place[column]]:
        with st.chat_message(message["character"]):
            st.markdown(message["content"])

    for character in st.session_state.col_to_character[column]:
        if character != "Xorde":
            print(f"Printing new messages")
            with st.chat_message(character):
                message_placeholder = st.empty()
                full_response = ""
                assistant_response = random.choice(
                    [
                        "Hello there! How can I assist you today?",
                        "Hi, human! Is there anything I can help you with?",
                        "Do you need help?",
                    ]
                )
                # Simulate stream of response with milliseconds delay
                for chunk in assistant_response.split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    # Add a blinking cursor to simulate typing
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
            # Add assistant response to chat history
            st.session_state.messages[st.session_state.col_to_place[column]].append({"role": "assistant", "content": full_response, "character": character})

def get_assistant_messages():
    with col1:
        message_loop('col1')
        
    with col2:
        message_loop('col2')

    with col3:
        message_loop('col3')

    with col4:
        message_loop('col4')

def move_person(column, person, new_location):
    print(st.session_state.col_to_character[column])
    st.session_state.col_to_character[column].remove(person)
    print(st.session_state.col_to_character[column])

    for col, place in st.session_state.col_to_place.items():
        if place == new_location:
            print(st.session_state.col_to_character[col])
            st.session_state.col_to_character[col].append(person)
            print(st.session_state.col_to_character[col])

def dont_move_person():
    pass

def change_location_prompt(column_changing, person_moving, new_location):
    with key_to_column[column_changing]:
        print("Creating buttons")
        st.write(f"{person_moving} wants to go to {new_location}. Allow this?")
        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.button("Yes", on_click=move_person, kwargs=dict(column=column_changing, person=person_moving, new_location=new_location))
        with c2:
            st.button("No", on_click=dont_move_person)



print("Asked for input")
prompt = st.chat_input("Type your message here")
if prompt:
    # Display user message in chat message container
    # with st.chat_message("Xorde Moofilton"):
    #     st.markdown(prompt)
    # Add user message to chat history
    for column, char_list in st.session_state.col_to_character.items():
        if "Xorde" in char_list:
            loc = st.session_state.col_to_place[column]
    st.session_state.messages[loc].append({"role": "user", "content": prompt, "character": "Xorde"})
    print("Saved user message")

    get_assistant_messages()

    someone_is_moving = random.choice([True, False])
    if someone_is_moving:
        all_characters = []
        for names in st.session_state.col_to_character.values():
            for n in names:
                all_characters.append(n)
        person_moving = random.choice(all_characters)
        location_options = list(st.session_state.col_to_place.values())
        column_changing = None
        
        for column, char_list in st.session_state.col_to_character.items():
            if person_moving in char_list:
                location_options.remove(st.session_state.col_to_place[column])
                column_changing = column
        
        print(person_moving)
        new_location = random.choice(location_options)
        change_location_prompt(column_changing, person_moving, new_location)
        
        