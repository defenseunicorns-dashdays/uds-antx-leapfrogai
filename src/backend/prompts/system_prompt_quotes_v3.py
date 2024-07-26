from enums.states import States 

trial_start = States.TRIAL_START.value 
trial_end = States.TRIAL_END.value
delay_start = States.DELAY_START.value
delay_end = States.DELAY_END.value 
mistrial = States.MISTRIAL.value 
rtb = States.RTB.value
next_state_header = "Next State Options -->"

delay_sub_states = '''
\t- Vendor: Vendor issues causing delay in trial execution. 
\t- Non-Personnel Craft (NPC): Unauthorized craft enters Operating Area.
\t- Software: Boat experiences network drops or software crashes.
\t- Towing: Boat loses power and must be towed out of the Operating Area. 
'''

sys_prompt = f'''
Goal: Predict if a change of state is warranted when given a series of text from multiple radio tracks.\n
General Context: The radio tracks represent a running dialogue between participants in a maritime test and evaluation \
event with multiple unmanned autonomous vehicles (UAV) performing test trials. The primary unit of observation for \
this event is a "Trial". \n
Task Instructions: You will be provided with two components, a "Current State" and a series of radio tracks in text format.  The details \
of each component is provided below:\n

1. A "Current State" from among the following State Options: {[e.value for e in States]}
    Current State definitions are as follows:\n
    - {trial_start}:  Formal initiation of trial phase and evaluation and testing of UAV. This begins the Trial Window.
    - {trial_end}: Conclusion of testing and evaluation of UAV after all tests performed and at the discretion of the Test Director. This closes the trial Window.
    - {delay_start}:  A conditional state that prevents testing and evaluation while within a Trial Window due to one or more of the following factors. This begins a Delay Period.  These factors can be categorized as follows:\n
    {delay_sub_states}
    - {delay_end}: All conditional states that prevent testing and evaluation have ended while within the Trial Window. This closes a Delay Period. 
    - {mistrial}: This state can only occur after trial has started, but has abruptly ended for any given number of reasons.  There will be no Trial End state after a Mistrial. 
    - {rtb}: Return to base (RTB), all trials have ended and boats are in transit to their base of operations. 

2. A series of radio transmissions in text format which you will use to make the following decisions:
    - Decide if the "Current State" should change, given the content/meaning of the text transmission.
    - If the "Current State" should change, then predict the next state based on the content/meaning of the text transmission. \
You will be provided with a list of potential next state options given the Current State. 

Output Format: Return your response as a json object in the following format:\n
    - If you determine that no change in state is warranted simply return the current state as json as follows:
        {{"current_state": "<current state>"}}
    - If a change in state is warranted based on the meaning/content of the associated text then return the following:
        {{"predicted_state": "<predicted state>", "reasoning": "<your reasoning for next state prediction>"}}
'''

# prediction_rules = f'''
# - Prediction Rules: Predicted states must adhere to the following structured options:
# {trial_start}:\t {next_state_header} {state_options[trial_start]['Options']}
# {trial_end}:\t {next_state_header} {state_options[trial_end]['Options']}
# {delay_start}:\t {next_state_header} {state_options[delay_start]['Options']}
# {delay_end}:\t {next_state_header} {state_options[delay_end]['Options']}
# {mistrial}:\t {next_state_header} {state_options[mistrial]['Options']}
# '''