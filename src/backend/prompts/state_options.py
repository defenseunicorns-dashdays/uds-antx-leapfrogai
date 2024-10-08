from enums.states import States

mag_four = {"Options": [States.TRIAL_START.value,
                        States.DELAY_START.value,
                        States.MISTRIAL.value,
                        States.RTB.value]}
next_state_options = {
    States.IN_TRANSIT.value :
        {"Options":
            [States.TRIAL_START.value,
             States.DELAY_START.value,
             States.RTB.value]
            },
    States.TRIAL_START.value : 
        {"Options": 
            [States.TRIAL_END.value, 
             States.DELAY_START.value,
             States.MISTRIAL.value,
             States.RTB.value]
            },
    States.TRIAL_END.value : 
        mag_four,
    States.DELAY_START.value : 
        {"Options": 
            [States.DELAY_END.value,
             States.MISTRIAL.value,
             States.RTB.value]
             },
    States.DELAY_END.value : 
        mag_four,
    States.MISTRIAL.value : 
        {"Options": 
            [States.TRIAL_START.value,
             States.DELAY_START.value,
             States.RTB.value]
            },
    States.RTB.value : 
        {"Options": 
            [States.IN_TRANSIT.value,
             States.MISTRIAL.value,
             States.DELAY_START.value]
            }

}