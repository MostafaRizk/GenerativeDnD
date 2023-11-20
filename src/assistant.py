import helpers
import ray
from datetime import datetime
from collections import deque

#@ray.remote
class Assistant():
    time_format = "%I:%M%p"

    def __init__(self, model):
        self.model = model
        self.planning_system_message = "You are a helpful AI assistant. Your job is to write itineraries for people's days"
        self.summary_system_message = "You are a helpful AI assistant. Your job is to summarise text."
        self.name = "assistant"
    
    def get_character_summary_from_bio(self, name, bio):
        prompt = f"Write a summary of {name} based on the following information: \n\n {bio}"
        history = [
                    {"role": "system", "content": f"{self.summary_system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name, inference_type="summary")
    
    def get_observation_for_character(self, messages, character):
        prompt = f"""Describe in one sentence what {character.name} did and said in the previous text. Only describe what others can perceive, not {character.name}'s internal state and do not fabricate any information. 
        Make the sentence as descriptive as possible. Start the sentence with '{character.name} is ' and end with a full stop. Some example sentences include:
        
        Frederik Olaffson is voraciously eating a warm pie while vocalising how much he is enjoying the taste.
        Jemima Hendricks is practicing combat techniques on the wooden dummies next to the wall as he tells his friends why he is angry.
        Edward Spangler is examining a book about necromancy and explaining to his friends what necromancy is."""

        history = deque(list(messages))

        history.appendleft({"role": "system", "content": f"{self.summary_system_message}"})
        history.append({"role": "user", "content": f"{prompt}", "character": f"user"})
        return self.model.inference_from_history(history, self.name, inference_type="summary")
    
    def get_importance(self, observation):
        prompt = f"""On a scale of 1 to 10, where 1 is purely mundane and routine and 10 is extremely significant and rare, rate the likely significance of the following event:
        
        {observation}

        """
        history = [
                    {"role": "system", "content": f"{self.summary_system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name, inference_type="summary")
    
    def get_plan_for_character_helper(self, character, date):
        prompt = f""""
        {character.name} is a character in a Dungeons and Dragons-style fantasy world.

        {character.description}

        Today is {date}. Write a broad strokes plan for {character.name}'s upcoming day from when they wake up until they sleep. 
        Write an itinerary with 5-10 tasks and their start times. Keep each item in the itinerary succinct. Format it as follows:

        1) Wake up at X:XXam
        2) Do Task 2 at X:XXam
        3) Do Task 3 at X:XXpm
        4) Do Task 4 at X:XXpm
        5) Do Task 5 at X:XXpm
        6) Go to bed at X:XXpm
        """
        history = [
                    {"role": "system", "content": f"{self.planning_system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name, inference_type="planner")
    
    def get_plan_for_character(self, character, date="Monday January 1"):
        done = False
        
        while not done:
            try:
                raw_plan = self.get_plan_for_character_helper(character, date)
                plan = helpers.get_plan_from_plan_string(raw_plan)
                done = True
            except TypeError:
                pass
        
        return plan
    
    def make_task_more_detailed_helper(self, character, task, start_time, end_time):
        prompt = f""""
        {character.name} is a character in a Dungeons and Dragons-style fantasy world.

        {character.description}

        {character.name} has the following task: {task} from {start_time} until {end_time}. 
        Write a more detailed plan for accomplishing this task. Keep each step of the plan succinct. Format it as follows:

        1) Do Step 1 at {start_time}
        2) Do Step 2 at X:XXam
        3) Do Step 3 at X:XXam
        4) Do Step 4 at X:XXpm
        5) Do Step 5 at X:XXpm
        """
        history = [
                    {"role": "system", "content": f"{self.planning_system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name, inference_type="planner")
    
    def make_task_more_detailed(self, character, task, start_time, end_time="unspecified time"):
        done = False
        
        while not done:
            try:
                raw_plan = self.make_task_more_detailed_helper(character, task, start_time, end_time)
                plan = helpers.get_plan_from_plan_string(raw_plan)

                start = datetime.strptime(start_time.upper(), self.time_format)

                if end_time != "unspecified time":
                    end = datetime.strptime(end_time.upper(), self.time_format)
                else:
                    end = None

                for _, sub_time in plan:
                    sub_time = datetime.strptime(sub_time.upper(), self.time_format)

                    if sub_time < start or (end and sub_time > end):
                        print("Time falls out of range")
                        raise TypeError("Sub task time falls outside the range of parent task")

                done = True
            except TypeError:
                print("TypeError")
                pass
        
        return plan



if __name__ == "__main__": 
    from llm import LLM
    from character import Character
    
    model = LLM(file="llm_params_planning.json")
    #character = Character("src/assets/Bazza_Summerwood.json", model)
    character = Character("src/assets/Leanah_Rasteti.json", model)
    assistant = Assistant(model, "You are a helpful AI assistant. Your job is to write itineraries for people's days")
    plan = assistant.get_plan_for_character(character)
    print(plan)
    
    # for i, item in enumerate(plan):
    #     print(item)
    #     if i + 1 < len(plan):
    #         end_time = plan[i+1][1]
    #     detailed_plan = assistant.make_task_more_detailed(character, item[0], item[1], end_time)
    #     print(detailed_plan)
    #     print()

    # for i in range(3):
    #     item_to_expand = plan[1]
    #     if len(plan) > 2:
    #         end_time = plan[2][1]
    #     plan = assistant.make_task_more_detailed(character, item_to_expand[0], item_to_expand[1], end_time)
    #     print(plan)

