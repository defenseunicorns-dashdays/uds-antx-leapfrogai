from src.enums.states import States 

trial_start = States.TRIAL_START.value 
trial_end = States.TRIAL_END.value
delay_start = States.DELAY_START.value
delay_end = States.DELAY_END.value 
mistrial = States.MISTRIAL.value 
rtb = States.RTB.value

examples = f'''
Current State:\t{trial_start}
Text:\tIt must have been right before we launched.  Yeah, go ahead.  Can I ask you guys a question?
Output: {{"current_state": {trial_start}}}

Current State:\t{trial_start}
Text:\tBe aware, we do have a fishing vessel maybe 100 yards from our location.
Output: {{"current_state": {trial_start}, "predicted_state": {delay_start}, "reason": "A fishing vessel is close to the trial area and could be a hazard to safe operations"}}

Current State:\t{delay_start}
Text:\tWe've got some time before the other target boats are in position. Continue to stay with Tango 1-3.
Output: {{"current_state": {delay_start}}}

Current State:\t{delay_end}
Text:\tTrial 211 has begun.
Output: {{"current_state": {delay_end}, "predicted_state": {trial_start}, "reason": "The text indicates that a new trial (211) has just started."}}

Current State:\t{trial_start}
Text:\tTo be advised, we've spotted several marine animals in your vicinity.
Output: {{"current_state": {trial_start}, "predicted_state": {delay_start}, "reason": "Marine animals were spotted near the operational area which could have adverse effects on the trial."}}

Current State:\t{delay_end}
Text:\tWe're gonna reset this trial.
Output: {{"current_state": {delay_end}, "predicted_state": {mistrial}, "reason": "The text indicates that the trial will need to be reset."}}

Current State:\t{delay_start}
Text:\tHarper.  Return to base.
Output: {{"current_state": {delay_start}, "predicted_state": {rtb}, "reason": "The text indicates that an order has been given to return to base."}}
'''

user = '''
As context you will be given a Current State and a Text snippet which will discuss ongoing maritime operations.
Given the separate pieces of context perform the following two sequential tasks:
1. Decide if a change to the Current State is warranted given the Text. 
   - If no change is warranted simply return a json object as follows:
   - Output: {{"current_state": <current state>}}
2. Based on your decision from step 1, if a change in state is warranted then return your output as follows:
    - Output: {{"current_state": <current state>, "predicted_state": <predicted state>, "reason": <reason for predicted state>}}
3. Use the following examples as your guide for predicting whether or not to change the state and if so, what to predict:
{examples}

---------
Current State: {current_state}
Text: {text}
---------
Output:
'''