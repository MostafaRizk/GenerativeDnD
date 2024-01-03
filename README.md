# GenerativeDnD
This is a text-based adventure game built around the concept of 'Generative Agents'. It is a work in progress.

Important modules:

- **llm.py**- This contains code for loading an LLM using the HuggingFace Transformers library. It is designed to allow the use of different models and contains pipelines for all the different LLM tasks that the game needs done

- **character.py**- This primarily allows you to create NPCs given an LLM, database client, and some starter config files. This contains the logic for retrieving pertinent memories according to the Generative Agents method and inserting them into the LLM context as well as logic for conditioning speech according to the character's location and circumstances

- **assistant.py**- Uses the LLM to create an assistant (the pipelines for assistant tasks are different to chat tasks because they require different parameters e.g. lower temperature). This has the logic for summarising recent events, scoring the importance of observed events, reflecting on recent memories and planning a character's day.

- **conversation.py**- Creates a conversation containing multiple player and non-player characters. It manages who is in the conversation, the speaking order, and what gets sent to the characters' memory databases

- **world.py**- Functions for parsing the world tree (i.e. the tree that describes all the locations in the game world)

- **main.py**- Brings it all together

To run:

1. Download repo on a linux system or WSL
2. Open the directory in a terminal window and run ```pipenv install``` to install dependencies
3. Run ```pipenv shell``` to activate the environment
4. Make sure that 'assets/characters.txt' contains the names of all the characters you want in the game and 'assets/players.txt' contains all the players you want. Make sure the player and characters have corresponding bio files in the assets folder. Also make sure that WORLD_PATH is set to 'world_map.json' rather than 'experimental_world_map.json'
5. cd into the src directory and type ```streamlit run main.py``` to run the app
6. The app will run at http://localhost:8501
7. Once the application loads, you'll get an error that says 'IndexError: deque index out of range'. Ignore this
