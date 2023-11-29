import re
import os
from collections import deque

def get_plan_from_plan_string(plan_string):
    plan_string = plan_string.split('\n')
    task_pattern = r'[A-Z].*' 
    time_pattern = r'\d{1,2}:\d{2}(am|pm|AM|PM)'

    plan = deque()

    for item in plan_string:
        task = re.search(task_pattern, item)
        time = re.search(time_pattern, item)

        if task and time:
            plan.append((task.group(), time.group().upper()))
    
    if len(plan) > 0:
        return plan
    else:
        raise TypeError("Plan string had an invalid format")

def get_plan_string_from_deque(plan_deque):
    return "\n".join([p[0] for p in plan_deque])

def get_score_from_importance_string(importance_string):
    sentence_pattern = r'The importance is \d{1,2}.'
    digit_pattern = r'\d{1,2}'
    
    sentence = re.search(sentence_pattern, importance_string)
    
    if sentence:
        sentence = sentence.group()
    
    score = re.search(digit_pattern, sentence)
    
    if score:
        score = int(score.group())
        return score
    
    return 0

def normalize(x, minimum, maximum):
    return (x - minimum) / (maximum - minimum)

def seconds_to_hours(seconds):
    return seconds/60/60

def exponential_decay(rate, time):
    return (1-rate)**time

def get_queries_from_question_string(question_string):
    question_pattern = r'[A-Z].*\?'
    queries = re.findall(question_pattern, question_string)

    return queries

def get_insights_from_insight_string(insight_string):
    insight_pattern = r'[A-Z].*\.'
    insights = re.findall(insight_pattern, insight_string)

    return insights

def list_characters(characters):
    if len(characters) == 1:
        return characters[0].name
    
    name_sequence = ", ".join([character.name for character in characters[:-1]])
    name_sequence = name_sequence + " and " + characters[-1].name
    return name_sequence

def list_entities(entity_names):
    if len(entity_names) == 1:
        return entity_names[0]
    
    name_sequence = ", ".join([e for e in entity_names[:-1]])
    name_sequence = name_sequence + " and " + entity_names[-1]
    return name_sequence

def extract_actions_from_utterance(utterance):
    action_pattern = r'\*(.*?)\*'
    actions = re.findall(action_pattern, utterance)
    for a in actions:
        a.replace("*", "")
    return " ".join(actions)

