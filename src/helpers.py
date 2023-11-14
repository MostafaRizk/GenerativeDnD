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