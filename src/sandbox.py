from assistant import Assistant
from character import NonPlayerCharacter
from llm import LLM

import chromadb
import os

#model = LLM()
model = LLM(file="mistral_params.json")
client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"))
assistant = Assistant(model)
character = NonPlayerCharacter("assets/characters/Leanah_Rasteti.json", model, assistant, client)

queries = assistant.get_most_salient_questions(character)
print(queries)
print()
insights = assistant.get_high_level_insights(queries, character)
print(insights)