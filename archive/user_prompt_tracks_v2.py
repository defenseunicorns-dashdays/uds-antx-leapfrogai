from src.enums.states import States 
from src.enums.tracks import Tracks, track_mapping
from src.prompts.options import next_state_options
from typing import Any

trial_start = States.TRIAL_START.value 
trial_end = States.TRIAL_END.value
delay_start = States.DELAY_START.value
delay_end = States.DELAY_END.value 
mistrial = States.MISTRIAL.value 
rtb = States.RTB.value

examples = f'''
EXAMPLE 1: No change in state
Current State:\t{trial_start}
Radio Transmissions:
- {Tracks.track1.value}: '',
- {Tracks.track3.value}: "Yes. Oh, the NavWar guy, I asked him. Yes. What Grant and I were talking about is that he gets operator overload sometimes. And so if there's a call going through on the green radio, that he might not hear it if he's fully in on the headset. Our thought was, okay, well, there's a bunch of NAVOR folks in there. Honestly, I grabbed the first one that I saw. The one that came up to me was like, hey, what can I do? Like, perfect. I'm like, but he's probably not the right person for that. I don't know if it's... That's what I kind of thought, figured would happen."
- {Tracks.track4.value}: "Is that independent? Oh no, I didn't even hear it. Is there volume on this? What is this? Oh, independent. Oh my gosh. I've been here a year. All right. Again, I cannot stress this enough, comms is not my day job. It is today, but..."
Potential next state options: {next_state_options[trial_start]['Options']}
Output: {{"current_state": {trial_start}}}

EXAMPLE 2: Delay Start prediction
Current State:\t{trial_start}
Radio Transmissions:
- {Tracks.track1.value}: 'Gents it looks like we have some fishing vessels approaching the operational area.',
- {Tracks.track3.value}: "Are you checking with her for that? 10 knots. Thank you. 2-1-1. EpiSci. I think we'll let them run for a while. I think that LBIT is still struggling.",
- {Tracks.track4.value}: "I'm just going to confirm we're still at 10 knots. Still 10 knots. So we're almost there. What? Basically perpendicular along the box. So roughly 1, 3, 0 for all of us. I'm just going to set this to one. If anything, you start to angle out of the box a little bit, just change a little bit. So definitely stay within it.
Potential next state options: {next_state_options[trial_start]['Options']}
Output: {{"current_state": {trial_start}, "predicted_state": {delay_start}, "reason": "A fishing vessel is close to the trial area and could be a hazard to safe operations"}}

EXAMPLE 3: No change in state
Current State:\t{delay_start}
Radio Transmissions:
- {Tracks.track1.value}: 'you'
- {Tracks.track3.value}: "Hello. Copy. Yeah. Do you only want them to send it if you tell them to? That one."
- {Tracks.track4.value}: "I was like, hey, I don't really, like, in a good way, but like, I don't really like this. This could be more efficient. Oh. Yeah, they can turn it way down. Yeah",
Potential next state options: {next_state_options[delay_start]['Options']}
Output: {{"current_state": {delay_start}}}

EXAMPLE 4: Trial Start prediction
Current State:\t{delay_end}
Radio Transmissions:
- {Tracks.track1.value}: "Do you think that's like mounting location or do you think that there is current What I'm also wondering I'm wondering if there's a boat a support boat next to red 16 between it and the radio right now If we get into, so we're ideally ramping up to a test. If we go into another PR, we're like, trying to figure shit out, at that point I would say we'll do, you got it.",
- {Tracks.track3.value}: "That's all well and good, alright enough chatter.  Go ahead and commence trial number 2-1-3."
- {Tracks.track4.value}: "Maybe just don't go directly at the dot. Just try to miss it by a little bit. Just in case. Yeah, and once you clear this hook a little bit more. Yeah."
Potential next state options: {next_state_options[delay_end]['Options']}
Output: {{"current_state": {delay_end}, "predicted_state": {trial_start}, "reason": "Radio transmission from the Test Director indicates that a new trial (2-1-3) has just commenced."}}

EXAMPLE 5: Delay Start prediction
Current State:\t{trial_start}
Radio Transmissions:
- {Tracks.track1.value}: "25 walk"
- {Tracks.track3.value}: "That'd be a fun upgrade. Yeah. Not fun is the right word, but I could see a use for that of being able to play back previous data. Yeah, I think of like a Ross bag or like you can still pop up in Arviz being able to do some version like that and see it propagate. Yeah, right. Yeah, let's put this on to. I'm curious at field events how much of the runway for the next series of dev presses gets generated. that's like, okay, so this is the first action that I'm hearing out of this. We're like, okay, here's a mole update. Is that a normal thing that happens at these?"
- {Tracks.track4.value}: "Hold up now, I'm seeing several marine animals in your vicinity."
Potential next state options: {next_state_options[trial_start]['Options']}
Output: {{"current_state": {trial_start}, "predicted_state": {delay_start}, "reason": "Radio transmission from the PCCU indicates that there are marine animals spotted near the testing area, thus necessitating a delay in starting the trial"}}

EXAMPLE 6: Mistrial prediction
Current State:\t{delay_end}
Radio Transmissions:
- {Tracks.track1.value}: "Good afternoon, again, sir. Leaving precautionary area. Yeah, I'm joining you. Seth, I can't see Lucy Tronco on my starboard side. We'll do a search for her. Copy that, Roger. Ajo traffic, Motorcycle Manor, 10-1"
- {Tracks.track3.value}: "They're new? Okay, I'm not going crazy. They should find a boat soon, huh? What are you guys able to see on your screen? Anthony, can I ask you a question? What's going on in that window? I think I made a folder. This is getting out of hand, going to declare a mistrial."
- {Tracks.track4.value}: "So one more thing to give us heads up on the way in these are supposed to go 20 meters off they see something that's supposed to go around it kind of thing. They don't always do that. So like Tango 10 and Tango 20 are going right towards each other. Just be ready to do evasive maneuvers if it looks like they're like going head on. Like that one I'd zoom way in. Maybe go the circle thing. Really like the circle thing where it says like 50 meter offset or 10 meter offset, whatever it's at. The ring, yeah. Bump that to 30 meters or so, yeah. And does it, oh. Very bottom right, the lock. Yeah. And then zoom way in. Yeah. So, if it looks like within like 30 meters, how does it start going right towards each other? Yeah, you're absolutely good."
Potential next state options: {next_state_options[delay_end]['Options']}
Output: {{"current_state": {delay_end}, "predicted_state": {mistrial}, "reason": "Radio transmission from the Test Director indicates that operations are getting out of hand and therefore declares a mistrial."}}
'''

user = '''
As context you will be given a Current State and a series of radio transmissions broken out into separate tracks. 
The transmissions represent dialogue between stakeholders involved in maritime UAV test and evaluation trials.\n  
Given the context perform the following two sequential tasks:
1. Decide if a change to the Current State is warranted given the transmissions. 
   - If no change is warranted simply return a json object as follows:
   - Output: {{"current_state": <current state>}}\n
2. Based on your decision from step 1, if a change in state is warranted then choose from among the next state options and return your output to include, current state, predicted state, and your reasoning for choosing the next predicted state.  Follow the output guidelines below:
    - Output: {{"current_state": <current state>, "predicted_state": <predicted state>, "reason": <reason for predicted state>}}\n

EXAMPLES
--------------------------
Use the following examples as your guide for predicting whether or not to change the state and if so, what to predict:
{examples}
--------------------------

Current State: {current_state}
Radio Transmissions:
{transmissions}
Potential next state options: {next_state_options}
--------------------------
Output:
'''

def parse_data_object(data_object: dict[str,Any]) -> str:
    '''
    Given a data object representing a single minute of radio tracks,
    this function parses the tracks, maps the original track names to 
    their functional names, and joins them with a double new-line break.
    '''
    tracks = [{k:data_object[k]} for k in data_object if k.startswith('track')]
    mapped_tracks = []
    for track in tracks:
        for key, value in track.items():
            mapped_tracks.append(f'{track_mapping[key]}: {value}')
    return '\n\n'.join(mapped_tracks)

def build_user_message(examples: str, 
                       current_state: str, 
                       radio_tracks: str, 
                       next_state_options: str
                       ) -> str:
    '''
    Builds user message string variable from dynamic string parameters.
    '''
    user_prompt = user.format(examples=examples, current_state=current_state, transmissions=radio_tracks, next_state_options=next_state_options)
    return user_prompt