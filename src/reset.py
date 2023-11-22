import chromadb
import os
from chromadb.config import Settings

client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"), settings=Settings(allow_reset=True))

decision = input("Type 'I am sure' if you are sure you want to delete the database: \n")

if decision == "I am sure":
    client.reset()