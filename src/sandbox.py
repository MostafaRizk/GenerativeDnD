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
if "messages" not in st.session_state:
        st.session_state.messages = defaultdict(list)
        print("Creating message dict")

col_to_character = {col1 : "Leanah",
                    col2: "Myrna",
                    col3: "Bazza",
                    col4: "Bhelram"}

col_to_place = {col1: "Lobby",
                col2: "Tavern",
                col3: "Bazza's office",
                col4: "Bhelram's store"}

def message_loop(column):
    st.write(col_to_place[column])

    print(f"Printing history ")
    for message in st.session_state.messages[col_to_character[column]]:
        with st.chat_message(message["character"]):
            st.markdown(message["content"])

    print(f"Printing new messages")
    with st.chat_message(col_to_character[column]):
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
    st.session_state.messages[col_to_character[column]].append({"role": "assistant", "content": full_response, "character": col_to_character[column]})

def get_assistant_messages():
    with col1:
        message_loop(col1)
        
    with col2:
        message_loop(col2)

    with col3:
        message_loop(col3)

    with col4:
        message_loop(col4)

print("Asked for input")
prompt = st.chat_input("Type your message here")
if prompt:
    # Display user message in chat message container
    # with st.chat_message("Xorde Moofilton"):
    #     st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages[col_to_character[col1]].append({"role": "user", "content": prompt, "character": "Xorde Moofilton"})
    print("Saved user message")

    get_assistant_messages()



