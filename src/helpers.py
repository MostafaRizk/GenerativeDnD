import re
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
            plan.append((task.group(), time.group()))
    
    if len(plan) > 0:
        return plan
    else:
        raise TypeError("Plan string had an invalid format")

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
    
