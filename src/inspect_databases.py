import chromadb
import os

client = chromadb.PersistentClient(path=os.path.join(os.getcwd(),"memory"))

done = False

while not done:
    character_name = input("Input name of character\n")

    if character_name == "":
        done = True
    
    else:
        try:
            collection_name = "_".join([word.lower() for word in character_name.split()]).replace('\'', '')
            collection = client.get_collection(name=collection_name)
            results = collection.get()

            memory_filter = input("Type 'fact', 'observation' or 'reflection' to filter by memory type\n")

            if memory_filter not in ["fact", "observation", "reflection"]:
                for i in range(collection.count()):
                    print(results['documents'][i], results['metadatas'][i]['type'], results['metadatas'][i]['importance'])
            
            else:
                for i in range(collection.count()):
                    if results['metadatas'][i]['type'] == memory_filter:
                        print(results['documents'][i])

        
        except Exception as error:
            print(error)