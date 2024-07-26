from src.prompts.options import next_state_options
from src.enums.states import States 

trial_start = States.TRIAL_START.value 
trial_end = States.TRIAL_END.value
delay_start = States.DELAY_START.value
delay_end = States.DELAY_END.value 
mistrial = States.MISTRIAL.value 
next_state_header = "Next State Options -->"

sys_prompt = f'''
Goal: Predict if a change of state is warranted when given a series of text.\n
Context: You will be provided with two items:\n
1. "Current State" from among the following State Options: {[e.value for e in States]}
2. A series of text transmissions which you will use to make the following decisions:
    - Should the "Current State" change given the content/meaning of the text transmission.
    - If the "Current State" should be changed, predict the next state based on the content/meaning of the text transmission.
    - Prediction Rules: Predicted states must adhere to the following structured options:
        {trial_start}:\t {next_state_header} {next_state_options[trial_start]['Options']}
        {trial_end}:\t {next_state_header} {next_state_options[trial_end]['Options']}
        {delay_start}:\t {next_state_header} {next_state_options[delay_start]['Options']}
        {delay_end}:\t {next_state_header} {next_state_options[delay_end]['Options']}
        {mistrial}:\t {next_state_header} {next_state_options[mistrial]['Options']}
Output Format: Return your response as a json object in the following format:\n
    - If you determine that no change in state is warranted simply return the current state as json as follows:
        {{"current_state": <current state>}}
    - If a change in state is warranted based on the meaning/content of the associated text then return the following:
        {{"current_state": <current state>, "predicted_state": <predicted state>, "reasoning": <reason for next state prediction>}}
'''
