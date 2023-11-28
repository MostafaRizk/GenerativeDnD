from helpers import *
from datetime import datetime
from collections import deque
from character import NonPlayerCharacter
from scipy.spatial import distance
import numpy as np

class Assistant():
    time_format = "%I:%M%p"

    def __init__(self, model):
        self.model = model
        self.planning_system_message = "You are a helpful AI assistant. Your job is to write itineraries for people's days"
        self.summary_system_message = "You are a helpful AI assistant. Your job is to summarise text."
        self.name = "assistant"

        self.REFLECTION_THRESHOLD = 300

        # Location variables and constants
        self.stationary_sentence = " is staying in their current location"
        self.movement_sentence = " is going to a new location"
    
    def get_character_summary_from_bio(self, name, bio):
        prompt = f"{name} is a character in a Dungeons and Dragons style medieval fantasy world. Write a summary of who {name} is as a person, based ONLY on the below information. Focus on their personality, defining experiences, and how they interact with people. Keep it succinct and do not fabricate any information: \n\n {bio}"
        history = [
                    {"role": "system", "content": f"{self.summary_system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name, inference_type="summary")
    
    def respond_to_query(self, query, facts):
        prompt = f"{facts}\n\n{query}"
        
        history = [
                    {"role": "system", "content": f"{self.summary_system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        return self.model.inference_from_history(history, self.name, inference_type="summary")

    def summarise_context(self, facts, entities):
        prompt = f"{facts}\n\nSummarize the above information about {entities} succinctly and directly, without any filler."
        
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
        prompt = f"""On a scale of 1 to 10, where 1 is purely mundane and routine and 10 is extremely significant and rare, rate the likely significance of the below event from the perspective of the character or characters involved. Start the sentence with 'The importance is '. Some example sentences include:

        The importance is 2.
        The importance is 10.
        The importance is 4.

        Here is the event:
        
        {observation}

        """
        history = [
                    {"role": "system", "content": f"{self.summary_system_message}"},
                    {"role": "user", "content": f"{prompt}", "character": f"user"}
                ]
        response= self.model.inference_from_history(history, self.name, inference_type="summary")
        score = get_score_from_importance_string(response)
        return score
    
    def get_most_salient_questions(self, character):
        history = character.get_most_recent_memories()

        # Get 3 questions
        prompt = f"""Given only the information above, what are the 3 most salient, high-level questions we can answer about the subjects in the statements? Format your answer as follows:
        
        1. Question 1
        2. Question 2
        3. Question 3
        """

        history.append({"role": "user", "content": f"{prompt}", "character": f"user"})
        done = False
        
        while not done:
            try:
                result = self.model.inference_from_history(history, self.name, inference_type="summary")
                done = True
            except RuntimeError:
                history.popleft()
        
        # for h in history:
        #     print(h['content'])
        # print()
        
        return get_queries_from_question_string(result)
    
    def get_high_level_insights(self, queries, character):
        insights = []
        for query in queries:
            memory_pairings = character.retrieve_memories(query)
            history = deque([{"role": "system", "content": f"{i}. {memory_pairings[i][2]}"} for i in range(len(memory_pairings))])

            # for h in history:
            #     print(h['content'])
            # print()

            prompt = f"""What 5 high-level insights can {character.name} infer about themselves from the combined knowledge of the above statements? Express each insight succinctly in a single sentence. Format your response as follows:
            
            1. {character.name} is X
            2. {character.name} has Y
            etc.
            """
            
            history.append({"role": "user", "content": f"{prompt}", "character": f"user"})
            done = False
        
            while not done:
                try:
                    result = self.model.inference_from_history(history, self.name, inference_type="summary")
                    done = True
                except RuntimeError:
                    history.popleft()

            insights += get_insights_from_insight_string(result)
        
        return insights
    
    def reflect_for_character(self, character):
        print(f"----REFLECTING FOR {character.name}----")
        queries = self.get_most_salient_questions(character)
        insights = self.get_high_level_insights(queries, character)
        
        for insight in insights:
            character.store_memory(memory=insight, importance=9, memory_type="reflection")
        
        character.update_description()
        character.importance_tally = 0
    
    def try_to_reflect_for_character(self, character):
        if type(character) == NonPlayerCharacter and character.importance_tally >= self.REFLECTION_THRESHOLD:
            self.reflect_for_character(character)

    def get_plan_for_character_helper(self, character, date):
        prompt = f""""
        {character.name} is a character in a Dungeons and Dragons-style fantasy world.

        {character.description}

        It is {date}. Write a broad strokes plan for {character.name}'s upcoming day from when they wake up until they sleep. 
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
    
    def get_plan_for_character(self, character, date):
        done = False
        
        while not done:
            try:
                raw_plan = self.get_plan_for_character_helper(character, date)
                plan = get_plan_from_plan_string(raw_plan)
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
                plan = get_plan_from_plan_string(raw_plan)

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

    def get_desired_location(self, character, character_summary, world, recent_conversation_history):
        verbose_location_string, adjacent_locations_string, location_observation_string, known_locations_string = world.get_location_context_for_character(character)
        world_context = f"{verbose_location_string}\n{adjacent_locations_string}\n{location_observation_string}\n{known_locations_string}\n"

        prompt = f"""{character_summary}\n\n{world_context}\n\nBased on the above conversation, is {character.name} going somewhere or staying where they are? Start your answer with '{character.name} is...'"""
        
        history = deque(list(recent_conversation_history))

        history.appendleft({"role": "system", "content": f"{self.summary_system_message}"})
        history.append({"role": "user", "content": f"{prompt}", "character": f"user"})

        return self.model.inference_from_history(history, self.name, inference_type="summary")
    
    def get_location(self, character, world, conversation_buffer):
        last_utterance = conversation_buffer[-1]["content"]
        last_action = extract_actions_from_utterance(last_utterance)
        full_text = "\n".join([extract_actions_from_utterance(c['content']) for c in conversation_buffer])
        #print(full_text)

        known_locations = world.get_list_of_known_locations(character)
        adjacent_locations = world.get_list_of_adjacent_locations(character)
        
        if not hasattr(character, 'stationary_sentence'):
            character.stationary_sentence = np.hstack(self.model.get_utterance_embedding(character.name + self.stationary_sentence))
        
        if not hasattr(character, "movement_sentence"):
            character.movement_sentence = np.hstack(self.model.get_utterance_embedding(character.name + self.movement_sentence))
        
        action = np.hstack(self.model.get_utterance_embedding(last_action))
        staying_probability = distance.cosine(action, character.stationary_sentence)
        moving_probability = distance.cosine(action, character.movement_sentence)

        # print(f"Staying: {staying_probability}")
        # print(f"Moving: {moving_probability}")

        if moving_probability > staying_probability:
            location = None
            
            for loc in adjacent_locations:
                if loc in full_text:
                    if not location:
                        location = loc
                    else:
                        location = None
                        break
            
            if location:
                location_words = character.location.split(":")
                location_words[-1] = location
                return ":".join(location_words)
            
            for loc in known_locations:
                if loc in full_text:
                    if not location:
                        location = loc
                    else:
                        location = None
                        break
            
            if location:
                full_location_name = world.find_first_leaf(location)
                return full_location_name
        
        return None
            
            
            



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

