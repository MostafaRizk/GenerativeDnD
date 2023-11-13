class Assistant():
    def __init__(self, model, system_message):
        self.model = model
        self.system_message = system_message
        self.name = "assistant"
    
    def get_character_summary_from_bio(self, name, bio):
        prompt = f"Write a summary of {name} based on the following information: \n\n {bio}"
        history = [
                    {"role": "system", "content": f"{self.system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name)
    
    def get_plan_for_character(self, character):
        prompt = f""""
        {character} is a character in a Dungeons and Dragons-style fantasy world.

        {character.description}

        Today is Monday January 1. Write a broad strokes plan for {character.name}'s upcoming day. Keep each item in the itinerary succinct. Format it as follows:

        Time 1- Do x
        Time 2- Do y
        Time 3- Do z
        etc.
        """
        history = [
                    {"role": "system", "content": f"{self.system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name)

if __name__ == "__main__":
    from llm import LLM
    from character import Character
    
    model = LLM()
    character = Character("src/assets/Bazza_Summerwood.json", model)
    assistant = Assistant(model, "You are a helpful AI assistant. Your job is to write itineraries for people's days")
    plan = assistant.get_plan_for_character(character)
    print(plan)
